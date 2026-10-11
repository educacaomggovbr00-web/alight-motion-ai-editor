"""Offline tests: no Gemini key, model call, or paid quota required."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

module_path = Path(__file__).resolve().parents[1] / "scripts/translate-gemini.py"
spec = importlib.util.spec_from_file_location("translate_gemini", module_path)
trans = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trans)

class GeminiSubtitleTests(unittest.TestCase):
    def test_transcription_translation_and_timestamps(self):
        raw = {"language":"en", "segments":[
            {"start":0.5, "end":1.5, "original":"I miss you",
             "pt_br":"Sinto saudade de você", "clarity":"clear"},
            {"start":2.1, "end":2.8, "original":"unclear", "pt_br":"talvez",
             "clarity":"uncertain"}]}
        lyrics, review = trans.transform_response(json.dumps(raw),4)
        self.assertEqual(
            [(w["text"], w["start"], w["end"]) for w in lyrics["words"]],
            [("Sinto", 0.5, 0.75), ("saudade", 0.75, 1.0),
             ("de", 1.0, 1.25), ("você", 1.25, 1.5)]
        )
        self.assertTrue(all("font" not in w and "color" not in w for w in lyrics["words"]))
        self.assertEqual(review["discarded_uncertain"],1)
        self.assertEqual(len(review["segments"]),2)

    def test_phrase_splitting_keeps_all_words(self):
        text = "Essa mensagem em português é grande demais para uma legenda na tela de uma só vez"
        raw = {"language":"en","segments":[{
            "start":0,"end":3.5,"original":"sample", "pt_br":text,"clarity":"clear"}]}
        lyrics,_=trans.transform_response(raw,4)
        self.assertGreater(len(lyrics["words"]),1)
        self.assertEqual(" ".join(w["text"] for w in lyrics["words"]),text)
        self.assertTrue(all(len(w["text"])<=40 for w in lyrics["words"]))
        self.assertEqual(lyrics["words"][-1]["end"],3.5)

    def test_short_segments_remain_readable(self):
        raw={"language":"en","segments":[{"start":0.5,"end":0.68,
            "original":"quick","pt_br":"muito rápido para dividir",
            "clarity":"clear"}]}
        lyrics,_=trans.transform_response(raw,4)
        self.assertEqual([w["text"] for w in lyrics["words"]],["muito rápido para dividir"])

    def test_no_audible_words_means_no_fabricated_subtitles(self):
        lyrics,review=trans.transform_response({"language":"unknown","segments":[]},15)
        self.assertEqual(lyrics,{"words":[]})
        self.assertEqual(review["segments"],[])

    def test_invalid_json_and_times_are_rejected(self):
        with self.assertRaises(ValueError):
            trans.transform_response({"segments":"not-list"},15)
        for item in [
            {"start":3,"end":20,"original":"a","pt_br":"b","clarity":"clear"},
            {"start":True,"end":1,"original":"a","pt_br":"b","clarity":"clear"},
            {"start":0,"end":1,"original":"a","pt_br":"b","clarity":"fake"},
        ]:
            with self.assertRaises(ValueError):
                trans.transform_response({"segments":[item]},4)

    def test_only_one_gemini_interaction_cleanup(self):
        calls={"sent":0,"deleted":False}
        uploaded=types.SimpleNamespace(uri="files/audio",mime_type="audio/wav",name="files/test")
        class Files:
            def upload(self, *, file, config):
                self.config=config
                return uploaded
            def delete(self, *, name):
                calls["deleted"]=(name==uploaded.name)
        class Interactions:
            def create(self, *, model, input, response_format, store, timeout):
                assert store is False and timeout == 120
                assert (model==trans.MODEL and input[1]["uri"]==uploaded.uri
                                 and response_format=={'type':'text','mime_type':'application/json','schema':trans.SCHEMA})
                calls["sent"]+=1
                return types.SimpleNamespace(output_text='{"language":"en","segments":[]}')
        class Client:
            def __init__(self,*,api_key,http_options):
                assert api_key=="only-for-test"
                assert http_options["retry_options"]["attempts"] == 1
                self.files=Files()
                self.interactions=Interactions()
        fake_google=types.ModuleType("google")
        fake_genai=types.ModuleType("google.genai")
        fake_genai.Client=Client
        fake_google.genai=fake_genai
        with patch.dict(sys.modules, {"google":fake_google,"google.genai":fake_genai}):
            with patch.dict("os.environ",{"GEMINI_API_KEY":"only-for-test"}):
                result=trans.call_gemini(Path("fake.wav"))
        self.assertIn('"segments":[]',result)
        self.assertEqual(calls["sent"],1)
        self.assertTrue(calls["deleted"])

    def test_overlap_and_rounding_rejected(self):
        for segments in [[{ "start":0,"end":2},{"start":1,"end":3}], [{"start":0.0001,"end":0.0002}]]:
            for item in segments:
                item.update(original="heard",pt_br="ouvido",clarity="clear")
            with self.assertRaises(ValueError):
                trans.transform_response({"segments":segments},4)

    def test_safe_errors_do_not_repeat_upstream_credentials(self):
        err=Exception("private upstream content")
        err.code=429
        self.assertIn("Quota",trans.safe_error(err))
        self.assertNotIn("private",trans.safe_error(err))

    def test_missing_key_cannot_replace_manual_lyrics(self):
        with tempfile.TemporaryDirectory() as folder:
            directory=Path(folder)
            (directory/"public/input").mkdir(parents=True)
            target=directory/"public/input/lyrics.json"
            target.write_text('{"words":[{"text":"ORIGINAL"}]}')
            old=Path.cwd()
            try:
                import os
                os.chdir(folder)
                with patch.dict("os.environ",{"GEMINI_API_KEY":""}):
                    with self.assertRaises(ValueError):
                        trans.main()
            finally:
                os.chdir(old)
            self.assertIn("ORIGINAL",target.read_text())

if __name__=="__main__":
    unittest.main()

