#!/usr/bin/env python3
"""Primeiro pipeline real MLT/Kdenlive para edits dark de artistas.

Renderiza o projeto .mlt com melt (MLT), sem abrir interface gráfica.
Usa FFmpeg apenas para preparar o vídeo e remuxar a música.
Esta versão faz P&B, flashes e cortes por impacto. Não promete velocity/blur ainda.
"""
import argparse
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

# Reusa funções do editor existente para download limitado e análise aproximada.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from editor import download_https, probe, find_impacts


def command(args, *, cwd=None):
    print("Executando:", Path(args[0]).name, " ".join(str(x) for x in args[1:5]), flush=True)
    subprocess.run(args, check=True, cwd=cwd)


def property_(parent, name, value):
    p = ET.SubElement(parent, "property", {"name": name})
    p.text = str(value)
    return p


def beats_for_video(src, duration, has_audio, bpm_interval):
    beats, detected = find_impacts(src, duration, has_audio)
    if not detected:
        beats = [round(x, 2) for x in
                 (bpm_interval * i for i in range(1, math.ceil(duration / bpm_interval)))
                 if x < duration - 0.12]
    return beats, "picos estimados do audio" if detected else "ritmo fixo (fallback)"


def segments(frame_count, fps, beats):
    """Intervalos adjacentes com flash em torno de cada batida."""
    impact_frames = set()
    for t in beats:
        pos = round(t * fps)
        for fr in range(max(0, pos - 2), min(frame_count, pos + 4)):
            impact_frames.add(fr)
    if not impact_frames:
        return [(0, frame_count - 1, False)]
    runs = []
    start = 0
    current = 0 in impact_frames
    for fr in range(1, frame_count):
        active = fr in impact_frames
        if active != current:
            runs.append((start, fr - 1, current))
            start, current = fr, active
    runs.append((start, frame_count - 1, current))
    return runs


def build_mlt(project, rel_media, width, height, fps, frames, runs, intensity):
    """MLT XML com produtores por trecho e playlist sem lacunas."""
    mlt = ET.Element("mlt", {
        "LC_NUMERIC": "C", "producer": "timeline",
        "title": "Dark Emo Rap - MLT"
    })
    ET.SubElement(mlt, "profile", {
        "description": "Vertical dark edit",
        "width": str(width), "height": str(height),
        "progressive": "1", "sample_aspect_num": "1", "sample_aspect_den": "1",
        "display_aspect_num": "9", "display_aspect_den": "16",
        "frame_rate_num": str(fps), "frame_rate_den": "1",
        "colorspace": "709"
    })

    flash_levels = {"leve": "1.25", "medio": "1.70", "forte": "2.35"}
    for i, (begin, end, is_flash) in enumerate(runs):
        prod = ET.SubElement(mlt, "producer", {
            "id": f"p{i}", "in": str(begin), "out": str(end)
        })
        property_(prod, "mlt_service", "avformat")
        property_(prod, "resource", rel_media)
        property_(prod, "audio_index", "-1")
        bw = ET.SubElement(prod, "filter")
        property_(bw, "mlt_service", "greyscale")
        if is_flash:
            bright = ET.SubElement(prod, "filter")
            property_(bright, "mlt_service", "brightness")
            property_(bright, "level", flash_levels[intensity])

    playlist = ET.SubElement(mlt, "playlist", {"id": "timeline"})
    for i, (begin, end, _) in enumerate(runs):
        ET.SubElement(playlist, "entry", {
            "producer": f"p{i}", "in": str(begin), "out": str(end)
        })

    ET.indent(mlt, space="  ")
    ET.ElementTree(mlt).write(project, encoding="utf-8", xml_declaration=True)
    return sum(1 for _, _, impact in runs if impact)


def main():
    ap = argparse.ArgumentParser(description="Edit dark de artista com projeto MLT + FFmpeg auxiliar")
    ap.add_argument("video", nargs="?", default="input/video.mp4")
    ap.add_argument("--url", help="HTTPS direto para MP4 (maximo 250 MiB)")
    ap.add_argument("--output-dir", default="output/mlt-dark")
    ap.add_argument("--intensidade", choices=("leve", "medio", "forte"), default="medio")
    ap.add_argument("--largura", type=int, default=540)
    ap.add_argument("--altura", type=int, default=960)
    ap.add_argument("--fps", type=int, choices=(24, 30, 60), default=30)
    ap.add_argument("--max-segundos", type=int, default=25)
    ap.add_argument("--intervalo-batida", type=float, default=0.75)
    args = ap.parse_args()

    if args.largura < 144 or args.altura < 144 or args.largura % 2 or args.altura % 2:
        ap.error("Resolucao precisa ser par e >= 144 em ambas as dimensoes")
    if args.max_segundos < 1 or args.max_segundos > 60:
        ap.error("Limite de 1 a 60 segundos por execucao")
    if not 0.3 <= args.intervalo_batida <= 2:
        ap.error("Intervalo fixo precisa ser entre 0.3 e 2.0 s")

    for name in ("ffmpeg", "ffprobe", "melt"):
        if not shutil.which(name):
            ap.error(f"Dependencia nao instalada: {name}")

    out = Path(args.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    assets = out / "assets"
    assets.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="dark-mlt-") as temporary:
        source = Path(args.video).resolve()
        if args.url:
            source = Path(temporary) / "video.mp4"
            print("Baixando MP4 por HTTPS com limite de tamanho...", flush=True)
            download_https(args.url, source)
        if not source.is_file():
            ap.error("Video nao encontrado. Envie input/video.mp4 ou informe --url.")

        duration, has_audio = probe(source)
        limit = min(duration, float(args.max_segundos))
        frames = math.floor(limit * args.fps)
        if frames < args.fps:
            ap.error("Video muito curto para este preset (minimo 1 segundo)")
        seconds = frames / args.fps

        beats, method = beats_for_video(source, seconds, has_audio, args.intervalo_batida)
        print(f"Duracao {seconds:.2f}s | batidas {len(beats)} | metodo {method}", flush=True)

        normalized = assets / "preparado.mp4"
        # Video temporario sem audio, com dimensoes e FPS constantes para o MLT.
        filter_str = (f"scale={args.largura}:{args.altura}:force_original_aspect_ratio=increase,"
                      f"crop={args.largura}:{args.altura},setsar=1,"
                      f"fps={args.fps},format=yuv420p")
        command([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(source), "-t", str(seconds), "-an",
            "-vf", filter_str, "-frames:v", str(frames),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
            str(normalized)
        ])

        runs = segments(frames, args.fps, beats)
        project = out / "projeto.mlt"
        flashes = build_mlt(
            project, "assets/preparado.mp4", args.largura, args.altura,
            args.fps, frames, runs, args.intensidade
        )
        print(f"Projeto MLT gerado: {len(runs)} cortes e {flashes} intervalos de flash", flush=True)

        stage = out / "video_mlt.mp4"
        # O efeito P&B e flashes sao executados no motor MLT (melt).
        command([
            "melt", "-progress2", "projeto.mlt",
            "-consumer", "avformat:video_mlt.mp4",
            "real_time=-1", "vcodec=libx264", "acodec=none",
            "crf=22", "preset=veryfast", "pix_fmt=yuv420p",
            "movflags=+faststart", "threads=2"
        ], cwd=out)

        final = out / "editado.mp4"
        if has_audio:
            # Música original preservada do arquivo de entrada.
            command([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(stage), "-i", str(source),
                "-map", "0:v:0", "-map", "1:a:0",
                "-t", str(seconds), "-c:v", "copy",
                "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
                str(final)
            ])
        else:
            command([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(stage), "-map", "0:v:0", "-an",
                "-c:v", "copy", "-movflags", "+faststart", str(final)
            ])
        if not final.is_file() or final.stat().st_size < 1000:
            raise RuntimeError("MLT nao gerou MP4 valido")
        manifest = {
            "editor": "Kdenlive / MLT (renderizado com melt)",
            "preset": "Dark Emo Rap P&B + flashes",
            "intensidade": args.intensidade,
            "duracao_s": seconds,
            "fps": args.fps, "resolucao": [args.largura, args.altura],
            "batidas": beats, "metodo_batida": method,
            "intervalos_flash": flashes,
            "efeitos_comprovaveis": ["greyscale (MLT)", "brightness (MLT em flashes)", "cortes de timeline"],
            "efeitos_ainda_nao_implementados": ["shake", "velocity", "RGB split", "motion blur"],
            "observacao": "Análise musical é aproximação; fonte sem áudio usa batida fixa."
        }
        (out / "manifesto.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Edit pronto em: {final}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError, RuntimeError) as exc:
        sys.exit(f"Erro MLT: {exc}")
