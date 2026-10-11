#!/usr/bin/env python3
"""Private, bounded retrieval of the unmodified official 21.1.1 installer."""
import argparse, hashlib, json, os, signal, subprocess, time, urllib.error, urllib.parse, urllib.request, zipfile
from pathlib import Path
RUN_SHA256 = '6ed698d0b1bd7fe2fa97076fae0c24f9e0cdd0fdeaf0cfea9a8a3df730a48a15'
BINARY_SHA256 = 'd083cf9f1eb875bdb928db54b20425b4111b53a16cae72a1aef1c3eeb603a121'
NAME = 'DaVinci_Resolve_21.1.1_Linux.run'
URL_PATH = '/DaVinciResolve/v21.1.1/DaVinci_Resolve_21.1.1_Linux.zip'
class Blocked(Exception): pass

def validate_url(url, now=None):
    try:
        p = urllib.parse.urlsplit(url)
        if (p.scheme != 'https' or p.hostname != 'sw.blackmagicdesign.com' or p.port not in (None,443)
                or p.username or p.password or p.fragment or urllib.parse.unquote(p.path) != URL_PATH):
            raise Blocked('Use somente a URL HTTPS oficial do Resolve 21.1.1 Linux.')
        expires = urllib.parse.parse_qs(p.query).get('Expires')
        if expires and (len(expires)!=1 or int(expires[0]) <= (time.time() if now is None else now)):
            raise Blocked('Link oficial expirado. Configure um novo no segredo DAVINCI_RESOLVE_LINUX_URL.')
    except (ValueError, TypeError):
        raise Blocked('URL oficial inválida; nenhuma URL foi registrada.') from None
    return url

class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def download(url, directory, seconds=600):
    validate_url(url)
    directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    run=directory/NAME
    if run.exists():
        if digest(run)!=RUN_SHA256: raise Blocked('Instalador existente diverge da amostra oficial anterior.')
        return run, {'downloadRepeated':False,'installerSha256':RUN_SHA256}
    archive=directory/'official-private.zip'
    deadline=time.monotonic()+seconds; total=0
    opener=urllib.request.build_opener(OfficialRedirect())
    try:
        with opener.open(urllib.request.Request(url,headers={'User-Agent':'Resolve-CI-Experiment/1.0'}),timeout=30) as response, archive.open('wb') as out:
            os.chmod(archive,0o600)
            while True:
                if time.monotonic()>deadline: raise Blocked('Tempo máximo do download oficial atingido.')
                chunk=response.read(1024*1024)
                if not chunk: break
                total+=len(chunk)
                if total>6*1024**3: raise Blocked('Download excedeu o limite de 6 GiB.')
                out.write(chunk)
        with zipfile.ZipFile(archive) as z:
            matches=[i for i in z.infolist() if i.filename==NAME]
            if len(matches)!=1 or matches[0].file_size>5*1024**3: raise Blocked('Pacote oficial não contém o instalador esperado.')
            with z.open(matches[0]) as f, run.open('wb') as out:
                os.chmod(run,0o600)
                for b in iter(lambda:f.read(1024*1024),b''): out.write(b)
        if digest(run)!=RUN_SHA256:
            run.unlink(missing_ok=True)
            raise Blocked('SHA-256 do instalador diferente da amostra oficial 21.1.1 anterior; execução recusada.')
        os.chmod(run,0o700)
        return run, {'downloadRepeated':True,'downloadBytes':total,'installerSha256':RUN_SHA256}
    except urllib.error.HTTPError as exc:
        raise Blocked(f'Download oficial recusado: HTTP {exc.code}. Verifique a validade do segredo.') from None
    except (urllib.error.URLError,TimeoutError):
        raise Blocked('Falha de conexão com a fonte oficial; URL não registrada.') from None
    except zipfile.BadZipFile:
        raise Blocked('Resposta oficial não era um ZIP válido.') from None
    finally:
        archive.unlink(missing_ok=True)

def extract(run, directory):
    if digest(run)!=RUN_SHA256: raise Blocked('Instalador não verificado; extração recusada.')
    binary=directory/'squashfs-root/bin/resolve'
    if not binary.exists():
        env={k:v for k,v in os.environ.items() if k not in ('DAVINCI_RESOLVE_LINUX_URL',)}
        with (directory/'extraction-private.log').open('wb') as log:
            p=subprocess.Popen([str(run),'--appimage-extract'],cwd=directory,env=env,stdout=log,stderr=log,start_new_session=True)
            try:
                if p.wait(timeout=240)!=0: raise Blocked('Extração do instalador falhou; consulte apenas o log privado do job.')
            except subprocess.TimeoutExpired:
                raise Blocked('Extração excedeu 240 segundos.') from None
            finally:
                try: os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError: pass
                p.wait(timeout=5)
    if not binary.exists() or digest(binary)!=BINARY_SHA256: raise Blocked('Executável extraído diverge do Resolve original anteriormente observado.')
    return {'state':'experimental','installerSha256':RUN_SHA256,'resolveSha256':BINARY_SHA256,'originalPayloadModified':False,'nativeInstallationProven':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['availability','download','extract']);p.add_argument('--private-dir',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    result={'state':'bloqueado','resolveStarted':False}
    try:
        url=os.environ.get('DAVINCI_RESOLVE_LINUX_URL','').strip()
        if a.mode=='extract': result=extract(a.private_dir/NAME,a.private_dir)
        else:
            if not url: raise Blocked('Segredo DAVINCI_RESOLVE_LINUX_URL não configurado; nenhum download iniciado.')
            validate_url(url)
            if a.mode=='availability': result={'state':'experimental','sourceAvailable':True,'downloadStarted':False}
            else: _,result=download(url,a.private_dir)
        return 0
    except Blocked as exc:
        result['reason']=str(exc);return 2
    except (OSError,ValueError):
        result['reason']='Erro de arquivo/entrada; nenhum link foi registrado.';return 2
    finally:
        a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__': raise SystemExit(main())
