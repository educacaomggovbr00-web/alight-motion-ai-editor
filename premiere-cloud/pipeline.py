"""Auxiliares locais; nunca edita/exporta por outro motor em lugar do Premiere."""
import argparse
from array import array
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import subprocess
import sys

STYLES = ('Anime Shake', 'Velocity Edit', 'AMV Cinematic', 'Glitch Edit',
          'Hard Beat Sync', 'Smooth Zoom', 'Extreme Impact')
STATES = ('nao_iniciado', 'bloqueado', 'experimental', 'testado', 'comprovadamente_funcional')

def command(args, timeout=90):
    # Não publica stderr: ferramentas podem revelar caminhos privados.
    result = subprocess.run(args, capture_output=True, timeout=timeout)
    if result.returncode:
        raise ValueError('Ferramenta auxiliar falhou; consulte o diagnóstico local privado')
    return result.stdout

def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

def job_id(value):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', value):
        raise ValueError('ID inválido: use até 64 letras, números, _ ou -')
    return value

def job_dir(root, identifier):
    root = Path(root).resolve()
    candidate = root / job_id(identifier)
    if candidate.is_symlink() or candidate.resolve().parent != root:
        raise ValueError('Diretório da tarefa fora da área privada')
    return candidate

def prepare(root, identifier, style, intensity, fps, orientation):
    if style not in STYLES or intensity not in ('leve', 'medio', 'forte'):
        raise ValueError('Estilo ou intensidade inválidos')
    if fps not in (30, 60) or orientation not in ('vertical', 'horizontal'):
        raise ValueError('Formato inválido')
    dest = job_dir(root, identifier)
    # Impede reexecuções de sobrescrever uma tarefa em andamento.
    dest.mkdir(parents=True, exist_ok=False)
    for folder in ('input', 'projects', 'output', 'reports'):
        (dest / folder).mkdir()
    width, height = (1080, 1920) if orientation == 'vertical' else (1920, 1080)
    job = dict(schema_version=1, job_id=identifier, engine='adobe-premiere-pro',
               style=style, intensity=intensity, preset_state='nao_iniciado',
               export=dict(width=width, height=height, fps=fps, video_codec='h264', audio_codec='aac'))
    write_json(dest / 'job.json', job)
    write_json(dest / 'reports/status.json', dict(state='bloqueado',
               reason='Aguardando mídia privada e operação/adapter validado do Premiere',
               tests={str(i): 'nao_iniciado' for i in range(1, 6)}))
    return job

def impacts(audio, seconds=30):
    if not 1 <= seconds <= 300:
        raise ValueError('Duração fora de 1–300 segundos')
    data = command(['ffmpeg', '-v', 'error', '-i', str(audio), '-t', str(seconds),
                    '-vn', '-ac', '1', '-ar', '11025', '-f', 's16le', 'pipe:1'])
    samples = array('h')
    samples.frombytes(data[:len(data) // 2 * 2])
    if sys.byteorder != 'little':
        samples.byteswap()
    hop, rate = 220, 11025
    energies = [math.sqrt(sum(x*x for x in samples[i:i+hop])/hop)
                for i in range(0, len(samples)-hop+1, hop)]
    events = []
    for i in range(1, len(energies)-1):
        baseline = statistics.median(energies[max(0, i-25):i+1])
        if energies[i] > max(250, baseline*1.8) and energies[i] > energies[i-1] and energies[i] >= energies[i+1]:
            timestamp = i*hop/rate
            if not events or timestamp-events[-1]['time_seconds'] >= .25:
                events.append(dict(time_seconds=round(timestamp, 5),
                                   strength=round(min(1, energies[i]/32768), 5), kind='impact_candidate'))
    return dict(schema_version=1, state='experimental', algorithm='local_rms_peak',
                timing_resolution_seconds=hop/rate, events=events,
                limitation='Picos de energia aproximados; não garantem batidas musicais nem BPM')

def validate_export(path, settings):
    data = json.loads(command(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))
    videos = [s for s in data.get('streams', []) if s.get('codec_type') == 'video']
    audios = [s for s in data.get('streams', []) if s.get('codec_type') == 'audio']
    if len(videos) != 1 or len(audios) != 1:
        raise ValueError('Exija uma faixa de vídeo e uma de áudio')
    v, a = videos[0], audios[0]
    fps = float(Fraction(v.get('avg_frame_rate', '0/1')))
    duration = float(data.get('format', {}).get('duration', 0))
    if (v['codec_name'] != 'h264' or a['codec_name'] != 'aac'
            or (v['width'], v['height']) != (settings['width'], settings['height'])
            or abs(fps-settings['fps']) > .01 or not math.isfinite(duration) or duration <= 0):
        raise ValueError('Exportação não corresponde ao formato solicitado')
    if path.suffix.lower() != '.mp4' or 'mp4' not in data['format'].get('format_name', '').split(','):
        raise ValueError('Contêiner MP4 obrigatório')
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return dict(state='testado', scope='arquivo_mp4_apenas', width=v['width'], height=v['height'],
                fps=fps, duration_seconds=duration, video_codec='h264', audio_codec='aac',
                sha256=digest.hexdigest(), premiere_proven=False)

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='action', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--root', required=True)
    prep.add_argument('--id', required=True)
    prep.add_argument('--style', choices=STYLES, default=STYLES[0])
    prep.add_argument('--intensity', choices=('leve', 'medio', 'forte'), default='medio')
    prep.add_argument('--fps', type=int, choices=(30, 60), default=30)
    prep.add_argument('--orientation', choices=('vertical', 'horizontal'), default='vertical')
    analyze = sub.add_parser('analyze')
    analyze.add_argument('--audio', required=True)
    analyze.add_argument('--seconds', type=int, default=30)
    analyze.add_argument('--output', required=True)
    validate = sub.add_parser('validate')
    validate.add_argument('--job', required=True)
    validate.add_argument('--video', required=True)
    validate.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        if args.action == 'prepare':
            prepare(args.root, args.id, args.style, args.intensity, args.fps, args.orientation)
        elif args.action == 'analyze':
            write_json(args.output, impacts(Path(args.audio), args.seconds))
        else:
            settings = json.loads(Path(args.job).read_text(encoding='utf-8'))['export']
            write_json(args.output, validate_export(Path(args.video), settings))
        print('Etapa auxiliar concluída; isso não comprova execução do Premiere.')
    except (ValueError, OSError, subprocess.TimeoutExpired, KeyError, ZeroDivisionError) as error:
        print('Etapa bloqueada: ' + type(error).__name__, file=sys.stderr)
        return 2
    return 0

if __name__ == '__main__':
    sys.exit(main())
