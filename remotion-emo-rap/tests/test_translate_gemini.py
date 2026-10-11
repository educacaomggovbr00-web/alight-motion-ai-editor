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
        self.assertEqual(lyrics["words"], [{
            "text":"Sinto saudade de você","start":0.5,"end":1.5,
            "font":"heavy","color":"#ffffff","x":0.5,"y":0.66
        }])
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
            def create(self, *, model, input, response_format):
                self.assertion= (model==trans.MODEL and input[1]["uri"]==uploaded.uri
                                 and response_format=={'type':'text','mime_type':'application/json','schema':trans.SCHEMA})
                calls["sent"]+=1
                return types.SimpleNamespace(output_text='{"language":"en","segments":[]}')
        class Client:
            def __init__(self,*,api_key):
                assert api_key=="only-for-test"
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
