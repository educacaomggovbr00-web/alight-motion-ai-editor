import React from "react";
import {
  AbsoluteFill,
  Audio,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { AnimatedLyrics } from "./AnimatedLyrics";
import {
  AnimatedBackground,
  ArtistVideo,
  BeatShake,
  DarkColorGrade,
  FlashOverlay,
  GlitchEffect,
  ImpactZoom,
  RGBSplit,
  pulseAt,
} from "./effects";
import type { EditProps } from "./schema";
export const Edit: React.FC<EditProps> = (p) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pulse = p.effects ? pulseAt(frame, fps, p.beats) : 0;
  const layers = (
    <AbsoluteFill>
      <ArtistVideo src={p.video} />
      <AnimatedLyrics p={p} />
    </AbsoluteFill>
  );
  // Artist grading stays under the lyrics, so typography remains high contrast.
  const graded = (
    <AbsoluteFill>
      <DarkColorGrade preset={p.preset} pulse={pulse} intensity={p.intensity}>
        <ArtistVideo src={p.video} />
      </DarkColorGrade>
      <AnimatedLyrics p={p} />
    </AbsoluteFill>
  );
  const finalLayers =
    p.preset === "dark-lyrics" ? (
      <ImpactZoom slow pulse={0} intensity={p.intensity}>
        {graded}
      </ImpactZoom>
    ) : (
      <BeatShake pulse={pulse} intensity={p.intensity}>
        <ImpactZoom pulse={pulse} intensity={p.intensity}>
          {p.preset === "emo-rap-glitch" ? (
            <GlitchEffect pulse={pulse} intensity={p.intensity}>
              <RGBSplit pulse={pulse} intensity={p.intensity}>
                {graded}
              </RGBSplit>
            </GlitchEffect>
          ) : (
            graded
          )}
        </ImpactZoom>
      </BeatShake>
    );
  return (
    <AbsoluteFill style={{ background: "#000", overflow: "hidden" }}>
      <AnimatedBackground />
      {p.effects ? finalLayers : layers}
      {p.effects && p.preset !== "dark-lyrics" && (
        <FlashOverlay
          pulse={pulse}
          intensity={p.intensity}
          reduced={p.reduceFlashes}
        />
      )}
      <AbsoluteFill
        style={{ boxShadow: "inset 0 0 100px #0008", pointerEvents: "none" }}
      />
      {p.demo && (
        <div
          style={{
            position: "absolute",
            top: 35,
            left: 30,
            color: "#fff",
            font: "18px monospace",
            letterSpacing: 3,
          }}
        >
          DEMO · TEXTO SINTÉTICO
        </div>
      )}
      {p.audio && <Audio src={staticFile(p.audio)} />}
    </AbsoluteFill>
  );
};
