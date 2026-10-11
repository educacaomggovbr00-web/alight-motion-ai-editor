import fs from "node:fs";
import path from "node:path";
import {
  demoProps,
  validateProps,
  validateWords,
  validateBeats,
  type EditProps,
} from "../src/schema";
import { probe, readJson, writeJson } from "./common";
const sizeFile = (name: string, max: number) => {
  const f = path.resolve("public/input", name);
  if (
    fs.lstatSync(f).isSymbolicLink() ||
    !fs.statSync(f).isFile() ||
    fs.statSync(f).size > max ||
    fs.statSync(f).size === 0
  )
    throw new Error("Arquivo invalido ou excede limite");
  return f;
};
export function prepare(overrides: Partial<EditProps> = {}) {
  const p = { ...demoProps, demo: false, ...overrides };
  validateProps({ ...p, words: [], beats: [] });
  if (!fs.existsSync("public/input/artist.mp4"))
    throw new Error("Entrada ausente: artist.mp4 obrigatorio");
  const v = probe(sizeFile("artist.mp4", 300 * 1024 ** 2));
  const vs = v.streams.find((s) => s.codec_type === "video");
  if (
    !v.format.format_name.includes("mp4") ||
    !vs ||
    vs.codec_name !== "h264" ||
    vs.width > 3840 ||
    vs.height > 3840 ||
    !Number.isFinite(Number(v.format.duration)) ||
    Number(v.format.duration) + 0.02 < p.duration ||
    Number(v.format.duration) > 300
  )
    throw new Error("Video requer H.264, ate 3840px/5min e duracao suficiente");
  const music = ["music.wav", "music.mp3", "music.m4a"].filter((name) =>
    fs.existsSync("public/input/" + name),
  );
  if (music.length > 1) throw new Error("Forneca apenas uma musica");
  p.audio = v.streams.some((s) => s.codec_type === "audio")
    ? "input/artist.mp4"
    : null;
  if (music.length) {
    const a = probe(sizeFile(music[0], 100 * 1024 ** 2));
    if (
      !a.streams.some((s) => s.codec_type === "audio") ||
      !Number.isFinite(Number(a.format.duration)) ||
      Number(a.format.duration) + 0.02 < p.duration ||
      Number(a.format.duration) > 300
    )
      throw new Error("Audio invalido ou curto");
    p.audio = "input/" + music[0];
  }
  p.words = fs.existsSync("public/input/lyrics.json")
    ? validateWords(readJson(sizeFile("lyrics.json", 1024 ** 2)), p.duration)
    : [];
  p.beats = fs.existsSync("public/input/beats.json")
    ? validateBeats(readJson(sizeFile("beats.json", 1024 ** 2)), p.duration)
    : [];
  fs.mkdirSync("out", { recursive: true });
  writeJson("out/props.json", validateProps(p));
  return p;
}
if (process.argv[1]?.endsWith("prepare.ts")) {
  const width = Number(process.env.RESOLUTION ?? 540);
  const p = prepare({
    preset: (process.env.PRESET ?? "dark-lyrics") as EditProps["preset"],
    intensity:
      { leve: 0.3, medio: 0.65, forte: 1 }[process.env.INTENSITY ?? "medio"] ??
      NaN,
    width,
    height: (width / 9) * 16,
    duration: Number(process.env.DURATION ?? 4),
    reduceFlashes: process.env.REDUCE_FLASHES !== "false",
    demo: process.env.DEMO === "true",
  });
  console.log(
    `Entrada validada: ${p.words.length} palavras, ${p.beats.length} impactos manuais; nao houve transcricao nem deteccao automatica`,
  );
}
