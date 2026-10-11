#!/usr/bin/env python3
"""Start an existing original Resolve only after a verified GL/CL buffer test."""
import argparse
import hashlib
import json
import os
import signal
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sharing-report', required=True, type=Path)
    parser.add_argument('--resolve', required=True, type=Path)
    parser.add_argument('--debug-log', type=Path, default=Path('~/.local/share/DaVinciResolve/logs/ResolveDebug.txt').expanduser())
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--seconds', type=int, default=45)
    args = parser.parse_args()
    if not 5 <= args.seconds <= 90:
        parser.error('--seconds must be between 5 and 90.')
    args.output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    result = {'state': 'bloqueado', 'resolveStarted': False, 'editingProven': False, 'exportProven': False}
    child = None
    try:
        raw = args.sharing_report.read_bytes()
        report = json.loads(raw)
        verified = report.get('glSharingPassed') is True and any(
            d.get('glSharedContextCreated') is True
            and d.get('sharedBufferRoundTrip', {}).get('passed') is True
            for d in report.get('devices', [])
        )
        result['sharingReportSha256'] = hashlib.sha256(raw).hexdigest()
        if not verified:
            result['reason'] = 'GL/OpenCL sharing not verified by a real shared buffer. Resolve was not started.'
            return 2
        if not args.resolve.is_file() or not os.access(args.resolve, os.X_OK):
            result['reason'] = 'Original Resolve executable not accessible. This script does not download or install it.'
            return 2
        if not os.environ.get('DISPLAY'):
            result['reason'] = 'An X11 session is required for this Linux experiment.'
            return 2
        offset = args.debug_log.stat().st_size if args.debug_log.exists() else 0
        with (args.output_dir / 'resolve-private.log').open('wb') as log:
            child = subprocess.Popen([str(args.resolve.resolve())], stdout=log, stderr=log, start_new_session=True)
            result.update(resolveStarted=True, state='experimental', observedSeconds=args.seconds)
            try:
                result['exitCode'] = child.wait(timeout=args.seconds)
            except subprocess.TimeoutExpired:
                result['timeLimitReached'] = True
        if args.debug_log.exists():
            with args.debug_log.open('rb') as log:
                if args.debug_log.stat().st_size >= offset:
                    log.seek(offset)
                recent = log.read().decode(errors='replace')
            messages = [line.strip() for line in recent.splitlines() if 'DVIP Exception:' in line or 'Failed to initialize OpenCL board manager' in line]
            result['dvipErrors'] = messages
            if messages:
                result.update(state='bloqueado', reason='DVIP initialization failed; inspect the reported errors.')
                return 2
        result['reason'] = 'A process launch alone does not prove the editor UI, project creation or MP4 export. Review the interactive session.'
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result['reason'] = f'{type(exc).__name__}: {exc}'
        return 2
    finally:
        if child is not None:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait(timeout=5)
        encoded = json.dumps(result, indent=2)
        (args.output_dir / 'result.json').write_text(encoded + '\n')
        print(encoded)


if __name__ == '__main__':
    raise SystemExit(main())
