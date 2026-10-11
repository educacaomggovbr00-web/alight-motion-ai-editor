import { test } from "node:test";
import assert from "node:assert/strict";
import {
  demoProps,
  validateWords,
  validateBeats,
  validateProps,
} from "../src/schema";
import { pulseAt } from "../src/effects";
const rejects = (f: () => unknown) => assert.throws(f);
test("timestamps, palavras e estilos", () => {
  assert.equal(
    validateWords(
      {
        words: [
          { text: "demo", start: 0, end: 1, font: "gothic", color: "#ff0044" },
        ],
      },
      4,
    ).length,
    1,
  );
  for (const words of [
    [{ text: "x", start: 1, end: 0.5 }],
    [{ text: "", start: 0, end: 1 }],
    [{ text: "x", start: 0, end: 5 }],
    [{ text: "x", start: NaN, end: 1 }],
    [{ text: "x", start: 0, end: 1, x: 2 }],
  ])
    rejects(() => validateWords({ words }, 4));
});
test("batidas espaçadas e limites", () => {
  assert.deepEqual(validateBeats({ beats: [0, 0.5, 1] }, 4), [0, 0.5, 1]);
  rejects(() => validateBeats({ beats: [1, 0.5] }, 4));
  rejects(() => validateBeats({ beats: [0, 0.1] }, 4));
  rejects(() => validateBeats({ beats: [4] }, 4));
});
test("entrada local e resolucoes", () => {
  assert.equal(validateProps(demoProps).width, 540);
  rejects(() =>
    validateProps({ ...demoProps, video: "https://secret/video.mp4" }),
  );
  rejects(() => validateProps({ ...demoProps, duration: 31 }));
  rejects(() => validateProps({ ...demoProps, width: 480 }));
});
test("pulso determinista e localizado no tempo", () => {
  assert.equal(pulseAt(15, 30, [0.5]), 1);
  assert.equal(pulseAt(14, 30, [0.5]), 0);
  assert.equal(pulseAt(45, 30, [0.5]), 0);
  assert.equal(pulseAt(17, 30, [0.5]), pulseAt(17, 30, [0.5]));
});
