#!/usr/bin/env python3
"""Bounded original-app experiment: independent GL gate, UI, SDK, ffprobe."""
import argparse, hashlib, json, os, re, resource, signal, subprocess, sys, tempfile, time
from pathlib import Path
from source import BINARY_SHA256, digest

def sanitized(text):
    text=re.sub(r'https?://[^\s<>"\']+', '[URL REDACTED]',text)
    return re.sub(r'(?i)(signature|key-pair-id|token|api_key)=[^\s&]+',r'\1=[REDACTED]',text)

def verified(report):
    if not isinstance(report,dict) or not isinstance(report.get('devices'),list): return False
    return (isinstance(report,dict) and report.get('glSharingPassed') is True and any(
        isinstance(d,dict) and d.get('glSharedContextCreated') is True and isinstance(d.get('sharedBufferRoundTrip'),dict)
        and d['sharedBufferRoundTrip'].get('passed') is True and d['sharedBufferRoundTrip'].get('valuesReadByOpenGL')==[42,8,9,10]
        for d in report.get('devices',[])))

def clean_env(env):
    blocked=('TOKEN','SECRET','PASSWORD','API_KEY','DOWNLOAD_URL','LINUX_URL')
    return {k:v for k,v in env.items() if not any(part in k.upper() for part in blocked) and not k.startswith('GITHUB_')}

def stop(p):
    if p is None:return
    try:os.killpg(p.pid,signal.SIGTERM)
    except ProcessLookupError:pass
    try:p.wait(timeout=3)
    except subprocess.TimeoutExpired:pass
    # Descendants may survive the leader. All belong to the group we created.
    try:os.killpg(p.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    p.wait(timeout=3)

def bounded(argv, env, seconds, output=None):
    with tempfile.TemporaryFile() as log:
        p=subprocess.Popen(argv,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        timed=False
        try:p.wait(timeout=seconds)
        except subprocess.TimeoutExpired:timed=True
        finally:stop(p)
        log.seek(0);text=sanitized(log.read(4*1024**2).decode(errors='replace'))
        if output:Path(output).write_text(text)
        return {'exitCode':p.returncode,'timeLimitReached':timed},text

def validate_mp4(path):
    p=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],capture_output=True,text=True,timeout=15)
    if p.returncode:raise ValueError('FFprobe não leu o MP4.')
    data=json.loads(p.stdout);video=next((s for s in data['streams'] if s['codec_type']=='video'),{})
    rate=video.get('avg_frame_rate','0/1');n,d=rate.split('/');fps=float(n)/float(d)
    duration=float(data['format']['duration'])
    if not (video.get('codec_name')=='h264' and video.get('width')==640 and video.get('height')==360 and abs(fps-30)<.001 and abs(duration-3)<.25):
        raise ValueError('MP4 não atende H.264, 640×360, 30 FPS e 3 segundos.')
    return data

def main():
    p=argparse.ArgumentParser();p.add_argument('--resolve-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--backend',choices=['glx','egl'],required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True);result={'state':'bloqueado','profile':a.backend,'resolveStarted':False,'glSharingPassed':False,'uiFunctionalProven':False,'dvipInitializationConfirmed':False,'projectCreated':False,'mediaImported':False,'timelineCreated':False,'exportProven':False}
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    env=clean_env(os.environ);x=app=None
    try:
        executable=a.resolve_root/'bin/resolve'
        if not executable.is_file() or digest(executable)!=BINARY_SHA256:
            result['reason']='Executável original verificado não disponível.';return 2
        result['resolveSha256Before']=BINARY_SHA256
        env.update(CODEX_EXPERIMENTAL_SOFTWARE_GL_SHARING='1',RUSTICL_DEVICE_TYPE='gpu',QT_QPA_PLATFORM='xcb',QT_XCB_GL_INTEGRATION='xcb_glx' if a.backend=='glx' else 'xcb_egl')
        # System GLib addresses the previously audited bundled GLib conflicts.
        family=['libglib-2.0.so.0','libgobject-2.0.so.0','libgmodule-2.0.so.0','libgio-2.0.so.0']
        env['LD_PRELOAD']=':'.join('/usr/lib/x86_64-linux-gnu/'+f for f in family)
        env['LD_LIBRARY_PATH']='/opt/mesa-experimental/lib:'+str(a.resolve_root/'libs')+':/usr/lib/x86_64-linux-gnu'
        result['settings']={k:env.get(k) for k in ['CODEX_EXPERIMENTAL_SOFTWARE_GL_SHARING','RUSTICL_DEVICE_TYPE','QT_QPA_PLATFORM','QT_XCB_GL_INTEGRATION','VK_DRIVER_FILES','LIBGL_DRIVERS_PATH','OCL_ICD_VENDORS','LD_LIBRARY_PATH','LD_PRELOAD']}
        result['physicalRenderNodes']=[str(n) for n in Path('/dev/dri').glob('renderD*')]
        limit=Path('/sys/fs/cgroup/memory.max');result['memoryLimit']=limit.read_text().strip() if limit.exists() else None
        display_file=a.output/'display-private'
        with display_file.open('w') as number,(a.output/'xvfb.log').open('w') as log:
            x=subprocess.Popen(['Xvfb','-displayfd',str(number.fileno()),'-screen','0','1280x720x24','-nolisten','tcp','-ac'],env=env,stdout=log,stderr=log,pass_fds=(number.fileno(),),start_new_session=True)
        for _ in range(50):
            if display_file.read_text().strip():break
            if x.poll() is not None:raise RuntimeError('Xvfb não iniciou.')
            time.sleep(.1)
        number=display_file.read_text().strip()
        if not number.isdecimal():raise RuntimeError('DISPLAY não disponível.')
        env['DISPLAY']=':'+number
        gate=a.output/'sharing-before-resolve.json'
        status,_=bounded(['python3','/experiment/gl-sharing-probe.py','--backend',a.backend,'--output',str(gate)],env,25,a.output/'sharing-probe.log')
        proof=json.loads(gate.read_text()) if gate.exists() else {}
        result['glSharingPassed']=verified(proof)
        if not result['glSharingPassed']:
            result['reason']='Gate real GL/CL falhou neste ambiente; Resolve não iniciado.';return 2
        _,ldd=bounded(['ldd',str(executable)],env,15,a.output/'dependencies.log')
        missing=[l for l in ldd.splitlines() if 'not found' in l]
        if missing:result['reason']='Bibliotecas necessárias ausentes.';result['missingLibraries']=missing;return 2
        synthetic=a.output/'synthetic.mov'
        status,_=bounded(['ffmpeg','-y','-v','error','-f','lavfi','-i','testsrc2=size=640x360:rate=30','-t','3','-an','-c:v','dnxhd','-profile:v','dnxhr_lb','-pix_fmt','yuv422p',str(synthetic)],env,30,a.output/'synthetic.log')
        if status['exitCode'] or not synthetic.exists():raise RuntimeError('Mídia sintética DNxHR não foi gerada.')
        render=a.output/'render';render.mkdir(exist_ok=True)
        env.update(CODEX_SYNTHETIC_VIDEO=str(synthetic),CODEX_RENDER_OUTPUT=str(render))
        # Make the same script available through the documented internal Scripts menu.
        utility=Path.home()/'.local/share/DaVinciResolve/Fusion/Scripts/Utility';utility.mkdir(parents=True,exist_ok=True)
        (utility/'CodexSyntheticSmoke.py').write_text((Path(__file__).parent/'edit_smoke.py').read_text())
        debug=Path.home()/'.local/share/DaVinciResolve/logs/ResolveDebug.txt'
        offset=debug.stat().st_size if debug.exists() else 0
        with tempfile.TemporaryFile() as log:
            app=subprocess.Popen([str(executable)],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            result.update(resolveStarted=True,state='experimental')
            for _ in range(40):
                if app.poll() is not None:break
                time.sleep(1)
            result['loadedLibraries']=[]
            maps=Path('/proc')/str(app.pid)/'maps'
            if maps.exists():
                result['loadedLibraries']=sorted(set(l.split()[-1] for l in maps.read_text().splitlines() if any(name in l for name in ['libgallium','libRusticl','libOpenCL','libGLX_mesa','libEGL_mesa','libLLVM','libglib-2.0'])))
            if app.poll() is None:
                status,_=bounded(['import','-window','root',str(a.output/'screen-before-sdk.png')],env,15)
                result['screenshotCaptured']=status['exitCode']==0
                _,ocr=bounded(['tesseract',str(a.output/'screen-before-sdk.png'),'stdout'],env,15,a.output/'screen-text.txt')
                _,titles=bounded(['xdotool','search','--onlyvisible','--name','.*','getwindowname'],env,10,a.output/'window-titles.txt')
                text=(ocr+'\n'+titles).lower();result['unsupportedGpuModeObserved']=('unsupported gpu' in text or 'unsupported gpu processing mode' in text) if result['screenshotCaptured'] else None
                result['splashColorPageObserved']='loading color page' in text
                python=a.resolve_root/'bin/ResolvePython'
                if python.exists():
                    status,_=bounded([str(python),str(Path(__file__).parent/'edit_smoke.py')],env,90,a.output/'sdk-launch.log');result['sdkProcess']=status
                else:result['sdkUnavailableReason']='Interpretador oficial ResolvePython não encontrado.'
                sdk=render/'sdk-result.json'
                if sdk.exists():
                    r=json.loads(sdk.read_text());result['sdk']=r
                    for k in ['projectCreated','mediaImported','timelineCreated']:result[k]=r.get(k) is True
                    if r.get('renderProducedFile'):
                        try:
                            metadata=validate_mp4(render/'resolve-synthetic.mp4');(a.output/'ffprobe.json').write_text(json.dumps(metadata,indent=2)+'\n')
                            result.update(exportProven=True,dvipInitializationConfirmed=True,state='testado')
                        except (OSError,ValueError,subprocess.TimeoutExpired) as exc:result['validationError']=type(exc).__name__
                bounded(['import','-window','root',str(a.output/'screen-after-sdk.png')],env,15)
            result['appExitCode']=app.poll()
            log.seek(0);(a.output/'application.log').write_text(sanitized(log.read(4*1024**2).decode(errors='replace')))
        if debug.exists():
            with debug.open('rb') as f:
                if debug.stat().st_size>=offset:f.seek(offset)
                recent=sanitized(f.read(8*1024**2).decode(errors='replace'))
            evidence=[l for l in recent.splitlines() if re.search(r'DVIP|OpenCL|OpenGL|GPU|Running DaVinci|21\.1\.1|Error|ERROR|Failed|LOADING',l)]
            (a.output/'resolve-relevant.log').write_text('\n'.join(evidence)+'\n')
            result['dvipErrors']=[l for l in evidence if 'DVIP Exception:' in l or 'failed to create context' in l or 'Failed to initialize OpenCL board manager' in l]
            result['version21ConfirmedInLog']='21.1.1' in recent
        result['reason']='Render real validado.' if result['exportProven'] else 'Execução observada; consulte logs/SDK. Ausência de erro não comprova DVIP ou editor funcional.'
        if result.get('dvipErrors') or result.get('unsupportedGpuModeObserved'):result['state']='bloqueado'
        return 0 if result['exportProven'] else 2
    except Exception as exc:
        result['reason']='Experimento falhou: '+type(exc).__name__;return 2
    finally:
        stop(app);stop(x)
        executable=a.resolve_root/'bin/resolve'
        result['resolveSha256After']=digest(executable) if executable.exists() else None
        result['originalExecutableUnmodified']=result.get('resolveSha256Before')==result['resolveSha256After']==BINARY_SHA256
        (a.output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':raise SystemExit(main())
