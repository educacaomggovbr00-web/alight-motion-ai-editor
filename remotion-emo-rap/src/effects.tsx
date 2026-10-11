import React from "react";
import {
  AbsoluteFill,
  OffthreadVideo,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { EditProps } from "./schema";
export const pulseAt = (
  frame: number,
  fps: number,
  beats: number[],
  length = 0.22,
) =>
  beats.reduce(
    (max, b) =>
      Math.max(
        max,
        frame >= b * fps
          ? Math.max(0, 1 - (frame - b * fps) / (length * fps))
          : 0,
      ),
    0,
  );
export const ArtistVideo: React.FC<{ src: string }> = ({ src }) => (
  <OffthreadVideo
    src={staticFile(src)}
    muted
    style={{ width: "100%", height: "100%", objectFit: "cover" }}
  />
);
export const AnimatedBackground: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(ellipse at ${40 + 10 * Math.sin(frame / 60)}% 60%, #311040, #030207 80%)`,
      }}
    />
  );
};
export const DarkColorGrade: React.FC<{
  children: React.ReactNode;
  preset: EditProps["preset"];
  pulse: number;
  intensity: number;
}> = ({ children, preset, pulse, intensity }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        filter:
          preset === "dark-lyrics"
            ? "grayscale(1) brightness(.45) contrast(1.2)"
            : `saturate(${pulse > 0.5 ? 1.4 : 0.35}) contrast(1.3) brightness(${0.6 + pulse * 0.18}) hue-rotate(${(Math.floor(frame / 30) % 3) * 35}deg)`,
        opacity: 0.96,
      }}
    >
      {children}
      <AbsoluteFill
        style={{
          background: "linear-gradient(0deg,rgba(0,0,0,.85),transparent 70%)",
          boxShadow: `inset 0 0 130px ${30 * intensity}px #000`,
        }}
      />
    </AbsoluteFill>
  );
};
export const BeatShake: React.FC<{
  children: React.ReactNode;
  pulse: number;
  intensity: number;
}> = ({ children, pulse, intensity }) => {
  const f = useCurrentFrame();
  const a = 10 * pulse * intensity;
  return (
    <AbsoluteFill
      style={{
        transform: `translate(${Math.sin(f * 2.1) * a}px,${Math.cos(f * 2.7) * a}px) rotate(${Math.sin(f * 1.3) * pulse * intensity}deg)`,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};
export const ImpactZoom: React.FC<{
  children: React.ReactNode;
  pulse: number;
  intensity: number;
  slow?: boolean;
}> = ({ children, pulse, intensity, slow }) => {
  const f = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const z = slow
    ? interpolate(f, [0, durationInFrames], [1.03, 1.15])
    : 1.05 + 0.16 * pulse * intensity;
  return (
    <AbsoluteFill
      style={{
        transform: `scale(${z})`,
        filter: `blur(${slow ? 0 : pulse * intensity * 1.8}px)`,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};
export const RGBSplit: React.FC<{
  children: React.ReactNode;
  pulse: number;
  intensity: number;
}> = ({ children, pulse, intensity }) => (
  <AbsoluteFill>
    {children}
    {pulse > 0.08 && (
      <>
        <AbsoluteFill
          style={{
            transform: `translateX(${7 * pulse * intensity}px)`,
            mixBlendMode: "screen",
            opacity: 0.2 * pulse,
            filter: "sepia(1) saturate(9) hue-rotate(290deg)",
          }}
        >
          {children}
        </AbsoluteFill>
        <AbsoluteFill
          style={{
            transform: `translateX(${-7 * pulse * intensity}px)`,
            mixBlendMode: "screen",
            opacity: 0.2 * pulse,
            filter: "sepia(1) saturate(9) hue-rotate(150deg)",
          }}
        >
          {children}
        </AbsoluteFill>
      </>
    )}
  </AbsoluteFill>
);
export const GlitchEffect: React.FC<{
  children: React.ReactNode;
  pulse: number;
  intensity: number;
}> = ({ children, pulse, intensity }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill>
      {children}
      {pulse > 0.6 && (
        <AbsoluteFill
          style={{
            clipPath: `inset(${(f * 7) % 65}% 0 ${10 + ((f * 11) % 20)}% 0)`,
            transform: `translateX(${(f % 2 ? 1 : -1) * 18 * intensity}px)`,
            filter: "invert(1)",
            opacity: 0.45,
          }}
        >
          {children}
        </AbsoluteFill>
      )}
      {pulse > 0.6 && (
        <AbsoluteFill
          style={{
            opacity: 0.12 * intensity,
            background:
              "repeating-linear-gradient(transparent 0px,transparent 6px,#fff 7px,transparent 8px)",
          }}
        />
      )}
    </AbsoluteFill>
  );
};
export const FlashOverlay: React.FC<{
  pulse: number;
  intensity: number;
  reduced: boolean;
}> = ({ pulse, intensity, reduced }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        background: Math.floor(f / 15) % 2 ? "#ce163d" : "white",
        opacity: Math.pow(pulse, 4) * intensity * (reduced ? 0.035 : 0.12),
      }}
    />
  );
};
