#!/usr/bin/env python3
"""SDK smoke test. Requires a real running Resolve; no fabricated render."""
import json, os, time, uuid
from pathlib import Path

def exercise(resolve, video, output, render_seconds=60):
    r={'state':'bloqueado','apiConnected':False,'projectCreated':False,'mediaImported':False,'timelineCreated':False,'exportProven':False}
    if resolve is None:
        r['reason']='API sem conexão. Não alteramos preferências/licença. SDK 21.1.1 documenta scripting externo no Studio; use script interno se necessário.';return r
    r['apiConnected']=True;r['version']=resolve.GetVersion()
    if list(r['version'][:3])!=[21,1,1]: r['reason']='Versão real diferente de 21.1.1.';return r
    pm=resolve.GetProjectManager();project=pm.CreateProject('Codex_Synthetic_'+uuid.uuid4().hex[:12])
    if not project: r['reason']='CreateProject não criou projeto.';return r
    r['projectCreated']=True
    if not project.SetSettings({'timelineFrameRate':'30','timelineResolutionWidth':'640','timelineResolutionHeight':'360'}):
        r['reason']='Configuração de timeline recusada.';return r
    pool=project.GetMediaPool(); clips=pool.ImportMedia([str(video)])
    if not clips: r['reason']='ImportMedia não importou mídia sintética.';return r
    r['mediaImported']=True
    timeline=pool.CreateTimelineFromClips('Codex_Synthetic_Timeline',[{'mediaPoolItem':c} for c in clips])
    if not timeline or not project.SetCurrentTimeline(timeline): r['reason']='Timeline não criada/selecionada.';return r
    r['timelineCreated']=True;r['projectSaved']=bool(pm.SaveProject());resolve.OpenPage('edit')
    formats=project.GetRenderFormats() or {};r['renderFormats']=formats
    if 'mp4' not in formats.values(): r['reason']='MP4 não disponível na edição/runtime instalado.';return r
    codecs=project.GetRenderCodecs('mp4') or {};r['mp4Codecs']=codecs
    codec=next((v for k,v in codecs.items() if 'h264' in ''.join(c for c in k.lower() if c.isalnum())),None)
    if not codec: r['reason']='H.264 MP4 não disponível; não substituímos render por FFmpeg.';return r
    if not project.SetCurrentRenderFormatAndCodec('mp4',codec): r['reason']='Seleção H.264 MP4 recusada.';return r
    project.SetCurrentRenderMode(1);output.mkdir(parents=True,exist_ok=True)
    if not project.SetRenderSettings({'TargetDir':str(output),'CustomName':'resolve-synthetic','SelectAllFrames':True,'ExportVideo':True,'ExportAudio':False,'FormatWidth':640,'FormatHeight':360,'FrameRate':30}):
        r['reason']='SetRenderSettings recusado.';return r
    job=project.AddRenderJob();r['renderJobId']=job
    if not job or not project.StartRendering([job]): r['reason']='Job real não iniciou.';return r
    deadline=time.monotonic()+render_seconds
    while project.IsRenderingInProgress():
        if time.monotonic()>deadline:
            project.StopRendering();r['reason']='Render excedeu limite; somente este job foi interrompido.';return r
        time.sleep(1)
    r['renderStatus']=project.GetRenderJobStatus(job)
    if not r['renderStatus'] or r['renderStatus'].get('JobStatus')!='Complete': r['reason']='Resolve não confirmou render Complete.';return r
    target=output/'resolve-synthetic.mp4'
    r['renderProducedFile']=target.is_file() and target.stat().st_size>0
    r['state']='testado' if r['renderProducedFile'] else 'bloqueado'
    r['reason']='Arquivo produzido pelo Resolve; ainda exige validação independente FFprobe.'
    return r

def main():
    out=Path(os.environ['CODEX_RENDER_OUTPUT']);video=Path(os.environ['CODEX_SYNTHETIC_VIDEO']);out.mkdir(parents=True,exist_ok=True)
    result={'state':'bloqueado','exportProven':False}
    try:
        app=globals().get('resolve')
        if app is None:
            import DaVinciResolveScript as sdk
            deadline=time.monotonic()+10
            while app is None and time.monotonic()<deadline:
                app=sdk.scriptapp('Resolve')
                if app is None: time.sleep(1)
        result=exercise(app,video,out)
    except Exception as exc:
        result={'state':'bloqueado','exportProven':False,'reason':'SDK falhou: '+type(exc).__name__}
    (out/'sdk-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__' or globals().get('resolve') is not None: main()
