import { Composition, registerRoot } from "remotion";
import React from "react";
import { Video } from "./Video";

const RemotionRoot: React.FC = () => (
  <Composition
    id="ProximateShowcase"
    component={Video}
    durationInFrames={3600}
    fps={30}
    width={1920}
    height={1080}
  />
);

registerRoot(RemotionRoot);
