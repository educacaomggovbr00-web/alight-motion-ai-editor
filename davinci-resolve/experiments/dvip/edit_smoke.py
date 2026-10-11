#!/usr/bin/env python3
"""Official SDK test: native edit/render; optional MP4 packaging is separate."""
import json,os,time,uuid
from pathlib import Path

def choose_render(project):
    formats=project.GetRenderFormats() or {}
    mp4=project.GetRenderCodecs('mp4') or {} if 'mp4' in formats.values() else {}
    h264=next((v for k,v in mp4.items() if 'h264' in ''.join(c for c in k.lower() if c.isalnum())),None)
    if h264:return ('mp4',h264),{'renderFormats':formats,'mp4Codecs':mp4}
    mov=project.GetRenderCodecs('mov') or {} if 'mov' in formats.values() else {}
    candidates=[(k,v) for k,v in mov.items() if 'dnxhr' in ''.join(c for c in k.lower() if c.isalnum())]
    candidate=next((v for k,v in candidates if 'lb' in k.lower()),candidates[0][1] if candidates else None)
    return (('mov',candidate) if candidate else None),{'renderFormats':formats,'mp4Codecs':mp4,'movCodecs':mov}

def exercise(resolve,video,output,render_seconds=180):
    r={'state':'bloqueado','apiConnected':False,'projectCreated':False,'mediaImported':False,'timelineCreated':False,'effectApplied':False,'exportProven':False}
    def checkpoint():
        (output/'sdk-progress.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    if resolve is None:
        r['reason']='API sem conexão. Não alteramos preferências/licença; testar menu interno oficial.';return r
    output.mkdir(parents=True,exist_ok=True)
    r['apiConnected']=True;r['version']=resolve.GetVersion();checkpoint()
    if list(r['version'][:3])!=[21,1,1]:r['reason']='Versão real diferente de 21.1.1.';return r
    pm=resolve.GetProjectManager();project=pm.CreateProject('Codex_Synthetic_'+uuid.uuid4().hex[:12])
    if not project:r['reason']='CreateProject não criou projeto.';return r
    r['projectCreated']=True;checkpoint()
    if not project.SetSettings({'timelineFrameRate':'30','timelineResolutionWidth':'640','timelineResolutionHeight':'360'}):
        r['reason']='Configuração de timeline recusada.';return r
    pool=project.GetMediaPool();clips=pool.ImportMedia([str(video)])
    if not clips:r['reason']='ImportMedia não importou mídia sintética.';return r
    r['mediaImported']=True;checkpoint()
    timeline=pool.CreateTimelineFromClips('Codex_Synthetic_Timeline',[{'mediaPoolItem':c} for c in clips])
    if not timeline or not project.SetCurrentTimeline(timeline):r['reason']='Timeline não criada/selecionada.';return r
    r['timelineCreated']=True;checkpoint()
    items=timeline.GetItemListInTrack('video',1) or []
    if items:
        # API names verified against the SDK 21.1.1 .pyi, not legacy SetProperty.
        accepted=items[0].SetProperties({'TransformEnabled':True,'ZoomX':1.06,'ZoomY':1.06,'ZoomGang':True})
        props=items[0].GetProperties() or {}
        r['effectApplied']=bool(accepted and abs(float(props.get('ZoomX',0))-1.06)<.001 and abs(float(props.get('ZoomY',0))-1.06)<.001)
        r['effect']='zoom estático 1.06' if r['effectApplied'] else 'transformação não confirmada'
    r['projectSaved']=bool(pm.SaveProject());resolve.OpenPage('edit');checkpoint()
    chosen,capabilities=choose_render(project);r.update(capabilities)
    if not chosen:r['reason']='Nem H.264 MP4 nem DNxHR MOV foram anunciados pelo Resolve.';return r
    fmt,codec=chosen;r.update(nativeFormat=fmt,nativeCodec=codec)
    if not project.SetCurrentRenderFormatAndCodec(fmt,codec):r['reason']='Seleção do codec nativo recusada.';return r
    project.SetCurrentRenderMode(1)
    settings={'TargetDir':str(output),'CustomName':'resolve-synthetic','SelectAllFrames':True,'ExportVideo':True,'ExportAudio':True,'FormatWidth':640,'FormatHeight':360,'FrameRate':30}
    if fmt=='mov':settings.update(AudioBitDepth=16,AudioSampleRate=48000)
    if not project.SetRenderSettings(settings):r['reason']='SetRenderSettings recusado.';return r
    job=project.AddRenderJob();r['renderJobId']=job;checkpoint()
    if not job or not project.StartRendering([job]):r['reason']='Job real não iniciou.';return r
    deadline=time.monotonic()+render_seconds
    while project.IsRenderingInProgress():
        if time.monotonic()>deadline:
            project.StopRendering();r['reason']='Render excedeu limite; somente este job foi interrompido.';return r
        time.sleep(1)
    r['renderStatus']=project.GetRenderJobStatus(job)
    if not r['renderStatus'] or r['renderStatus'].get('JobStatus')!='Complete':r['reason']='Resolve não confirmou render Complete.';return r
    target=output/('resolve-synthetic.'+fmt)
    r['renderProducedFile']=target.is_file() and target.stat().st_size>0;r['nativeFileName']=target.name
    r['state']='testado' if r['renderProducedFile'] else 'bloqueado'
    r['reason']='Render produzido pelo Resolve; ainda exige FFprobe. MOV pode receber embalagem MP4 auxiliar explicitamente separada.'
    checkpoint();return r

def main():
    out=Path(os.environ['CODEX_RENDER_OUTPUT']);video=Path(os.environ['CODEX_SYNTHETIC_VIDEO']);out.mkdir(parents=True,exist_ok=True)
    app=globals().get('resolve');context='internal-globals' if app is not None else 'external-sdk'
    (out/'sdk-started.json').write_text(json.dumps({'context':context,'internalResolveGlobalPresent':app is not None}))
    result={'state':'bloqueado','exportProven':False}
    try:
        if app is None:
            import DaVinciResolveScript as sdk
            app=sdk.scriptapp('Resolve')
        result=exercise(app,video,out)
    except Exception as exc:
        partial=out/'sdk-progress.json'
        if partial.exists():result=json.loads(partial.read_text())
        result.update(state='bloqueado',exportProven=False,reason='SDK falhou: '+type(exc).__name__)
    result['invocationContext']=context
    (out/'sdk-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__' or globals().get('resolve') is not None:main()
