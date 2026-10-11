#!/usr/bin/env python3
"""Download Drive media privately with bounded size, time and redirects."""
import argparse,json,os,re,time,urllib.parse,urllib.request,urllib.error
from pathlib import Path
from private_crypto import password_bytes
ALLOWED={'drive.google.com','drive.usercontent.google.com','drive.googleusercontent.com'}

def https_drive(url):
    try:
        p=urllib.parse.urlsplit(url)
        if p.scheme!='https' or p.hostname not in ALLOWED or p.username or p.password or p.port not in (None,443):raise ValueError
    except ValueError:raise ValueError('Use um link HTTPS do Google Drive; valor não registrado.') from None
    return p

def download_url(url):
    p=https_drive(url)
    if p.hostname=='drive.google.com':
        match=re.fullmatch(r'/file/d/([A-Za-z0-9_-]+)/view/?',p.path)
        identifier=match.group(1) if match else urllib.parse.parse_qs(p.query).get('id',[''])[0]
        if not re.fullmatch(r'[A-Za-z0-9_-]{10,200}',identifier):raise ValueError('Link de arquivo Drive inválido.')
        return 'https://drive.google.com/uc?export=download&id='+identifier
    return url

class DriveRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        https_drive(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def download(url,folder):
    folder.mkdir(parents=True,exist_ok=True,mode=0o700);os.chmod(folder,0o700)
    target=folder/'input-original.mp4';partial=folder/'input-original.partial'
    deadline=time.monotonic()+180;total=0
    try:
        opener=urllib.request.build_opener(DriveRedirect())
        with opener.open(urllib.request.Request(download_url(url),headers={'User-Agent':'Mozilla/5.0'}),timeout=30) as response,partial.open('wb') as out:
            os.chmod(partial,0o600)
            if 'text/html' in response.headers.get('Content-Type',''):raise ValueError('Drive retornou página, não mídia. Não há automação de login; confira o acesso compartilhado.')
            while True:
                if time.monotonic()>deadline:raise ValueError('Download privado excedeu 180 segundos.')
                data=response.read(1024*1024)
                if not data:break
                total+=len(data)
                if total>250*1024**2:raise ValueError('Entrada excedeu 250 MiB.')
                out.write(data)
        if total==0:raise ValueError('Entrada privada vazia.')
        partial.replace(target);return {'privateInputDownloaded':True,'downloadBytes':total,'published':False}
    finally:partial.unlink(missing_ok=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['availability','download']);p.add_argument('--private-dir',type=Path,required=True);a=p.parse_args()
    try:
        url=os.environ.get('DAVINCI_INPUT_VIDEO_URL','').strip();password_bytes(os.environ.get('DAVINCI_MEDIA_PASSWORD',''))
        if not url:raise ValueError('Configure DAVINCI_INPUT_VIDEO_URL em Secrets and variables → Actions; não publique o link.')
        download_url(url)
        result={'privateInputConfigured':True,'downloadStarted':False} if a.mode=='availability' else download(url,a.private_dir)
        print(json.dumps(result));return 0
    except urllib.error.HTTPError as exc:print(json.dumps({'state':'bloqueado','reason':'Drive recusou download: HTTP '+str(exc.code)}));return 2
    except Exception as exc:print(json.dumps({'state':'bloqueado','reason':str(exc) if isinstance(exc,ValueError) else 'Download privado falhou: '+type(exc).__name__}));return 2
if __name__=='__main__':raise SystemExit(main())
