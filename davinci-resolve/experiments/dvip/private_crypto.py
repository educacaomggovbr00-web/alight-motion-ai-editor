"""Authenticated envelopes for private media; keys never belong in a cache."""
import argparse,hashlib,hmac,json,os,struct
from pathlib import Path
ITERATIONS=600000
MAX_BYTES=250*1024**2
MAGICS={'delivery':b'DVR1','input':b'DVI1'}

def password_bytes(password):
    if len(password)<16:raise ValueError('Configure DAVINCI_MEDIA_PASSWORD com pelo menos 16 caracteres; não envie a senha em mensagens.')
    return password.encode('utf-8')

def encrypt(source,target,password,kind='delivery'):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    if not 0<source.stat().st_size<=MAX_BYTES:raise ValueError('Arquivo privado excede limite ou está vazio.')
    salt=os.urandom(16);nonce=os.urandom(12);header=MAGICS[kind]+salt+nonce+struct.pack('>I',ITERATIONS)
    key=hashlib.pbkdf2_hmac('sha256',password_bytes(password),salt,ITERATIONS,32)
    cipher=AESGCM(key).encrypt(nonce,source.read_bytes(),header)
    target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    target.write_bytes(header+cipher);os.chmod(target,0o600)
    return {'encrypted':True,'format':MAGICS[kind].decode(),'sizeBytes':target.stat().st_size,'plaintextPublished':False}

def decrypt(source,target,password,kind='input'):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    if not 52<source.stat().st_size<=MAX_BYTES+52:raise ValueError('Envelope privado inválido.')
    data=source.read_bytes();header=data[:36]
    if header[:4]!=MAGICS[kind] or struct.unpack('>I',header[32:36])[0]!=ITERATIONS:raise ValueError('Formato ou parâmetros privados inválidos.')
    key=hashlib.pbkdf2_hmac('sha256',password_bytes(password),header[4:20],ITERATIONS,32)
    plain=AESGCM(key).decrypt(header[20:32],data[36:],header)
    target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    target.write_bytes(plain);os.chmod(target,0o600)
    return {'authenticatedDecryption':True}

def input_cache_key(source,password,recipe):
    source_hash=hashlib.sha256(source.read_bytes()).digest()
    key=hashlib.sha256(password_bytes(password)).digest()
    return 'dvr-input-private-v1-'+hmac.new(key,source_hash+recipe.encode('utf-8'),hashlib.sha256).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['encrypt','decrypt','cache-key']);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path);p.add_argument('--kind',choices=list(MAGICS),default='delivery');p.add_argument('--recipe',default='45-60s;540x960;30fps;DNxHR-LB;PCM48k;v1');a=p.parse_args()
    try:
        password=os.environ.get('DAVINCI_MEDIA_PASSWORD','')
        if a.mode=='cache-key':print(input_cache_key(a.input,password,a.recipe));return 0
        if a.output is None:raise ValueError('Destino privado ausente.')
        result=(encrypt if a.mode=='encrypt' else decrypt)(a.input,a.output,password,a.kind)
        print(json.dumps(result));return 0
    except Exception as exc:
        print(json.dumps({'state':'bloqueado','reason':str(exc) if isinstance(exc,ValueError) else 'Envelope recusado: '+type(exc).__name__}));return 2
if __name__=='__main__':raise SystemExit(main())
