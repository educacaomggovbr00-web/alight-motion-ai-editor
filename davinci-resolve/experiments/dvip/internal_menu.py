"""Invoke only our installed script through the documented Workspace menu."""
import re,time
from pathlib import Path

TARGET='codexsyntheticsmoke'
def normalized(value):return ''.join(c for c in value.lower() if c.isalnum())

def labels(tsv, scale=2):
    groups={}
    for line in tsv.splitlines():
        r=line.split('\t')
        if len(r)<12 or r[0]!='5' or not r[11].strip():continue
        try:
            if float(r[10])<30:continue
            box=tuple(int(r[i]) for i in range(6,10))
        except ValueError:continue
        groups.setdefault(tuple(r[1:5]),[]).append((r[11],box))
    out=[]
    for words in groups.values():
        variants=[words]+[[word] for word in words]
        for variant in variants:
            left=min(w[1][0] for w in variant);top=min(w[1][1] for w in variant)
            right=max(w[1][0]+w[1][2] for w in variant);bottom=max(w[1][1]+w[1][3] for w in variant)
            out.append({'text':' '.join(w[0] for w in variant),'key':normalized(''.join(w[0] for w in variant)),
                        'x':(left+right)//(2*scale),'y':(top+bottom)//(2*scale)})
    return out

def choose(rows, key, top_only=False):
    matches=[r for r in rows if r['key'] in (key,key+'py') and (not top_only or r['y']<35)]
    return matches[0] if matches else None

def invoke(output, env, run):
    result={'attempted':False,'scriptMenuInvoked':False,'actions':[]}
    def capture(index):
        screen=output/f'internal-menu-{index}.png';large=output/f'internal-menu-ocr-{index}.png'
        status,_=run(['import','-window','root',str(screen)],env,10)
        if status['exitCode']:return []
        status,_=run(['convert',str(screen),'-resize','200%',str(large)],env,10)
        if status['exitCode']:return []
        _,tsv=run(['tesseract',str(large),'stdout','--psm','11','tsv'],env,15,output/f'internal-menu-{index}.log')
        rows=labels(tsv)
        text=' '.join(r['text'] for r in rows).lower()
        if any(s in text for s in ['license agreement','terms and conditions','sign in','license key']):return []
        return rows
    def act(row,click):
        argv=['xdotool','mousemove','--sync',str(row['x']),str(row['y'])]
        if click:argv+=['click','1']
        status,_=run(argv,env,5)
        result['actions'].append({'recognizedLabel':row['text'],'clicked':click,'exitCode':status['exitCode']})
        time.sleep(1)
        return status['exitCode']==0
    rows=capture(0);workspace=choose(rows,'workspace',top_only=True)
    if workspace is None:
        result['reason']='Menu Workspace não reconhecido com segurança.';return result
    result['attempted']=True
    if not act(workspace,True):return result
    rows=capture(1);scripts=choose(rows,'scripts')
    if scripts is None:
        result['reason']='Submenu Scripts ausente ou não reconhecido.';run(['xdotool','key','Escape'],env,5);return result
    if not act(scripts,False):return result
    rows=capture(2);target=choose(rows,TARGET)
    if target is None:
        utility=choose(rows,'utility')
        if utility is not None and act(utility,False):target=choose(capture(3),TARGET)
    if target is None:
        result['reason']='Script instalado não aparece no menu; nenhuma licença/preferência alterada.';run(['xdotool','key','Escape'],env,5);return result
    result['scriptMenuInvoked']=act(target,True)
    result['reason']='Comando enviado ao menu; execução deve ser confirmada pelo relatório do script.'
    return result
