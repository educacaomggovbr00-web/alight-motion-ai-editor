"""Probe Resolve's documented Lua Console without altering licensing or media.

Screens are observed by OCR. Only a recognized Workspace > Console menu
and an explicit Lua prompt permit typing a fixed, read-only dofile command.
"""
import json
import time
from pathlib import Path
from internal_menu import labels, choose

SCRIPT_NAME = 'CodexLuaProbe.lua'
EDIT_SCRIPT_NAME = 'CodexLuaEditSmoke.lua'

def command(script):
    """Only an explicitly allowlisted Lua file can be executed."""
    expected_dir = Path('/opt/resolve/Fusion/Scripts/Utility')
    if Path(script).name not in (SCRIPT_NAME, EDIT_SCRIPT_NAME):
        raise ValueError('Not an approved script')
    expected = expected_dir / Path(script).name
    if Path(script) != expected:
        raise ValueError('Unexpected Lua diagnostic script path')
    return 'dofile("' + str(expected) + '")'

def lua_prompt(rows):
    """OCR must identify a Lua prompt, not a generic language/menu label."""
    for item in rows:
        if item['key'] == 'lua' and '>' in item['text'] and item['x'] < 250 and item['y'] > 100:
            return item
    return None

def invoke(output, env, run, script, native_edit_script=None):
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
                if native_edit_script is not None:
                    edit = {'requested': True, 'submitted': False, 'resultObserved': False}
                    result['nativeEdit'] = edit
                    if not result['apiConnected']:
                        edit['reason'] = 'API Lua ainda sem conexão.'
                    elif Path(native_edit_script).name != EDIT_SCRIPT_NAME or not Path(native_edit_script).is_file():
                        edit['reason'] = 'Arquivo Lua de edição não permitido ou ausente.'
                    else:
                        # The read-only probe returned before submitting any editing command.
                        # Re-check a visible Lua prompt: a stale console is NOT enough.
                        edit_prompt = lua_prompt(capture('edit-prompt'))
                        if edit_prompt is None:
                            edit['reason'] = 'Prompt Lua de edição não reconhecido.'
                        elif not action(['xdotool', 'mousemove', '--sync', str(edit_prompt['x'] + 65), str(edit_prompt['y']), 'click', '1']):
                            edit['reason'] = 'Campo do Console não pôde receber foco.'
                        elif not action(['xdotool', 'type', '--clearmodifiers', '--delay', '10', '--', command(native_edit_script)]):
                            edit['reason'] = 'Comando de edição não digitado.'
                        elif not action(['xdotool', 'key', 'Return']):
                            edit['reason'] = 'Comando de edição não enviado.'
                        else:
                            edit['submitted'] = True
                            report = output / 'render' / 'sdk-result.json'
                            # The supervisor's whole container also has an independent timeout.
                            for _ in range(175):
                                if report.is_file():
                                    try:
                                        edit['resultObserved'] = json.loads(report.read_text()).get('invocationContext') == 'internal-lua-console'
                                    except (OSError, ValueError):
                                        edit['reason'] = 'Relatório Lua inválido.'
                                    break
                                time.sleep(1)
                            if not edit['resultObserved'] and not edit.get('reason'):
                                edit['reason'] = 'Execução Lua não concluiu no prazo.'
                return result
            except (OSError, ValueError):
                break
        time.sleep(1)
    result['reason'] = 'Comando enviado, mas probe Lua não retornou arquivo.'
    return result
