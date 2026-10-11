"""Gemini: uma chamada para ouvir audio, transcrever e traduzir para pt-BR.

Nunca registra chave, conteudo integral da resposta ou audio no log Actions.
Canto pode gerar erros; omita trechos incertos e revise antes de publicar.
"""
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

MODEL = "gemini-3.8-flash"
MAX_SEGMENTS = 70
SCHEMA = {
    "type": "object",
    "properties": {
        "language": {"type": "string"},
        "segments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "start": {"type": "number"},
                    "end": {"type": "number"},
                    "original": {"type": "string"},
                    "pt_br": {"type": "string"},
                    "clarity": {"type": "string", "enum": ["clear", "uncertain"]},
                },
                "required": ["start", "end", "original", "pt_br", "clarity"],
            },
        },
    },
    "required": ["language", "segments"],
}
PROMPT = """Listen to this audio once and return structured JSON only.
Transcribe the ACTUALLY AUDIBLE sung or spoken vocals, preserving the original
language. Translate each audible short phrase naturally into Brazilian Portuguese
(pt-BR) in the SAME response. Include relative start and end timestamps in
SECONDS from 0 for this clip, using short phrases (preferably 1-6 words).
The clip may have music, rap, distortion, adlibs, or livestream chatter.
- The provided audio is your ONLY source. Do NOT use memorized song lyrics,
  presumed lyrics, genre stereotypes or guesses to fill uncertain gaps.
- Do not hallucinate missing verses. Instrumental sections yield no segments.
- Mark partly inaudible/ambiguous passages clarity=uncertain and do not guess.
- For reliable passages mark clarity=clear, original=the heard words, pt_br=translation.
- Keep segments chronological; time estimates are approximate phrase timing,
  not reliable word-level forced alignment.
- Do not translate on-screen content; this is audio-only.
- If words cannot reliably be heard, return an empty segments array.
"""

def clean_text(value):
    if not isinstance(value, str):
        raise ValueError("Texto Gemini invalido")
    value = re.sub(r"[\x00-\x1f\x7f]", " ", value).strip()
    if len(value) > 240:
        raise ValueError("Segmento excede limite")
    return value

def split_phrase(text, limit=40):
    parts, current = [], ""
    for token in text.split():
        if len(token) > limit:
            raise ValueError("Palavra de legenda longa demais")
        if len(current) + len(token) + (1 if current else 0) > limit:
            parts.append(current)
            current = token
        else:
            current = (current + " " if current else "") + token
    if current:
        parts.append(current)
    return parts

def transform_response(raw, duration):
    """Rejeita resposta malformada antes de gravar qualquer legenda."""
    if isinstance(raw, str):
        raw = json.loads(raw)
    if not isinstance(raw, dict) or not isinstance(raw.get("segments"), list):
        raise ValueError("Formato Gemini invalido")
    segments = raw["segments"]
    if len(segments) > MAX_SEGMENTS:
        raise ValueError("Muitos segmentos")
    if type(duration) not in (int, float) or not math.isfinite(duration) or not 1 <= duration <= 30:
        raise ValueError("Duracao invalida")
    words, review = [], []
    uncertain, previous = 0, -1.0
    for seg in segments:
        if not isinstance(seg, dict):
            raise ValueError("Segmento invalido")
        start, end = seg.get("start"), seg.get("end")
        if (type(start) not in (int, float) or type(end) not in (int, float)
            or not math.isfinite(start) or not math.isfinite(end)
            or not 0 <= start < end <= duration + 0.05 or start < previous):
            raise ValueError("Timestamps invalidos")
        previous = end
        start, end = round(float(start), 3), round(min(float(end), duration), 3)
        if end <= start:
            raise ValueError("Timestamps colapsaram ao arredondar")
        original, translated = clean_text(seg.get("original")), clean_text(seg.get("pt_br"))
        clarity = seg.get("clarity")
        if clarity not in ("clear", "uncertain"):
            raise ValueError("Clareza invalida")
        review.append({"start": start, "end": end, "original": original,
                       "pt_br": translated, "clarity": clarity})
        if clarity == "uncertain" or not original or not translated:
            uncertain += 1
            continue
        # Prefira uma palavra animada por vez como na referencia dark.
        # Os tempos de cada palavra sao ESTIMATIVAS, jamais alinhamento fonetico.
        tokens = translated.split()
        span = end - start
        parts = tokens if tokens and all(len(t) <= 40 for t in tokens) and span / len(tokens) >= 0.16 else split_phrase(translated)
        if not parts:
            continue
        if span / len(parts) < 0.08:
            # Trechos curtos demais nao ganham legendas piscando ilegíveis.
            continue
        for i, part in enumerate(parts):
            a = round(start + span * i / len(parts), 3)
            b = round(end if i == len(parts)-1 else start + span * (i+1) / len(parts), 3)
            if b - a < 0.07:
                continue
            # Fonte/cor/posicao ficam a cargo de cada preset do Remotion.
            words.append({"text": part, "start": a, "end": b})
    if len(words) > 300:
        raise ValueError("Legendas demais")
    return {"words": words}, {
        "model": MODEL,
        "word_timing": "approximate_uniform_distribution_not_forced_alignment",
        "requires_human_review": True,
        "source_language": clean_text(raw.get("language", "unknown")),
        "segments": review,
        "discarded_uncertain": uncertain,
        "notice": "Tempos e traducao sao aproximados; divisoes por palavra sao estimativas, nao alinhamento fonetico. Revise antes de publicar.",
    }

def audio_source(directory):
    music = [directory / n for n in ("music.wav", "music.mp3", "music.m4a") if (directory / n).exists()]
    if len(music) > 1:
        raise ValueError("Somente um arquivo de musica")
    source = music[0] if music else directory / "artist.mp4"
    if not source.is_file() or source.is_symlink():
        raise ValueError("Audio/video ausente")
    return source

def extract_audio(source, duration, dest):
    done = subprocess.run([
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(source), "-vn", "-t", str(duration), "-ac", "1", "-ar",
        "16000", "-c:a", "pcm_s16le", str(dest),
    ], capture_output=True, timeout=60)
    if done.returncode or not dest.is_file() or dest.stat().st_size < 32000:
        raise ValueError("Audio ausente ou curto")
    if dest.stat().st_size > 2_000_000:
        raise ValueError("Audio excede limite")

def call_gemini(wav):
    """One remote Gemini interaction; API usage depends on user's key/tier."""
    from google import genai
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise ValueError("Configure GEMINI_API_KEY em Actions Secrets")
    client = genai.Client(api_key=key, http_options={"timeout": 120000, "retry_options": {"attempts": 1}})
    uploaded = None
    try:
        uploaded = client.files.upload(file=str(wav), config={"mime_type": "audio/wav"})
        interaction = client.interactions.create(
            model=MODEL,
            store=False,
            timeout=120,
            input=[
                {"type": "text", "text": PROMPT},
                {"type": "audio", "uri": uploaded.uri, "mime_type": uploaded.mime_type},
            ],
            response_format={"type": "text", "mime_type": "application/json", "schema": SCHEMA},
        )
        if not interaction.output_text:
            raise ValueError("Resposta Gemini vazia")
        return interaction.output_text
    finally:
        if uploaded is not None:
            try:
                client.files.delete(name=uploaded.name)
            except Exception:
                # Excluir no servidor e uma tentativa; a retencao do provedor se aplica.
                print("Aviso: limpeza do audio no provedor nao confirmada; consulte a politica de retencao.", file=sys.stderr)

def safe_error(error):
    code = getattr(error, "code", getattr(error, "status_code", None))
    return {401: "Chave nova rejeitada: substitua GEMINI_API_KEY em Actions Secrets.",
            403: "Acesso negado: confira permissoes da nova chave e disponibilidade regional.",
            404: "Modelo/arquivo indisponivel para esta conta; consulte os modelos habilitados.",
            429: "Quota esgotada ou limite de requisicoes. Aguarde; nao houve repeticao automatica."}.get(code,
            "Nao foi possivel transcrever: confira audio, timestamps, acesso ao modelo e Secret GEMINI_API_KEY. Nenhuma letra foi inventada.")

def main():
    duration = float(os.environ.get("DURATION", "15"))
    if not math.isfinite(duration) or not 1 <= duration <= 30:
        raise ValueError("Duracao deve estar entre 1 e 30 segundos")
    directory = Path("public/input")
    # Ao selecionar explicitamente IA, sobrescreve lyrics.json APENAS no runner;
    # o ZIP original e o repositorio nao sao alterados.
    if not os.environ.get("GEMINI_API_KEY"):
        raise ValueError("Secret GEMINI_API_KEY ausente")
    source = audio_source(directory)
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "audio.wav"
        extract_audio(source, duration, wav)
        raw = call_gemini(wav)
    subtitles, review = transform_response(raw, duration)
    directory.mkdir(parents=True, exist_ok=True)
    Path("out").mkdir(parents=True, exist_ok=True)
    (directory / "lyrics.json").write_text(json.dumps(subtitles, ensure_ascii=False, indent=2), encoding="utf-8")
    Path("out/traducao-para-revisar.json").write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Gemini: {len(review['segments'])} trechos analisados, {len(subtitles['words'])} legendas; "
          f"{review['discarded_uncertain']} incertos ignorados. Revise antes de publicar.")

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Never show lyrics or upstream errors that could include API credentials.
        print("IA Gemini nao concluiu. " + safe_error(error), file=sys.stderr)
        sys.exit(2)
