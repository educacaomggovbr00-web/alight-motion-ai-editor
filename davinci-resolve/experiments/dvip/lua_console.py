"""Probe Resolve's documented Lua Console without altering licensing or media.

Screens are observed by OCR. Only a recognized Workspace > Console menu
and an explicit Lua prompt permit typing a fixed, read-only dofile command.
"""
import json
import time
from pathlib import Path
from internal_menu import labels, choose

SCRIPT_NAME = 'CodexLuaProbe.lua'

def command(script):
    """Only the diagnostic script in the expected installation directory."""
    expected = Path('/opt/resolve/Fusion/Scripts/Utility') / SCRIPT_NAME
    if Path(script) != expected:
        raise ValueError('Unexpected Lua diagnostic script path')
    return 'dofile("' + str(expected) + '")'

def lua_prompt(rows):
    """OCR must identify a Lua prompt, not a generic language/menu label."""
    for item in rows:
        if item['key'] == 'lua' and 'lua' in item['text'].lower() and item['x'] < 250 and item['y'] > 100:
            return item
    return None

def invoke(output, env, run, script):
    result = {'attempted': False, 'consoleOpened': False, 'commandSubmitted': False, 'apiConnected': False}
    env = dict(env, OMP_THREAD_LIMIT='1', OMP_NUM_THREADS='1')
    try:
        cmd = command(script)
    except ValueError:
        result['reason'] = 'Caminho de script Lua inesperado; comando bloqueado.'
        return result
    if not Path(script).is_file():
        result['reason'] = 'Probe Lua não instalado.'
        return result

    def capture(tag):
        screenshot = output / ('lua-console-' + tag + '.png')
        enlarged = output / ('lua-console-ocr-' + tag + '.png')
        status, _ = run(['import', '-window', 'root', str(screenshot)], env, 12)
        if status['exitCode'] or status.get('timeLimitReached'):
            return []
        status, _ = run(['convert', str(screenshot), '-resize', '200%', str(enlarged)], env, 12)
        if status['exitCode'] or status.get('timeLimitReached'):
            return []
        status, data = run(['tesseract', str(enlarged), 'stdout', '--psm', '11', 'tsv'], env, 25,
                           output / ('lua-console-' + tag + '.log'))
        return labels(data, scale=2) if status['exitCode'] == 0 and not status.get('timeLimitReached') else []

    def action(argv):
        status, _ = run(argv, env, 8)
        return status['exitCode'] == 0 and not status.get('timeLimitReached')

    # Close any open Scripts submenu before navigating anew.
    action(['xdotool', 'key', 'Escape'])
    action(['xdotool', 'key', 'Escape'])
    workspace = choose(capture('desktop'), 'workspace', top_only=True)
    if workspace is None:
        result['reason'] = 'Workspace não reconhecido; nenhuma entrada digitada.'
        return result
    result['attempted'] = True
    if not action(['xdotool', 'mousemove', '--sync', str(workspace['x']), str(workspace['y']), 'click', '1']):
        result['reason'] = 'Falha ao abrir Workspace.'
        return result
    time.sleep(1)
    console = choose(capture('workspace'), 'console')
    if console is None:
        result['reason'] = 'Console não encontrado no menu Workspace.'
        action(['xdotool', 'key', 'Escape'])
        return result
    if not action(['xdotool', 'mousemove', '--sync', str(console['x']), str(console['y']), 'click', '1']):
        result['reason'] = 'Falha ao abrir Console.'
        return result
    result['consoleOpened'] = True
    time.sleep(2)
    prompt = lua_prompt(capture('prompt'))
    if prompt is None:
        result['reason'] = 'Prompt Lua não reconhecido; nenhum comando executado.'
        return result
    if not action(['xdotool', 'mousemove', '--sync', str(prompt['x'] + 65), str(prompt['y']), 'click', '1']):
        result['reason'] = 'Não foi possível focar o prompt Lua.'
        return result
    if not action(['xdotool', 'type', '--clearmodifiers', '--delay', '10', '--', cmd]):
        result['reason'] = 'Falha ao inserir comando de diagnóstico.'
        return result
    if not action(['xdotool', 'key', 'Return']):
        result['reason'] = 'Falha ao enviar comando de diagnóstico.'
        return result
    result['commandSubmitted'] = True
    probe = output / 'render' / 'lua-console-result.json'
    for _ in range(10):
        if probe.is_file():
            try:
                data = json.loads(probe.read_text())
                result['apiConnected'] = data.get('apiConnected') is True
                result['version'] = data.get('version')
                result['product'] = data.get('product')
                result['reason'] = 'Probe Lua respondeu; render não foi testado.'
                return result
            except (OSError, ValueError):
                break
        time.sleep(1)
    result['reason'] = 'Comando enviado, mas probe Lua não retornou arquivo.'
    return result
