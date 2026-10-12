#!/usr/bin/env python3
"""Bounded original-app experiment: independent GL gate, UI, SDK, ffprobe."""
import argparse, hashlib, json, os, re, resource, signal, subprocess, sys, tempfile, time, shutil, math
from internal_menu import invoke as invoke_internal_script
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
    blocked=('TOKEN','SECRET','PASSWORD','API_KEY','DOWNLOAD_URL','LINUX_URL','VIDEO_URL')
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

def validate_mp4(path,width=640,height=360,expected_duration=3):
    p=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],capture_output=True,text=True,timeout=15)
    if p.returncode:raise ValueError('FFprobe não leu o MP4.')
    data=json.loads(p.stdout);video=next((s for s in data['streams'] if s['codec_type']=='video'),{})
    rate=video.get('avg_frame_rate','0/1');n,d=rate.split('/');fps=float(n)/float(d)
    duration=float(data['format']['duration'])
    audio=next((s for s in data['streams'] if s['codec_type']=='audio'),{})
    if not (video.get('codec_name')=='h264' and video.get('width')==width and video.get('height')==height and abs(fps-30)<.001 and abs(duration-expected_duration)<.25 and audio.get('codec_name')=='aac'):
        raise ValueError('MP4 não atende codecs, resolução, FPS e duração solicitados.')
    return data

def validate_native(path,fmt,width=640,height=360,expected_duration=3):
    p=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],capture_output=True,text=True,timeout=15)
    if p.returncode:raise ValueError('Render nativo não legível.')
    data=json.loads(p.stdout);video=next((s for s in data['streams'] if s['codec_type']=='video'),{});audio=next((s for s in data['streams'] if s['codec_type']=='audio'),{})
    n,d=video.get('avg_frame_rate','0/1').split('/');rate=float(n)/float(d)
    allowed=('h264',) if fmt=='mp4' else ('dnxhd',)
    if video.get('codec_name') not in allowed or video.get('width')!=width or video.get('height')!=height or abs(rate-30)>.001 or abs(float(data['format']['duration'])-expected_duration)>.25 or not audio:
        raise ValueError('Render nativo fora da especificação de vídeo/áudio.')
    return data

def onboarding_button(text):
    text=text.lower()
    if any(x in text for x in ['license agreement','terms and conditions','sign in','activation','license key']):return None
    if "what's new in davinci resolve" in text and 'continue' in text:return 'continue'
    if 'welcome' in text and 'davinci resolve' in text and 'skip' in text:return 'skip'
    if 'almost there' in text and 'before jumping straight into a project' in text and 'skip and start right now' in text:return 'skip'
    return None

def advance_onboarding(output, env):
    steps=[]
    for index in range(3):
        screen=output/f'onboarding-{index}.png'
        status,_=bounded(['import','-window','root',str(screen)],env,10)
        if status['exitCode']:break
        ocr_status,tsv=bounded(['tesseract',str(screen),'stdout','--psm','6','tsv'],env,30,output/f'onboarding-{index}.log')
        if ocr_status['exitCode']:
            steps.append({'screen':index,'ocrFailed':True,'timeLimitReached':ocr_status['timeLimitReached'],'clicked':False});break
        rows=[line.split('\t') for line in tsv.splitlines()[1:]]
        words=[r for r in rows if len(r)>=12 and r[11].strip()]
        text=' '.join(r[11] for r in words)
        # Verified 1280x720 introduction layout: OCR the enclosed Continue label separately.
        if "what's new in davinci resolve" in text.lower() and 'continue' not in text.lower():
            crop=output/f'onboarding-footer-{index}.png'
            status,_=bounded(['convert',str(screen),'-crop','110x25+670+584','+repage','-resize','400%','-negate',str(crop)],env,10)
            if status['exitCode']==0:
                _,footer=bounded(['tesseract',str(crop),'stdout','--psm','7','tsv'],env,15,output/f'onboarding-footer-{index}.log')
                for row in [l.split('\t') for l in footer.splitlines()[1:]]:
                    if len(row)>=12 and row[11].strip().lower()=='continue':
                        row[6]=str(670+int(row[6])//4);row[7]=str(584+int(row[7])//4)
                        row[8]=str(int(row[8])//4);row[9]=str(int(row[9])//4)
                        words.append(row);text+=' '+row[11]
        button=onboarding_button(text)
        if button is None:break
        match=next((r for r in words if r[11].lower().startswith(button)),None)
        if not match:break
        x=int(match[6])+int(match[8])//2;y=int(match[7])+int(match[9])//2
        status,_=bounded(['xdotool','mousemove','--sync',str(x),str(y),'click','1'],env,5)
        steps.append({'screen':index,'recognizedButton':button,'clicked':status['exitCode']==0})
        if status['exitCode']:break
        time.sleep(5)
    return steps

def main():
    p=argparse.ArgumentParser();p.add_argument('--resolve-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--backend',choices=['glx','egl'],required=True);p.add_argument('--input-video',type=Path);p.add_argument('--width',type=int,default=640);p.add_argument('--height',type=int,default=360);p.add_argument('--duration',type=float,default=3);a=p.parse_args()
    if (a.width,a.height) not in ((640,360),(540,960)) or not math.isfinite(a.duration) or not 1<=a.duration<=30:p.error('Formato/duração fora dos limites.')
    a.output.mkdir(parents=True,exist_ok=True);result={'state':'bloqueado','profile':a.backend,'resolveStarted':False,'glSharingPassed':False,'uiFunctionalProven':False,'dvipInitializationConfirmed':False,'projectCreated':False,'mediaImported':False,'timelineCreated':False,'exportProven':False,'nativeRenderProven':False,'nativeMp4ExportProven':False,'mp4DeliveryValidated':False}
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    env=clean_env(os.environ);x=app=None
    try:
        executable=a.resolve_root/'bin/resolve'
        if not executable.is_file() or digest(executable)!=BINARY_SHA256:
            result['reason']='Executável original verificado não disponível.';return 2
        result['resolveSha256Before']=BINARY_SHA256
        # Official post_install.sh creates these normal support folders. No license data is supplied.
        for folder in ['easyDCP', '.license', 'logs']:
            (a.resolve_root/folder).mkdir(parents=True,exist_ok=True)
        Path('/var/BlackmagicDesign/DaVinci Resolve').mkdir(parents=True,exist_ok=True)
        for folder in ['configs','logs','Fusion']:
            (Path.home()/'.local/share/DaVinciResolve'/folder).mkdir(parents=True,exist_ok=True)
        env.update(CODEX_EXPERIMENTAL_SOFTWARE_GL_SHARING='1',RUSTICL_DEVICE_TYPE='gpu',QT_DEBUG_PLUGINS='1',QT_QPA_PLATFORM='xcb',QT_XCB_GL_INTEGRATION='xcb_glx' if a.backend=='glx' else 'xcb_egl')
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
        desktop_env={k:v for k,v in env.items() if k not in ('LD_LIBRARY_PATH','LD_PRELOAD')}
        desktop_env.update(OMP_THREAD_LIMIT='1',OMP_NUM_THREADS='1')
        gate=a.output/'sharing-before-resolve.json'
        status,_=bounded(['python3','/experiment/gl-sharing-probe.py','--backend',a.backend,'--output',str(gate)],env,25,a.output/'sharing-probe.log')
        proof=json.loads(gate.read_text()) if gate.exists() else {}
        result['glSharingPassed']=verified(proof)
        if not result['glSharingPassed']:
            result['reason']='Gate real GL/CL falhou neste ambiente; Resolve não iniciado.';return 2
        _,ldd=bounded(['ldd',str(executable)],env,15,a.output/'dependencies.log')
        _,plugins=bounded(['ldd',str(a.resolve_root/'libs/plugins/platforms/libqxcb.so')],env,15,a.output/'qt-plugin-dependencies.log')
        missing=[l for l in (ldd+'\n'+plugins).splitlines() if 'not found' in l]
        if missing:result['reason']='Bibliotecas necessárias ausentes.';result['missingLibraries']=missing;return 2
        synthetic=a.input_video if a.input_video is not None else a.output/'synthetic.mov'
        if a.input_video is None:
            status,_=bounded(['ffmpeg','-y','-v','error','-f','lavfi','-i','testsrc2=size='+str(a.width)+'x'+str(a.height)+':rate=30','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t',str(a.duration),'-c:a','pcm_s16le','-c:v','dnxhd','-profile:v','dnxhr_lb','-pix_fmt','yuv422p',str(synthetic)],env,30,a.output/'synthetic.log')
            if status['exitCode'] or not synthetic.exists():raise RuntimeError('Mídia sintética DNxHR/PCM não foi gerada.')
        else:
            if not synthetic.is_file() or synthetic.stat().st_size>250*1024**2:raise ValueError('Entrada privada preparada ausente ou muito grande.')
            validate_native(synthetic,'mov',a.width,a.height,a.duration)
        result['inputKind']='private' if a.input_video is not None else 'synthetic'
        render=a.output/'render';render.mkdir(exist_ok=True)
        env.update(CODEX_SYNTHETIC_VIDEO=str(synthetic),CODEX_RENDER_OUTPUT=str(render),CODEX_WIDTH=str(a.width),CODEX_HEIGHT=str(a.height),CODEX_DURATION=str(a.duration),CODEX_MEDIA_PRIVATE='1' if a.input_video is not None else '0')
        # A runner has no sound card: use ALSA's null playback device, not a retry loop.
        alsa_config=a.output/'alsa-null.conf'
        alsa_config.write_text('pcm.!default { type null }\n')
        env['ALSA_CONFIG_PATH']=str(alsa_config)
        result['audioPlaybackBackend']='ALSA null; file audio remains in render'
        # Make the same script available through the documented internal Scripts menu.
        utility=Path.home()/'.local/share/DaVinciResolve/Fusion/Scripts/Utility';utility.mkdir(parents=True,exist_ok=True)
        (utility/'CodexSyntheticSmoke.py').write_text((Path(__file__).parent/'edit_smoke.py').read_text())
        global_utility=a.resolve_root/'Fusion/Scripts/Utility'
        global_utility.mkdir(parents=True,exist_ok=True)
        (global_utility/'CodexSyntheticSmoke.py').write_text((Path(__file__).parent/'edit_smoke.py').read_text())
        result['scriptLocationsPrepared']=['user Utility','all-users Utility']
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
                result['onboardingActions']=advance_onboarding(a.output,desktop_env)
                if result['onboardingActions']:time.sleep(40)
                # Wait for the real main window before touching the documented Scripts menu.
                startup_samples=[]
                for _ in range(60):
                    _,ready=bounded(['xdotool','search','--onlyvisible','--name','DaVinci Resolve -','getwindowname','%@'],desktop_env,5)
                    try:
                        stat=(Path('/proc')/str(app.pid)/'stat').read_text().split(') ',1)[1].split()
                        status_text=(Path('/proc')/str(app.pid)/'status').read_text()
                        memory=next((line for line in status_text.splitlines() if line.startswith('VmRSS:')),None)
                        startup_samples.append({'monotonic':round(time.monotonic(),1),'state':stat[0],'userCpuTicks':stat[11],'systemCpuTicks':stat[12],'rss':memory})
                    except OSError:pass
                    if 'DaVinci Resolve -' in ready:break
                    if app.poll() is not None:break
                    time.sleep(5)
                result['uiMainWindowObserved']='DaVinci Resolve -' in ready
                (a.output/'startup-process-samples.json').write_text(json.dumps(startup_samples,indent=2))
                if not result['uiMainWindowObserved'] and app.poll() is None:
                    bounded(['gdb','--batch','-ex','set pagination off','-ex','thread apply all bt 8','-ex','detach','-p',str(app.pid)],desktop_env,20,a.output/'startup-thread-backtrace.log')
                status,_=bounded(['import','-window','root',str(a.output/'screen-before-sdk.png')],desktop_env,15)
                result['screenshotCaptured']=status['exitCode']==0
                _,ocr=bounded(['tesseract',str(a.output/'screen-before-sdk.png'),'stdout','--psm','6'],desktop_env,15,a.output/'screen-text.txt')
                _,titles=bounded(['xdotool','search','--onlyvisible','--name','.*','getwindowname','%@'],desktop_env,10,a.output/'window-titles.txt')
                text=(ocr+'\n'+titles).lower();result['unsupportedGpuModeObserved']=('unsupported gpu' in text or 'unsupported gpu processing mode' in text) if result['screenshotCaptured'] else None
                result['splashColorPageObserved']='loading color page' in text
                python=a.resolve_root/'bin/ResolvePython'
                if python.exists():
                    status,_=bounded([str(python),str(Path(__file__).parent/'edit_smoke.py')],env,90,a.output/'sdk-launch.log');result['sdkProcess']=status
                else:result['sdkUnavailableReason']='Interpretador oficial ResolvePython não encontrado.'
                sdk=render/'sdk-result.json'
                external=json.loads(sdk.read_text()) if sdk.exists() else {}
                if not external.get('apiConnected') and result.get('uiMainWindowObserved'):
                    result['externalSdk']=external
                    for name in ['sdk-result.json','sdk-progress.json','sdk-started.json']:(render/name).unlink(missing_ok=True)
                    result['internalScriptMenu']=invoke_internal_script(a.output,desktop_env,bounded)
                    if result['internalScriptMenu'].get('scriptMenuInvoked'):
                        deadline=time.monotonic()+200
                        while not sdk.exists() and app.poll() is None and time.monotonic()<deadline:time.sleep(1)
                        result['internalScriptTimedOut']=not sdk.exists()
                progress=render/'sdk-progress.json'
                if sdk.exists() or progress.exists():
                    r=json.loads((sdk if sdk.exists() else progress).read_text());result['sdk']=r
                    for k in ['projectCreated','mediaImported','timelineCreated','effectApplied']:result[k]=r.get(k) is True
                    if r.get('renderProducedFile') and r.get('renderStatus',{}).get('JobStatus')=='Complete':
                        try:
                            fmt=r.get('nativeFormat');filename=r.get('nativeFileName')
                            if fmt not in ('mov','mp4') or filename!='resolve-synthetic.'+fmt:raise ValueError('Caminho nativo inesperado.')
                            native=render/filename
                            metadata=validate_native(native,fmt,a.width,a.height,a.duration);(a.output/'ffprobe-native.json').write_text(json.dumps(metadata,indent=2)+'\n')
                            result.update(nativeRenderProven=True,nativeRenderSha256=digest(native),dvipInitializationConfirmed=True,uiFunctionalProven=True)
                            final=render/'final-delivery.mp4'
                            if fmt=='mp4':
                                shutil.copyfile(native,final)
                                validate_mp4(final,a.width,a.height,a.duration);result.update(nativeMp4ExportProven=True,exportProven=True,mp4Packaging='Resolve original')
                            else:
                                status,_=bounded(['ffmpeg','-y','-v','error','-i',str(native),'-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(final)],desktop_env,40,a.output/'mp4-packaging.log')
                                if status['exitCode']:raise ValueError('Embalagem MP4 auxiliar falhou.')
                                result['mp4Packaging']='FFmpeg auxiliar após render DNxHR MOV do Resolve; não é MP4 exportado diretamente pelo Resolve'
                            final_metadata=validate_mp4(final,a.width,a.height,a.duration);(a.output/'ffprobe.json').write_text(json.dumps(final_metadata,indent=2)+'\n')
                            result.update(mp4DeliveryValidated=True,state='testado')
                        except (OSError,ValueError,subprocess.TimeoutExpired) as exc:result['validationError']=type(exc).__name__
                bounded(['import','-window','root',str(a.output/'screen-after-sdk.png')],desktop_env,15)
            result['appExitCode']=app.poll()
            log.seek(0);(a.output/'application.log').write_text(sanitized(log.read(4*1024**2).decode(errors='replace')))
        if debug.exists():
            with debug.open('rb') as f:
                if debug.stat().st_size>=offset:f.seek(offset)
                recent=sanitized(f.read(8*1024**2).decode(errors='replace'))
            (a.output/'resolve-debug-fresh.log').write_text(recent)
            evidence=[l for l in recent.splitlines() if re.search(r'DVIP|OpenCL|OpenGL|GPU|Running DaVinci|21\.1\.1|Error|ERROR|Failed|LOADING',l)]
            (a.output/'resolve-relevant.log').write_text('\n'.join(evidence)+'\n')
            result['dvipErrors']=[l for l in evidence if 'DVIP Exception:' in l or 'failed to create context' in l or 'Failed to initialize OpenCL board manager' in l]
            result['version21ConfirmedInLog']='21.1.1' in recent
            result['dvipContextCreated']='Created OpenCL context for devices' in recent
            result['glInteropInitialized']='OpenGL interop was initialized.' in recent
        if debug.exists() and 'CrashReport' in recent: result['nativeCrashReportObserved']=True
        result['reason']='Render nativo e MP4 final validados; consulte origem da embalagem.' if result['nativeRenderProven'] and result['mp4DeliveryValidated'] else 'Execução observada; consulte logs/SDK. Ausência de erro não comprova DVIP ou editor funcional.'
        if result.get('dvipErrors') or result.get('unsupportedGpuModeObserved') or result.get('nativeCrashReportObserved'):result['state']='bloqueado'
        if 'Failed to create application support directories' in (a.output/'application.log').read_text():
            result.update(state='bloqueado',reason='Failed to create application support directories')
        return 0 if result['nativeRenderProven'] and result['mp4DeliveryValidated'] else 2
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
