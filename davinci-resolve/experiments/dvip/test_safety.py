import io, json, os, tempfile, unittest, urllib.parse, zipfile
from pathlib import Path
from unittest.mock import patch
import source, supervise, edit_smoke, lua_console

class SourceTests(unittest.TestCase):
    def test_official_expiration(self):
        url='https://sw.blackmagicdesign.com'+source.URL_PATH+'?Expires=100'
        with self.assertRaises(source.Blocked):source.validate_url(url,now=101)
        self.assertEqual(source.validate_url(url,now=99),url)
    def test_host_credentials_path_and_scheme(self):
        for url in ['http://sw.blackmagicdesign.com'+source.URL_PATH,
                    'https://sw.blackmagicdesign.com.evil.invalid'+source.URL_PATH,
                    'https://user:password@sw.blackmagicdesign.com'+source.URL_PATH,
                    'https://sw.blackmagicdesign.com/other.zip',
                    'https://127.0.0.1'+source.URL_PATH]:
            with self.subTest(url=url),self.assertRaises(source.Blocked):source.validate_url(url)
    def test_invalid_url_does_not_leak(self):
        with self.assertRaises(source.Blocked) as ctx:source.validate_url('https://evil.invalid/x?token=FAKE_TEST_ONLY')
        self.assertNotIn('FAKE_TEST_ONLY',str(ctx.exception))
    def test_verified_local_installer_reused_without_network(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/source.NAME;p.write_bytes(b'unit fixture, not an installer')
            with patch.object(source,'RUN_SHA256',source.digest(p)),patch.object(source.urllib.request,'build_opener',side_effect=AssertionError('Network forbidden')):
                _,r=source.download('https://sw.blackmagicdesign.com'+source.URL_PATH,Path(d))
            self.assertFalse(r['downloadRepeated'])
    def test_bad_existing_installer_never_executed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/source.NAME;p.write_bytes(b'bad fixture')
            with patch.object(source.subprocess,'Popen',side_effect=AssertionError('Execution forbidden')):
                with self.assertRaises(source.Blocked):source.extract(p,Path(d))

class EvidenceTests(unittest.TestCase):
    def test_real_provenance_fixture(self):
        p=Path(__file__).parent.parent/'resultado-sharing-corrigido.json'
        r=json.loads(p.read_text());probes=[x for x in r['patchOptIn1'].values() if 'backend' in x]
        self.assertEqual(len(probes),4)
        self.assertTrue(all(supervise.verified(x) for x in probes))
    def test_names_extension_and_context_alone_not_enough(self):
        for r in [None,[],{'devices':None},{'glSharingPassed':True,'devices':[]},
                  {'glSharingPassed':True,'devices':[{'glSharedContextCreated':True,'sharedBufferRoundTrip':{'passed':True,'valuesReadByOpenGL':[0,0,0,0]}}]}]:
            self.assertFalse(supervise.verified(r))
    def test_secrets_not_in_child_environment(self):
        e=supervise.clean_env({'PATH':'/usr/bin','DAVINCI_RESOLVE_LINUX_URL':'FAKE_TEST_ONLY','GITHUB_TOKEN':'FAKE','GEMINI_API_KEY':'FAKE','DISPLAY':':1'})
        self.assertEqual(e,{'PATH':'/usr/bin','DISPLAY':':1'})
    def test_log_url_redaction(self):
        s=supervise.sanitized('Error https://sw.blackmagicdesign.com/x?Signature=FAKE_TEST_ONLY token=FAKE_MORE')
        self.assertNotIn('FAKE_TEST_ONLY',s);self.assertNotIn('FAKE_MORE',s)
    def test_process_timeout_is_enforced(self):
        status,_=supervise.bounded(['python3','-c','import time; time.sleep(30)'],os.environ.copy(),.1)
        self.assertTrue(status['timeLimitReached']);self.assertNotEqual(status['exitCode'],0)
    def test_absent_api_never_claims_export(self):
        r=edit_smoke.exercise(None,Path('/unused'),Path('/unused'))
        self.assertFalse(r['apiConnected']);self.assertFalse(r['exportProven'])
    def test_missing_mp4_does_not_invent_codec(self):
        class Project:
            def GetRenderFormats(self):return {'QuickTime':'mov'}
            def GetRenderCodecs(self,fmt):return {'Unsupported codec':'unsupported'}
        chosen,capabilities=edit_smoke.choose_render(Project())
        self.assertIsNone(chosen)
        self.assertEqual(capabilities['mp4Codecs'],{})
    def test_mov_fallback_only_when_dnxhr_announced(self):
        class Project:
            def GetRenderFormats(self):return {'QuickTime':'mov'}
            def GetRenderCodecs(self,fmt):return {'DNxHR LB':'real-announced-id'}
        chosen,_=edit_smoke.choose_render(Project())
        self.assertEqual(chosen,('mov','real-announced-id'))
if __name__=='__main__':unittest.main()

class OnboardingSafety(unittest.TestCase):
    def test_license_and_login_never_clicked(self):
        from supervise import onboarding_button
        for text in ["What's new in DaVinci Resolve Continue license agreement", "Welcome DaVinci Resolve skip sign in", "Welcome DaVinci Resolve skip activation"]:
            self.assertIsNone(onboarding_button(text))
    def test_unrecognized_dialog_not_clicked(self):
        from supervise import onboarding_button
        self.assertIsNone(onboarding_button('Error Continue'))

class VerifiedSetupScreen(unittest.TestCase):
    def test_only_known_setup_skip(self):
        from supervise import onboarding_button
        text="GREAT, YOU'RE ALMOST THERE! Before jumping straight into a project let's make sure you're all set up. SKIP AND START RIGHT NOW"
        self.assertEqual(onboarding_button(text),'skip')
        self.assertIsNone(onboarding_button(text+' license agreement'))

class MenuSafety(unittest.TestCase):
    def test_only_own_script_can_be_selected(self):
        from internal_menu import choose
        rows=[{'key':'codexsyntheticsmoke2','text':'other','x':0,'y':10}]
        self.assertIsNone(choose(rows,'codexsyntheticsmoke'))
    def test_workspace_must_be_on_top_menu(self):
        from internal_menu import choose
        rows=[{'key':'workspace','text':'Workspace','x':300,'y':200}]
        self.assertIsNone(choose(rows,'workspace',top_only=True))

class LuaConsoleSafety(unittest.TestCase):
    SCRIPT='/opt/resolve/Fusion/Scripts/Utility/CodexLuaProbe.lua'

    def test_command_is_pinned_to_diagnostic_file(self):
        self.assertEqual(lua_console.command(self.SCRIPT), 'dofile("'+self.SCRIPT+'")')
        for path in ['/tmp/arbitrary.lua', self.SCRIPT+'; os.execute("x")']:
            with self.assertRaises(ValueError):lua_console.command(path)

    def test_only_a_spatially_plausible_lua_prompt_is_accepted(self):
        self.assertIsNone(lua_console.lua_prompt([{'key':'lua','text':'Lua','x':500,'y':20}]))
        self.assertIsNone(lua_console.lua_prompt([{'key':'console','text':'Console','x':20,'y':500}]))
        self.assertIsNotNone(lua_console.lua_prompt([{'key':'lua','text':'Lua>','x':35,'y':640}]))

    def test_right_docked_lua_prompt_is_valid_but_toolbar_label_is_not(self):
        self.assertIsNone(lua_console.lua_prompt([
            {'key':'lua', 'text':'Lua', 'x':750, 'y':80},
            {'key':'lua', 'text':'Lua for beginners', 'x':550, 'y':640},
            {'key':'python', 'text':'Python>', 'x':550, 'y':640},
        ]))
        self.assertEqual(lua_console.lua_prompt([
            {'key':'lua', 'text':'Lua>', 'x':45, 'y':230},
            {'key':'lua', 'text':'Lua >', 'x':630, 'y':680},
        ])['x'],630)

    def test_reconstruct_separated_lua_prompt_with_weak_symbol_confidence(self):
        def word(number, label, confidence, x, y, width):
            return '\t'.join([
                '5','1','1','1','1',str(number),str(x),str(y),
                str(width),'36',str(confidence),label])
        sample = '\n'.join([
            word(1,'Lua',91,1120,1312,60),
            word(2,'>',9,1186,1313,24)])
        rows=lua_console.prompt_rows_from_tsv(sample,scale=2)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['key'],'lua')
        self.assertGreater(rows[0]['x'],250)
        self.assertIsNotNone(lua_console.lua_prompt(rows))
        # A tab title, ordinary Lua text or a visually unrelated '>' must
        # never trigger xdotool typing.
        invalid='\n'.join([
            word(1,'Lua',88,1120,1312,60),
            word(2,'script',94,1186,1313,70)])
        self.assertEqual(lua_console.prompt_rows_from_tsv(invalid),[])
        distant='\n'.join([
            word(1,'Lua',88,1120,1312,60),
            word(2,'>',20,2200,1313,24)])
        self.assertEqual(lua_console.prompt_rows_from_tsv(distant),[])

    def test_right_docked_prompt_allows_only_allowlisted_probe_command(self):
        calls=[]
        def runner(argv,env,seconds,output=None):
            calls.append(argv)
            return {'exitCode':0,'timeLimitReached':False},''
        workspace=[{'key':'workspace','text':'Workspace','x':635,'y':11}]
        console=[{'key':'console','text':'Console','x':670,'y':180}]
        prompt=[{'key':'lua','text':'Lua >','x':640,'y':680}]
        with tempfile.TemporaryDirectory() as tmp:
            with (patch.object(lua_console.Path,'is_file',return_value=True),
                  patch.object(lua_console,'labels',side_effect=[workspace,console,prompt]),
                  patch.object(lua_console.time,'sleep')):
                result=lua_console.invoke(Path(tmp),{},runner,self.SCRIPT)
        self.assertTrue(result['consoleOpened'])
        self.assertTrue(result['commandSubmitted'])
        self.assertEqual(sum(cmd[:2]==['xdotool','type'] for cmd in calls),1)
        self.assertEqual(result['promptDetection'][0]['selectedX'],640)
        self.assertEqual(result['promptDetection'][0]['explicitLuaPrompt'],True)
        self.assertFalse(result['apiConnected'])

    def test_missing_lua_prompt_never_types_or_executes(self):
        calls=[]
        def runner(argv, env, seconds, output=None):
            calls.append(argv)
            return {'exitCode':0,'timeLimitReached':False}, ''
        workspace=[{'key':'workspace','text':'Workspace','x':600,'y':11}]
        console=[{'key':'console','text':'Console','x':640,'y':250}]
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(lua_console.Path,'is_file',return_value=True), \
                 patch.object(lua_console,'labels',side_effect=[workspace,console,[]]), \
                 patch.object(lua_console.time,'sleep'):
                result=lua_console.invoke(Path(tmp),{},runner,self.SCRIPT)
        self.assertTrue(result['consoleOpened'])
        self.assertFalse(result['commandSubmitted'])
        self.assertFalse(any('type' in argv for argv in calls))

    def test_unrecognized_workspace_never_types(self):
        calls=[]
        def runner(argv, env, seconds, output=None):
            calls.append(argv)
            return {'exitCode':0,'timeLimitReached':False}, ''
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(lua_console.Path,'is_file',return_value=True), \
                 patch.object(lua_console,'labels',return_value=[]):
                result=lua_console.invoke(Path(tmp),{},runner,self.SCRIPT)
        self.assertFalse(result['attempted'])
        self.assertFalse(any('type' in argv for argv in calls))


class LuaNativeEditSafety(unittest.TestCase):
    PROBE='/opt/resolve/Fusion/Scripts/Utility/CodexLuaProbe.lua'
    EDIT='/opt/resolve/Fusion/Scripts/Utility/CodexLuaEditSmoke.lua'

    def test_only_allowlisted_internal_lua_file_can_run(self):
        self.assertEqual(lua_console.command(self.EDIT), 'dofile("'+self.EDIT+'")')
        for path in ['/tmp/CodexLuaEditSmoke.lua', self.EDIT+'; os.execute("x")',
                     '/opt/resolve/Fusion/Scripts/Utility/Other.lua']:
            with self.assertRaises(ValueError):lua_console.command(path)

    def test_native_edit_never_types_without_second_visible_prompt(self):
        from internal_menu import normalized
        rows=[
            [{'key': 'workspace', 'text': 'Workspace', 'x': 635, 'y': 11}],
            [{'key': 'console', 'text': 'Console', 'x': 670, 'y': 180}],
            [{'key': 'lua', 'text': 'Lua>', 'x': 45, 'y': 610}],
            []]
        calls=[]
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'render').mkdir()
            (root/'render'/'lua-console-result.json').write_text('{"apiConnected":true}')
            def runner(argv, env, seconds, output=None):
                calls.append(argv)
                return {'exitCode':0,'timeLimitReached':False}, ''
            with patch.object(lua_console.Path,'is_file',return_value=True), \
                 patch.object(lua_console,'labels',side_effect=rows), \
                 patch.object(lua_console.time,'sleep'):
                report=lua_console.invoke(root,{},runner,self.PROBE,self.EDIT)
            self.assertTrue(report['apiConnected'])
            self.assertFalse(report['nativeEdit']['submitted'])
            self.assertEqual(sum(a[:2]==['xdotool','type'] for a in calls),1)

    def test_second_lua_command_when_probe_and_prompt_pass(self):
        rows=[
            [{'key': 'workspace', 'text': 'Workspace', 'x': 635, 'y': 11}],
            [{'key': 'console', 'text': 'Console', 'x': 670, 'y': 180}],
            [{'key': 'lua', 'text': 'Lua>', 'x': 45, 'y': 610}],
            [{'key': 'lua', 'text': 'Lua>', 'x': 45, 'y': 610}]]
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);render=root/'render';render.mkdir()
            (render/'lua-console-result.json').write_text('{"apiConnected":true}')
            calls=[]
            def runner(argv, env, seconds, output=None):
                calls.append(argv)
                if len(argv)>=2 and argv[:2]==['xdotool','type'] and any(self.EDIT in arg for arg in argv):
                    (render/'sdk-result.json').write_text('{"invocationContext":"internal-lua-console","nativeRenderProven":false}')
                return {'exitCode':0,'timeLimitReached':False}, ''
            with patch.object(lua_console.Path,'is_file',return_value=True), \
                 patch.object(lua_console,'labels',side_effect=rows), \
                 patch.object(lua_console.time,'sleep'):
                report=lua_console.invoke(root,{},runner,self.PROBE,self.EDIT)
            self.assertTrue(report['nativeEdit']['submitted'])
            self.assertTrue(report['nativeEdit']['resultObserved'])
            self.assertEqual(sum(a[:2]==['xdotool','type'] for a in calls),2)
            self.assertNotIn('nativeRenderProven',report)

    def test_private_input_cannot_request_lua_experiment(self):
        import subprocess, sys
        script=Path(supervise.__file__)
        p=subprocess.run([sys.executable,str(script),'--resolve-root','/does-not-exist',
                          '--output','/tmp/not-used','--backend','glx',
                          '--input-video','/tmp/private.mov','--lua-native-edit'],
                         capture_output=True,text=True,timeout=8)
        self.assertEqual(p.returncode,2)
        self.assertIn('apenas com mídia sintética',p.stderr)

class LuaFileTransportSafety(unittest.TestCase):
    def test_report_writer_is_file_api_not_table_serialization(self):
        root=Path(__file__).parent
        for name in ['lua_probe.lua','lua_edit_smoke.lua']:
            source=(root/name).read_text()
            self.assertIn('bmd.writefile(',source)
            self.assertNotIn('bmd.writestring(',source.split('-- writestring(table)')[0] if name == 'lua_probe.lua' else source.split('-- The Fusion writestring()')[0])

