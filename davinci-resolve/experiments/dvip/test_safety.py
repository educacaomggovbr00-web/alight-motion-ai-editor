import io, json, os, tempfile, unittest, urllib.parse, zipfile
from pathlib import Path
from unittest.mock import patch
import source, supervise, edit_smoke

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
