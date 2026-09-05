"use client";

import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import type { ReactNode } from "react";

export function Tooltip({ content, children }: { content: string; children: ReactNode }) {
  return <TooltipPrimitive.Provider delayDuration={180}><TooltipPrimitive.Root><TooltipPrimitive.Trigger asChild>{children}</TooltipPrimitive.Trigger><TooltipPrimitive.Portal><TooltipPrimitive.Content side="bottom" sideOffset={8} className="z-50 rounded-md bg-[#1f1f1f] px-2.5 py-1.5 text-xs text-white shadow-sm animate-in fade-in-0 zoom-in-95">{content}<TooltipPrimitive.Arrow className="fill-[#1f1f1f]" /></TooltipPrimitive.Content></TooltipPrimitive.Portal></TooltipPrimitive.Root></TooltipPrimitive.Provider>;
}
