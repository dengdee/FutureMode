import { IconArrowLeft, IconCircleCheck, IconVideo } from "@tabler/icons-react";
import Link from "next/link";

export function MeetingWorkspaceHeader({ meetingId, phase }: { meetingId: string; phase: "prepare" | "review" | "audio" | "live" }) {
  const phaseLabel = { prepare: "會前準備", review: "會後回顧", audio: "收音設定", live: "即時會議" }[phase];

  return (
    <div className="border-b border-[#e6e6e3] pb-6">
      <Link href="/dashboard" className="inline-flex items-center gap-1 text-sm text-[#787774] hover:text-[#1f1f1f]"><IconArrowLeft size={17} />返回會議</Link>
      <div className="mt-5 flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <div><p className="text-sm font-medium text-[#0f9f8a]">{phaseLabel}</p><h1 className="mt-2 text-3xl font-semibold tracking-tight">產品方向校準會議</h1><p className="mt-2 text-sm text-[#787774]">Meeting #{meetingId}</p></div>
        <div className="flex flex-wrap gap-2 text-sm"><span className="inline-flex items-center gap-1 rounded-full bg-[#e7f7ef] px-3 py-1.5 text-[#1d6b4d]"><IconCircleCheck size={16} />會議脈絡已載入</span><span className="inline-flex items-center gap-1 rounded-full bg-[#f1f1ef] px-3 py-1.5 text-[#5f5f5b]"><IconVideo size={16} />Google Meet</span></div>
      </div>
    </div>
  );
}
