import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { EditProps, Word } from "./schema";
const colors = ["#ffffff", "#ff334e", "#9c66ff", "#83bfff"];
const WordLayer: React.FC<{ word: Word; index: number; p: EditProps }> = ({
  word,
  index,
  p,
}) => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const from = word.start * fps,
    end = word.end * fps,
    local = frame - from;
  if (frame < from || frame >= end) return null;
  const total = end - from;
  const envelope = interpolate(
    local,
    [0, Math.min(3, total / 3), Math.max(total * 0.67, total - 4), total],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  const entrance = spring({
    frame: local,
    fps,
    config: {
      damping: p.preset === "dark-lyrics" ? 22 : 13,
      stiffness: 210,
      mass: 0.65,
    },
  });
  const big = p.preset === "big-text-impact";
  const aggressive = p.preset === "emo-rap-glitch";
  const base =
    width * (big ? (index % 3 === 1 ? 0.16 : 0.24) : aggressive ? 0.18 : 0.14);
  const fontSize = Math.min(
    base * (word.size ?? 1),
    (width * 0.85) / Math.max(1, word.text.length * 0.62),
  );
  const scale = p.effects
    ? p.preset === "dark-lyrics"
      ? interpolate(local, [0, total], [0.88, 1.12], {
          easing: Easing.bezier(0.22, 0.7, 0.3, 1),
        })
      : 0.55 + 0.5 * entrance
    : 1;
  const rotation =
    p.effects && big
      ? (index % 2 ? 1 : -1) * interpolate(entrance, [0, 1], [12, -4])
      : 0;
  const y =
    (word.y ?? (big ? 0.42 + (index % 3) * 0.08 : aggressive ? 0.58 : 0.66)) *
    p.height;
  const color =
    word.color ??
    (p.preset === "dark-lyrics" ? "#ffffff" : colors[index % colors.length]);
  const font = word.font ?? (big && index % 2 === 0 ? "gothic" : "heavy");
  return (
    <div
      style={{
        position: "absolute",
        left: `${(word.x ?? 0.5) * 100}%`,
        top: y,
        transform: `translate(-50%,-50%) scale(${scale}) rotate(${rotation}deg)`,
        opacity: envelope,
        fontFamily:
          font === "gothic"
            ? "UnifrakturCook"
            : font === "mono"
              ? "monospace"
              : "Anton",
        fontSize,
        lineHeight: 0.95,
        textTransform: "uppercase",
        whiteSpace: "nowrap",
        color,
        textAlign: "center",
        letterSpacing: big ? "-2px" : "1px",
        textShadow: `0 0 ${aggressive ? 20 : 8}px ${color}99, 3px 4px 0 #000`,
        WebkitTextStroke: big ? "1px #ffffff40" : undefined,
      }}
    >
      {aggressive && p.effects && (
        <span
          style={{
            position: "absolute",
            color: "#ff123d",
            opacity: 0.45,
            transform: `translate(${-3 * Math.sin(frame * 1.7)}px,2px)`,
          }}
        >
          {word.text}
        </span>
      )}
      {word.text}
      {big && p.effects && (
        <div
          style={{
            fontFamily: "Anton",
            fontSize: fontSize * 0.18,
            letterSpacing: 5,
            color: "#ffffff99",
            marginTop: 12,
          }}
        >
          ◈ {String(index + 1).padStart(2, "0")} ◈
        </div>
      )}
    </div>
  );
};
export const AnimatedLyrics: React.FC<{ p: EditProps }> = ({ p }) => (
  <AbsoluteFill>
    {p.words.map((w, i) => (
      <WordLayer key={i} word={w} index={i} p={p} />
    ))}
  </AbsoluteFill>
);
