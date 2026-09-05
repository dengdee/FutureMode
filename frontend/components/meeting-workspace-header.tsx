import { IconArrowLeft } from "@tabler/icons-react";
import Link from "next/link";

export function MeetingWorkspaceHeader({
  phase,
  title,
}: {
  meetingId?: string;
  phase: "prepare" | "summary" | "review" | "audio" | "live";
  title?: string;
}) {
  const phaseLabel = {
    prepare: "議前討論",
    summary: "議前整理",
    review: "會後回顧",
    audio: "收音設定",
    live: "即時會議",
  }[phase];

  return (
    <div className="border-b border-[#e6e6e3] pb-6">
      <Link
        href="/dashboard"
        className="inline-flex items-center gap-1 text-sm text-[#787774] hover:text-[#1f1f1f]"
      >
        <IconArrowLeft size={17} />
        返回儀表板
      </Link>
      <div className="mt-5 flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <div>
          <p className="text-sm font-medium text-[#0f9f8a]">{phaseLabel}</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">
            {title ?? "會議工作區"}
          </h1>
          <p className="mt-2 text-sm text-[#787774]">
            依序完成議前討論、議前整理、會中協作與會後確認。
          </p>
        </div>
      </div>
    </div>
  );
}
