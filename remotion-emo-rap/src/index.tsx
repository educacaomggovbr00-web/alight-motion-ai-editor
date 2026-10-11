import React from "react";
import { Composition, registerRoot } from "remotion";
import "@fontsource/anton/latin-400.css";
import "@fontsource/unifrakturcook/latin-700.css";
import { Edit } from "./Edit";
import { demoProps, validateProps } from "./schema";
const Root = () => (
  <Composition
    id="EmoRap"
    component={Edit}
    width={540}
    height={960}
    fps={30}
    durationInFrames={120}
    defaultProps={demoProps}
    calculateMetadata={({ props }) => {
      const p = validateProps(props);
      return {
        width: p.width,
        height: p.height,
        durationInFrames: Math.round(p.duration * 30),
        props: p,
      };
    }}
  />
);
registerRoot(Root);
