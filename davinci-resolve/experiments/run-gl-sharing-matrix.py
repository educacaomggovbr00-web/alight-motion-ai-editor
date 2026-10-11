#!/usr/bin/env python3
"""Bound and isolate real diagnostic subprocesses; never start Resolve."""
import argparse
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def stop(process):
    if process is not None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=5)


def bounded(command, name, directory, env, seconds, result_file=None):
    print('START', name, flush=True)
    with (directory / (name + '.stdout.log')).open('w') as out, (directory / (name + '.stderr.log')).open('w') as err:
        child = subprocess.Popen(command, env=env, stdout=out, stderr=err, start_new_session=True)
        timed_out = False
        try:
            child.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
        finally:
            stop(child)
    status = {'name': name, 'exitCode': child.returncode, 'timeLimitReached': timed_out}
    if result_file is not None:
        if child.returncode != 0 or timed_out or not result_file.exists():
            failure = {'state': 'bloqueado', 'glSharingPassed': False, 'resolveTested': False, **status}
            result_file.write_text(json.dumps(failure, indent=2) + '\n')
        report = json.loads(result_file.read_text())
        report['matrixLabel'] = name
        result_file.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2), flush=True)
    print('END', json.dumps(status), flush=True)
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--label', choices=['with-udmabuf', 'without-udmabuf'], required=True)
    parser.add_argument('--xvfb', default='Xvfb')
    parser.add_argument('--legacy', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    scripts = Path(__file__).parent
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'
    statuses = []
    label = args.label + '-vulkan-dmabuf'
    statuses.append(bounded([sys.executable, str(scripts / 'vulkan-dmabuf-probe.py'), '--output', str(args.output / (label + '.json'))], label, args.output, env, 20, args.output / (label + '.json')))
    display = None
    with tempfile.TemporaryDirectory(prefix='codex-gl-sharing-') as temporary:
        number_file = Path(temporary) / 'display'
        try:
            with number_file.open('w') as number, (args.output / (args.label + '-xvfb.log')).open('w') as log:
                display = subprocess.Popen([args.xvfb, '-displayfd', str(number.fileno()), '-screen', '0', '1280x720x24', '-nolisten', 'tcp', '-ac'], env=env, pass_fds=(number.fileno(),), stdout=log, stderr=log, start_new_session=True)
                for _ in range(40):
                    if number_file.read_text().strip():
                        break
                    if display.poll() is not None:
                        raise RuntimeError('Xvfb exited during initialization.')
                    time.sleep(.1)
            number = number_file.read_text().strip()
            if not number.isdecimal():
                raise RuntimeError('No Xvfb display became available.')
            env['DISPLAY'] = ':' + number
            for kind in ['native', 'advertised-gpu']:
                profile_env = env.copy()
                if kind == 'native':
                    profile_env.pop('RUSTICL_DEVICE_TYPE', None)
                else:
                    profile_env['RUSTICL_DEVICE_TYPE'] = 'gpu'
                for backend in ['glx', 'egl']:
                    name = args.label + '-' + kind + '-' + backend
                    result_file = args.output / (name + '.json')
                    statuses.append(bounded([sys.executable, str(scripts / 'gl-sharing-probe.py'), '--backend', backend, '--output', str(result_file)], name, args.output, profile_env, 25, result_file))
            if args.legacy:
                profile_env = env.copy()
                profile_env['RUSTICL_DEVICE_TYPE'] = 'gpu'
                statuses.append(bounded([sys.executable, str(args.legacy)], args.label + '-legacy', args.output, profile_env, 25))
        except (OSError, RuntimeError) as exc:
            statuses.append({'name': args.label + '-display', 'error': str(exc)})
        finally:
            stop(display)
    # Metadata must never prevent the actual API probes above from running.
    for name, command, seconds in [('clinfo', ['clinfo'], 15), ('vulkan-summary', ['vulkaninfo', '--summary'], 15), ('mesa-versions', ['dpkg-query', '-W', 'mesa-opencl-icd', 'mesa-vulkan-drivers', 'libgl1-mesa-dri'], 5)]:
        statuses.append(bounded(command, args.label + '-' + name, args.output, env, seconds))
    (args.output / (args.label + '-processes.json')).write_text(json.dumps(statuses, indent=2) + '\n')


if __name__ == '__main__':
    main()
