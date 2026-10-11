#!/usr/bin/env python3
"""Private DNxHR/PCM input conversion, never a substitute for Resolve editing."""
import argparse,json,math,os,signal,subprocess
from pathlib import Path

def inspect(path):
    p=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],capture_output=True,text=True,timeout=20)
    if p.returncode:raise ValueError('FFprobe rejeitou a mídia.')
    return json.loads(p.stdout)

def prepare(source,directory,start=45,duration=15):
    if not source.is_file() or source.suffix.lower()!='.mp4' or not 0<source.stat().st_size<=250*1024**2:raise ValueError('Entrada deve ser MP4 local até 250 MiB.')
    if not all(math.isfinite(v) for v in (start,duration)) or start<0 or not 1<=duration<=30:raise ValueError('Trecho exige início não negativo e duração entre 1 e 30 segundos.')
    original=inspect(source);streams=original['streams'];length=float(original['format']['duration'])
    if start+duration>length+.03:raise ValueError('Trecho solicitado excede a duração do vídeo.')
    if not any(s['codec_type']=='video' for s in streams) or not any(s['codec_type']=='audio' for s in streams):raise ValueError('Vídeo e áudio original são necessários.')
    directory.mkdir(parents=True,exist_ok=True,mode=0o700);os.chmod(directory,0o700)
    partial=directory/'input-prepared.partial.mov';target=directory/'input-prepared.mov'
    argv=['ffmpeg','-y','-v','error','-ss',str(start),'-i',str(source),'-t',str(duration),'-map','0:v:0','-map','0:a:0','-map_metadata','-1','-vf','scale=540:960:force_original_aspect_ratio=decrease,pad=540:960:(ow-iw)/2:(oh-ih)/2:black,fps=30','-c:v','dnxhd','-profile:v','dnxhr_lb','-pix_fmt','yuv422p','-c:a','pcm_s16le','-ar','48000',str(partial)]
    with (directory/'prepare-private.log').open('wb') as log:
        p=subprocess.Popen(argv,stdout=log,stderr=log,start_new_session=True)
        try:
            if p.wait(timeout=120):raise ValueError('Conversão auxiliar falhou; log permanece privado.')
        except subprocess.TimeoutExpired:raise ValueError('Preparação excedeu 120 segundos.') from None
        finally:
            if p.poll() is None:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=5)
    data=inspect(partial);video=next(s for s in data['streams'] if s['codec_type']=='video');audio=next(s for s in data['streams'] if s['codec_type']=='audio')
    if video['codec_name']!='dnxhd' or (video['width'],video['height'])!=(540,960) or audio['codec_name']!='pcm_s16le' or abs(float(data['format']['duration'])-duration)>.1:raise ValueError('Entrada preparada não atende DNxHR/PCM e duração.')
    partial.replace(target);os.chmod(target,0o600)
    report={'state':'testado','inputPreparationOnly':True,'editedByResolve':False,'published':False,'cached':False,'sourceStartSeconds':start,'durationSeconds':duration,'width':540,'height':960,'fps':30,'videoCodec':video['codec_name'],'audioCodec':audio['codec_name'],'originalAudioContentPreserved':True,'originalFramingFitWithBlackPadding':True}
    (directory/'prepare-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');os.chmod(directory/'prepare-report.json',0o600)
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--private-dir',type=Path,required=True);p.add_argument('--start',type=float,default=45);p.add_argument('--duration',type=float,default=15);a=p.parse_args()
    try:print(json.dumps(prepare(a.input,a.private_dir,a.start,a.duration),ensure_ascii=False));return 0
    except (OSError,ValueError,subprocess.TimeoutExpired) as exc:print(json.dumps({'state':'bloqueado','reason':str(exc) if isinstance(exc,ValueError) else type(exc).__name__},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
