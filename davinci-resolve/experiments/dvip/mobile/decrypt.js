async function decryptBytes(buffer, password) {
  const bytes = new Uint8Array(buffer);
  if (bytes.byteLength <= 52 || bytes.byteLength > 100 * 1024 * 1024 + 52) throw new Error('Arquivo inválido ou maior que 100 MiB.');
  if (new TextDecoder().decode(bytes.slice(0, 4)) !== 'DVR1') throw new Error('Este arquivo não é um resultado de vídeo protegido.');
  const iterations = new DataView(bytes.buffer, bytes.byteOffset + 32, 4).getUint32(0, false);
  if (iterations !== 600000) throw new Error('Formato de proteção não reconhecido.');
  if (!globalThis.crypto?.subtle) throw new Error('Abra esta página num contexto seguro (HTTPS ou arquivo local compatível).');
  const material = await crypto.subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveKey']);
  const key = await crypto.subtle.deriveKey({name: 'PBKDF2', salt: bytes.slice(4, 20), iterations, hash: 'SHA-256'}, material, {name: 'AES-GCM', length: 256}, false, ['decrypt']);
  let plain;
  try { plain = await crypto.subtle.decrypt({name: 'AES-GCM', iv: bytes.slice(20, 32), additionalData: bytes.slice(0, 36), tagLength: 128}, key, bytes.slice(36)); }
  catch { throw new Error('Senha incorreta ou arquivo alterado.'); }
  return {data: plain, mime: 'video/mp4', filename: 'meu-edit-davinci.mp4'};
}
if (typeof document !== 'undefined') {
  const form = document.getElementById('open-form'), status = document.getElementById('status');
  let previousUrl;
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const file = document.getElementById('file').files[0], password = document.getElementById('password');
    const button = document.getElementById('open'), link = document.getElementById('download');
    if (!file) { status.textContent = 'Selecione o arquivo final.dvr.'; return; }
    button.disabled = true; link.hidden = true; status.textContent = 'Abrindo o vídeo neste aparelho…';
    try {
      const result = await decryptBytes(await file.arrayBuffer(), password.value);
      if (previousUrl) URL.revokeObjectURL(previousUrl);
      previousUrl = URL.createObjectURL(new Blob([result.data], {type: result.mime}));
      link.href = previousUrl; link.download = result.filename; link.hidden = false;
      status.textContent = 'Arquivo validado. Toque em Baixar MP4.';
    } catch (error) { status.textContent = error.message; }
    finally { password.value = ''; button.disabled = false; }
  });
}
