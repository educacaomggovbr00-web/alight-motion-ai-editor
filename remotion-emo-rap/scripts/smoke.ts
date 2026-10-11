import { execFileSync } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs";
import { makeDemo } from "./demo";
import { prepare } from "./prepare";
import { renderer } from "./render";
import { verify } from "./verify";
import { writeJson } from "./common";
import { presets } from "../src/schema";
const pixels = (file: string) =>
  execFileSync(
    "ffmpeg",
    [
      "-v",
      "error",
      "-i",
      file,
      "-vf",
      "scale=90:160",
      "-f",
      "rawvideo",
      "-pix_fmt",
      "rgb24",
      "-frames:v",
      "1",
      "pipe:1",
    ],
    { maxBuffer: 100000, timeout: 30000 },
  );
const diff = (a: Buffer, b: Buffer) =>
  a.reduce((s, v, i) => s + Math.abs(v - b[i]), 0) / a.length;
const hash = (b: Buffer) => crypto.createHash("sha256").update(b).digest("hex");
makeDemo();
const base = prepare({ demo: true });
const r = await renderer();
const reports = [];
const samples: Buffer[] = [];
try {
  for (const preset of presets) {
    const p = { ...base, preset };
    const prefix = "out/" + preset;
    await r.video(p, prefix + ".mp4");
    const check = verify(prefix + ".mp4", p);
    await r.still(p, 34, prefix + "-impact.png");
    await r.still(p, 46, prefix + "-settled.png");
    await r.still({ ...p, effects: false }, 34, prefix + "-control.png");
    await r.still(p, 34, prefix + "-repeat.png");
    const impact = pixels(prefix + "-impact.png"),
      settled = pixels(prefix + "-settled.png"),
      control = pixels(prefix + "-control.png"),
      repeat = pixels(prefix + "-repeat.png");
    const effectDifference = diff(impact, control),
      timeDifference = diff(impact, settled);
    if (
      effectDifference < 1 ||
      timeDifference < 1 ||
      hash(impact) !== hash(repeat)
    )
      throw new Error("Quadros sem diferenca visual ou nao deterministas");
    samples.push(impact);
    reports.push({
      preset,
      ...check,
      effectDifference,
      timeDifference,
      deterministicSample: true,
    });
  }
  const presetDifferences = [
    diff(samples[0], samples[1]),
    diff(samples[1], samples[2]),
    diff(samples[0], samples[2]),
  ];
  if (presetDifferences.some((v) => v < 1))
    throw new Error("Presets visualmente iguais");
  const optional = { ...base, duration: 1, words: [], beats: [], audio: null };
  await r.video(optional, "out/sem-letras-sem-audio.mp4");
  const optionalInputs = verify("out/sem-letras-sem-audio.mp4", optional);
  writeJson("out/smoke.json", {
    state: "testado",
    demoOnly: true,
    renderer: "Remotion",
    reports,
    presetDifferences,
    optionalInputs,
    note: "Amostras comprovam diferencas e determinismo nos quadros escolhidos; nao avaliam automaticamente qualidade profissional.",
  });
  console.log(
    JSON.stringify({
      state: "testado",
      presets: 3,
      reports,
      presetDifferences,
    }),
  );
} finally {
  await r.browser.close({ silent: true });
}
