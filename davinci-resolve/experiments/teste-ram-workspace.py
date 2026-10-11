import hashlib
import json
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path

private = Path('/workspace/ram-idea-private')
private.mkdir(mode=0o700, exist_ok=True)
memory_image = Path('/dev/shm/codex-davinci-memory-test.img')
if memory_image.exists():
    raise RuntimeError('A test image already exists; refusing to overwrite it')
max_memory = int(Path('/sys/fs/cgroup/memory.max').read_text())
used_memory = int(Path('/sys/fs/cgroup/memory.current').read_text())
if max_memory - used_memory < 448 * 1024 * 1024:
    raise RuntimeError('Insufficient cgroup memory headroom for this bounded test')

def mem_available():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1]) * 1024

def stop_process(proc):
    if proc is None:
        return
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    proc.wait(timeout=5)

shader = app = display = None
result = {'physicalGpuBefore': Path('/dev/dri').exists() or Path('/dev/nvidia0').exists(), 'memAvailableBefore': mem_available(), 'imageSizeBytes': 128 * 1024 * 1024}
env = os.environ.copy()
env.update(RUSTICL_ENABLE='llvmpipe,zink', RUSTICL_DEVICE_TYPE='gpu', LIBGL_ALWAYS_SOFTWARE='1', MESA_LOADER_DRIVER_OVERRIDE='zink', GALLIUM_DRIVER='zink', LP_NUM_THREADS='2', LIBGL_DRIVERS_PATH='/workspace/zink-private/root/usr/lib/x86_64-linux-gnu/dri', VK_DRIVER_FILES='/workspace/zink-private/root/usr/share/vulkan/icd.d/lvp_icd.json', OCL_ICD_VENDORS='/workspace/zink-private/root/etc/OpenCL/vendors', LD_LIBRARY_PATH='/workspace/zink-private/root/usr/lib/x86_64-linux-gnu:/workspace/rusticl-private/root/usr/lib/x86_64-linux-gnu:/workspace/davinci-private/tools/usr/lib/x86_64-linux-gnu')
proot = ['/workspace/davinci-private/tools/usr/bin/proot', '-b', '/workspace/rusticl-private/root/usr/lib/clc:/usr/lib/clc', '-b', '/workspace/rusticl-private/root/usr/lib/llvm-19:/usr/lib/llvm-19']
try:
    with memory_image.open('xb') as image_file:
        os.chmod(memory_image, 0o600)
        chunk = bytes(1024 * 1024)
        for _ in range(128):
            image_file.write(chunk)
        image_file.flush()
        os.fsync(image_file.fileno())
    result['imageAllocatedBytes'] = memory_image.stat().st_blocks * 512
    result['memAvailableAfterRamImage'] = mem_available()
    with (private / 'filesystem.log').open('w') as log:
        subprocess.run(['/workspace/zink-private/root/usr/sbin/mkfs.fat', '-F', '16', str(memory_image)], stdout=log, stderr=log, timeout=10, check=True)
    message = b'Teste sintetico: arquivo gravado em FAT16 dentro da RAM.\n'
    source = private / 'PROVA.TXT'
    source.write_bytes(message)
    subprocess.run(['/workspace/zink-private/root/usr/bin/mcopy', '-i', str(memory_image), str(source), '::PROVA.TXT'], timeout=10, check=True)
    restored = subprocess.check_output(['/workspace/zink-private/root/usr/bin/mtype', '-i', str(memory_image), '::PROVA.TXT'], timeout=10)
    result['fatReadWritePassed'] = restored == message
    result['proofSha256'] = hashlib.sha256(restored).hexdigest()
    result['memAvailableAfterFatTest'] = mem_available()
    print('RAM disk image FAT16: read/write verified', flush=True)
    shader_log = (private / 'buffer.log').open('w')
    shader = subprocess.Popen(proot + ['python', '/workspace/zink-private/reserve-opencl.py', str(private / 'buffer.json')], env=env, stdin=subprocess.PIPE, stdout=shader_log, stderr=shader_log, start_new_session=True)
    for _ in range(100):
        if (private / 'buffer.json').exists():
            break
        if shader.poll() is not None:
            raise RuntimeError('The real OpenCL buffer allocation failed; inspect buffer.log')
        time.sleep(.1)
    result['opencl'] = json.loads((private / 'buffer.json').read_text())
    result['memAvailableWithBothReservations'] = mem_available()
    result['physicalGpuAfterReservation'] = Path('/dev/dri').exists() or Path('/dev/nvidia0').exists()
    print('OpenCL buffer: 64 MiB filled/read; reservations remain active', flush=True)
    number = (private / 'display.txt').open('w')
    display_log = (private / 'xvfb.log').open('w')
    display = subprocess.Popen(['/workspace/davinci-private/tools/usr/bin/Xvfb', '-displayfd', str(number.fileno()), '-screen', '0', '1280x720x24', '-nolisten', 'tcp', '-ac'], stdout=display_log, stderr=display_log, pass_fds=(number.fileno(),), start_new_session=True)
    for _ in range(50):
        if (private / 'display.txt').read_text().strip():
            break
        time.sleep(.1)
    env['DISPLAY'] = ':' + (private / 'display.txt').read_text().strip()
    env['LD_LIBRARY_PATH'] += ':/workspace/davinci-private/squashfs-root/libs'
    with (private / 'resolve.log').open('w') as log:
        app = subprocess.Popen(proot + ['/workspace/davinci-private/squashfs-root/bin/resolve'], env=env, stdout=log, stderr=log, start_new_session=True)
        time.sleep(30)
        subprocess.run(['import', '-window', 'root', str(private / 'resolve-with-ram.png')], env=env, timeout=8, check=True)
        shutil.copyfile('/home/agent/.local/share/DaVinciResolve/logs/ResolveDebug.txt', private / 'ResolveDebug.txt')
        debug = (private / 'ResolveDebug.txt').read_text(errors='replace')
        result['resolveStarted'] = '21.1.1' in (private / 'resolve.log').read_text()
        result['resolveDvipContextFailed'] = 'OpenCL Context Manager failed to create context' in debug
        result['editingProven'] = False
finally:
    for proc in [app, display, shader]:
        stop_process(proc)
    memory_image.unlink(missing_ok=True)
    result['ramImageRemoved'] = not memory_image.exists()
    result['memAvailableAfterCleanup'] = mem_available()
    (private / 'result.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
