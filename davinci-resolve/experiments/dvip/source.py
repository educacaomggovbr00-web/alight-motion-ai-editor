#!/usr/bin/env python3
"""Official DaVinci Resolve 21.1.2 ZIP downloader, isolated and audited.
No SHA-256 for 21.1.2 was previously observed: runtime hashes are NOT vendor signatures.
"""
import argparse, hashlib, json, os, re, signal, subprocess, time, urllib.error, urllib.parse, urllib.request, zipfile
from pathlib import Path

# A edicao vem SOMENTE do caminho oficial da URL na variavel de ambiente.
# Nunca confiar em nomes arbitrarios de arquivo enviados pelo usuario.
FREE_URL_PATH = '/DaVinciResolve/v21.1.2/DaVinci_Resolve_21.1.2_Linux.zip'
STUDIO_URL_PATH = '/DaVinciResolve/v21.1.2/DaVinci_Resolve_Studio_21.1.2_Linux.zip'
source_path = urllib.parse.urlsplit(os.environ.get('DAVINCI_RESOLVE_LINUX_URL', '')).path
EDITION = 'studio' if source_path == STUDIO_URL_PATH else 'free'
NAME = ('DaVinci_Resolve_Studio_21.1.2_Linux.run' if EDITION == 'studio'
        else 'DaVinci_Resolve_21.1.2_Linux.run')
URL_PATH = STUDIO_URL_PATH if EDITION == 'studio' else FREE_URL_PATH
# Optional independently obtained pinned installer hash, for stronger verification.
RUN_SHA256 = os.environ.get('DAVINCI_RESOLVE_2112_SHA256','').strip().lower()
BINARY_SHA256 = ''  # Captured from the extracted official package; not a vendor-published reference.
MANIFEST = 'official-source-21.1.2-' + EDITION + '.json'

class Blocked(Exception): pass

def validate_url(url, now=None):
    try:
        p = urllib.parse.urlsplit(url)
        if (p.scheme != 'https' or p.hostname != 'sw.blackmagicdesign.com'
                or p.port not in (None,443) or p.username or p.password or p.fragment
                or urllib.parse.unquote(p.path) != URL_PATH):
            raise Blocked('Somente download HTTPS oficial Resolve 21.1.2 (Free ou Studio) permitido.')
        expires = urllib.parse.parse_qs(p.query).get('Expires')
        if expires and (len(expires)!=1 or int(expires[0]) <= (time.time() if now is None else now)):
            raise Blocked('URL oficial expirada; atualize o Secret DAVINCI_RESOLVE_LINUX_URL.')
        if RUN_SHA256 and not re.fullmatch(r'[a-f0-9]{64}',RUN_SHA256):
            raise Blocked('SHA-256 fixado invalido.')
    except (ValueError, TypeError):
        raise Blocked('URL oficial invalida; URL nao registrada.') from None
    return url

class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def _manifest(directory):
    p=directory/MANIFEST
    if not p.is_file(): raise Blocked('Manifesto de download oficial ausente; nao executar.')
    try:
        j=json.loads(p.read_text())
    except (ValueError,OSError): raise Blocked('Manifesto de download invalido.') from None
    if j.get('version')!='21.1.2' or j.get('edition', 'free')!=EDITION or not re.fullmatch('[a-f0-9]{64}',str(j.get('installerSha256',''))):
        raise Blocked('Metadados de integridade invalidos.')
    return j

def download(url, directory, seconds=1800):
    validate_url(url)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    run=directory/NAME
    if run.exists():
        if not run.is_file() or run.is_symlink(): raise Blocked('Instalador local inseguro.')
        sha=digest(run)
        # For test fixtures and user-pinned sha, permit local reuse without manifest.
        if RUN_SHA256 and sha==RUN_SHA256:
            return run, {'downloadRepeated':False,'installerSha256':sha,'hashPinned':True}
        if _manifest(directory).get('installerSha256')!=sha:
            raise Blocked('Instalador local diverge do manifesto.')
        return run, {'downloadRepeated':False,'installerSha256':sha,'hashPinned':False}
    archive=directory/'official-private.zip'
    deadline=time.monotonic()+seconds
    total=0
    opener=urllib.request.build_opener(OfficialRedirect())
    try:
        with opener.open(urllib.request.Request(url,headers={'User-Agent':'Resolve-CI-Experiment/1.1'}),timeout=30) as response, archive.open('xb') as out:
            os.chmod(archive,0o600)
            while True:
                if time.monotonic()>deadline: raise Blocked('Tempo maximo do download oficial atingido.')
                chunk=response.read(1024*1024)
                if not chunk: break
                total+=len(chunk)
                if total>12*1024**3: raise Blocked('Download excede o limite de segurança de 12 GiB.')
                out.write(chunk)
        with zipfile.ZipFile(archive) as z:
            matches=[i for i in z.infolist() if i.filename==NAME and not i.is_dir()]
            if len(matches)!=1 or matches[0].file_size>12*1024**3 or matches[0].file_size<100_000:
                raise Blocked('Pacote oficial nao contem o instalador 21.1.2 esperado.')
            with z.open(matches[0]) as f,run.open('xb') as out:
                os.chmod(run,0o600)
                copied=0
                while True:
                    b=f.read(1024*1024)
                    if not b:break
                    copied+=len(b)
                    if copied>12*1024**3:raise Blocked('Arquivo extraido excede 12 GiB.')
                    out.write(b)
            if copied!=matches[0].file_size: raise Blocked('Extração ZIP incompleta.')
        sha=digest(run)
        if RUN_SHA256 and sha!=RUN_SHA256: raise Blocked('Hash do .run diverge do SHA-256 informado.')
        manifest={'version':'21.1.2','edition':EDITION,'installerSha256':sha,
                  'hashPinned':bool(RUN_SHA256),'officialHostChecked':True,
                  'officialUrlPathChecked':True,'vendorPublishedHashVerified':False,
                  'archiveBytes':total}
        (directory/MANIFEST).write_text(json.dumps(manifest,indent=2)+'\n')
        os.chmod(directory/MANIFEST,0o600)
        os.chmod(run,0o700)
        return run, {'downloadRepeated':True,'downloadBytes':total,'installerSha256':sha,
                     'hashPinned':bool(RUN_SHA256)}
    except urllib.error.HTTPError as exc:
        raise Blocked(f'Download oficial recusado: HTTP {exc.code}. Verifique validade do Secret.') from None
    except (urllib.error.URLError,TimeoutError):
        raise Blocked('Falha de conexão oficial; URL nao registrada.') from None
    except zipfile.BadZipFile:
        raise Blocked('ZIP oficial invalido.') from None
    finally:
        archive.unlink(missing_ok=True)
        if not (directory/MANIFEST).is_file() and run.exists() and not RUN_SHA256:
            run.unlink(missing_ok=True)

def extract(run, directory):
    manifest=_manifest(directory)
    if not run.is_file() or run.is_symlink() or digest(run)!=manifest['installerSha256']:
        raise Blocked('Instalador nao corresponde ao download oficial observado.')
    if RUN_SHA256 and digest(run)!=RUN_SHA256: raise Blocked('Hash fixado divergente.')
    binary=directory/'squashfs-root/bin/resolve'
    if not (binary.is_file() and (directory/'squashfs-root/resolve-original-metadata.json').is_file()):
        env={k:v for k,v in os.environ.items() if k not in ('DAVINCI_RESOLVE_LINUX_URL','DAVINCI_RESOLVE_2112_SHA256')}
        with (directory/'extraction-private.log').open('wb') as log:
            p=subprocess.Popen([str(run),'--appimage-extract'],cwd=directory,env=env,stdout=log,stderr=log,start_new_session=True)
            try:
                if p.wait(timeout=900)!=0: raise Blocked('Extracao oficial falhou; consultar log privado.')
            except subprocess.TimeoutExpired:
                raise Blocked('Extracao excedeu 900s.') from None
            finally:
                try:os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                p.wait(timeout=5)
    if not binary.is_file() or binary.is_symlink(): raise Blocked('Binario Resolve ausente.')
    binary_sha=digest(binary)
    # Expected for supervisor at start and end; a runtime observation, not a signature.
    metadata={'version':'21.1.2','edition':EDITION,'installerSha256':manifest['installerSha256'],
              'binarySha256':binary_sha,'hashPinned':bool(RUN_SHA256),
              'vendorPublishedHashVerified':False,'originalPayloadModified':False}
    (directory/'squashfs-root/resolve-original-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    return {'state':'experimental',**metadata,'nativeInstallationProven':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['availability','download','extract'])
    p.add_argument('--private-dir',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    result={'state':'bloqueado','resolveStarted':False}
    try:
        url=os.environ.get('DAVINCI_RESOLVE_LINUX_URL','').strip()
        if a.mode=='extract': result=extract(a.private_dir/NAME,a.private_dir)
        else:
            if not url:raise Blocked('Secret DAVINCI_RESOLVE_LINUX_URL ausente; nao baixou nada.')
            validate_url(url)
            if a.mode=='availability': result={'state':'experimental','sourceAvailable':True,'downloadStarted':False,'version':'21.1.2','edition':EDITION,'studioLicenseNotAutomated':EDITION=='studio'}
            else:_,result=download(url,a.private_dir)
        return 0
    except Blocked as exc:
        result['reason']=str(exc);return 2
    except (OSError,ValueError,zipfile.BadZipFile):
        result['reason']='Falha de arquivo/entrada; URL nao foi registrada.';return 2
    finally:
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__': raise SystemExit(main())
