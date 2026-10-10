#!/usr/bin/env python3
"""Editor MP4 para GitHub Actions com impactos estimados pelo áudio.

Requer FFmpeg e FFprobe. Não modifica projetos internos do Alight Motion.
"""

import argparse
from array import array
import json
import math
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import tempfile
from urllib.parse import urlparse
from urllib.request import Request, urlopen

MAX_DOWNLOAD_BYTES = 250 * 1024 * 1024


def run_capture(cmd):
    return subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def download_https(url, dest):
    if urlparse(url).scheme != "https":
        raise ValueError("O link do vídeo precisa começar com https://")
    request = Request(url, headers={"User-Agent": "alight-motion-ai-editor/0.1"})
    with urlopen(request, timeout=30) as response, dest.open("wb") as output:
        if urlparse(response.geturl()).scheme != "https":
            raise ValueError("O link redirecionou para uma conexão não segura")
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_DOWNLOAD_BYTES:
            raise ValueError("Vídeo muito grande (limite de 250 MiB)")
        copied = 0
        while chunk := response.read(1024 * 1024):
            copied += len(chunk)
            if copied > MAX_DOWNLOAD_BYTES:
                raise ValueError("Vídeo muito grande (limite de 250 MiB)")
            output.write(chunk)


def probe(path):
    raw = run_capture(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)])
    info = json.loads(raw.stdout)
    video = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), None)
    audio = next((s for s in info.get("streams", []) if s.get("codec_type") == "audio"), None)
    if not video:
        raise ValueError("O arquivo não possui vídeo")
    duration = float(info.get("format", {}).get("duration") or video.get("duration") or 0)
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Não foi possível identificar a duração")
    return duration, bool(audio)


def find_impacts(video_path, seconds, has_audio):
    """Estimativa por picos locais de energia, não detecção perfeita de batidas."""
    if not has_audio:
        return [], False
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(video_path),
           "-t", str(seconds), "-vn", "-ac", "1", "-ar", "11025", "-f", "s16le", "pipe:1"]
    samples_raw = run_capture(cmd).stdout
    values = array("h")
    values.frombytes(samples_raw[:len(samples_raw) - len(samples_raw) % 2])
    rate = 11025
    hop = 551
    energies = []
    for idx in range(0, len(values) - hop + 1, hop):
        block = values[idx:idx + hop]
        energies.append(math.sqrt(sum(x * x for x in block) / len(block)))
    if len(energies) < 15 or max(energies) < 100:
        return [], False
    median = statistics.median(energies)
    candidates = []
    for idx in range(5, len(energies) - 5):
        neighborhood = energies[max(0, idx - 7):min(len(energies), idx + 8)]
        baseline = statistics.mean(neighborhood)
        power = energies[idx]
        if (power >= max(energies[idx - 2:idx + 3])
                and power >= max(230, median * 1.20)
                and power >= baseline * 1.14):
            candidates.append((idx * hop / rate, power / (baseline + 1)))
    selected = []
    for timestamp, strength in sorted(candidates, key=lambda item: -item[1]):
        if all(abs(timestamp - old) >= 0.36 for old in selected):
            selected.append(timestamp)
        if len(selected) >= 30:
            break
    selected.sort()
    return selected, len(selected) >= 2


def filter_graph(beats, width, height, fps, level):
    amount = {"leve": 0.5, "medio": 1.0, "forte": 1.4}[level]
    pulses = [f"max(0\\,1-abs(on-{round(t * fps)})/5)" for t in beats]
    impulse = "+".join(pulses) if pulses else "0"
    zoom = f"min(1.18\\,1.025+{0.048 * amount:.4f}*({impulse}))"
    shake_x = f"iw/2-(iw/zoom/2)+{0.014 * amount:.4f}*iw*sin(on*2.7)*({impulse})"
    shake_y = f"ih/2-(ih/zoom/2)+{0.012 * amount:.4f}*ih*cos(on*2.1)*({impulse})"
    flashes = [f"max(0\\,1-abs(t-{t:.3f})/0.085)" for t in beats]
    flash = "+".join(flashes) if flashes else "0"
    brightness = f"min(0.23\\,{0.14 * amount:.4f}*({flash}))"
    return (f"[0:v]fps={fps},"
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},setsar=1,"
            f"zoompan=z='{zoom}':x='{shake_x}':y='{shake_y}':d=1:s={width}x{height}:fps={fps},"
            f"eq=brightness='{brightness}':eval=frame,format=yuv420p[v]")


def main():
    ap = argparse.ArgumentParser(description="Edita MP4 com zooms, flashes e shakes em impactos aproximados")
    ap.add_argument("video", nargs="?", default="input/video.mp4")
    ap.add_argument("--url", help="Link HTTPS direto para o MP4")
    ap.add_argument("--output", default="output/editado.mp4")
    ap.add_argument("--intensidade", choices=["leve", "medio", "forte"], default="medio")
    ap.add_argument("--max-segundos", type=int, default=30)
    ap.add_argument("--largura", type=int, default=720)
    ap.add_argument("--altura", type=int, default=1280)
    ap.add_argument("--fps", type=int, default=30)
    args = ap.parse_args()
    if args.max_segundos < 1 or args.max_segundos > 300 or args.fps < 1 or args.fps > 60:
        ap.error("Duração deve estar entre 1 e 300 segundos e FPS entre 1 e 60")
    if args.largura < 144 or args.altura < 144 or args.largura % 2 or args.altura % 2:
        ap.error("Largura e altura devem ser pares e pelo menos 144")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        ap.error("Instale ffmpeg e ffprobe para continuar")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="alight-editor-") as temp:
        video = Path(args.video)
        if args.url:
            video = Path(temp) / "video.mp4"
            print("Baixando vídeo HTTPS...", flush=True)
            download_https(args.url, video)
        if not video.is_file():
            ap.error(f"Vídeo não encontrado: {video} (adicione input/video.mp4 ou use --url)")
        duration, has_audio = probe(video)
        seconds = min(duration, args.max_segundos)
        impacts, detected = find_impacts(video, seconds, has_audio)
        if not detected:
            impacts = [round(x * 0.8 + 0.8, 2) for x in range(int(seconds / 0.8))
                       if x * 0.8 + 0.8 < seconds]
        graph = filter_graph(impacts, args.largura, args.altura, args.fps, args.intensidade)
        command = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(video),
                   "-t", str(seconds), "-filter_complex", graph, "-map", "[v]"]
        if has_audio:
            command += ["-map", "0:a:0", "-c:a", "aac", "-b:a", "160k"]
        command += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                    "-r", str(args.fps), "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    "-shortest", str(output)]
        print(f"Duração: {seconds:.1f}s | áudio: {has_audio} | marcas: {len(impacts)} "
              f"({'áudio' if detected else 'ritmo fixo'})", flush=True)
        subprocess.run(command, check=True)
        print(f"Vídeo editado: {output}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (subprocess.CalledProcessError, ValueError, OSError) as exc:
        print(f"Erro ao editar: {exc}", file=sys.stderr)
        sys.exit(1)
