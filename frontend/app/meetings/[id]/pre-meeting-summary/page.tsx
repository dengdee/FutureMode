"use client";

import { IconSparkles } from "@tabler/icons-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AppShell } from "../../../../components/app-shell";
import { MeetingWorkspaceHeader } from "../../../../components/meeting-workspace-header";
import { listAgendaItems } from "../../../../lib/api/agenda";
import { getMeeting } from "../../../../lib/api/meetings";
import type { AgendaItem, MeetingSummary } from "../../../../types/api";

export default function PreMeetingSummaryPage() {
  const { id } = useParams<{ id: string }>();
  const [meeting, setMeeting] = useState<MeetingSummary | null>(null);
  const [agenda, setAgenda] = useState<AgendaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function refresh() {
    const [current, agendaResult] = await Promise.all([
      getMeeting(id),
      listAgendaItems(id),
    ]);
    setMeeting(current);
    setAgenda(agendaResult.items);
  }
  useEffect(() => {
    refresh()
      .catch((cause) =>
        setError(cause instanceof Error ? cause.message : "無法讀取議前整理。"),
      )
      .finally(() => setLoading(false));
  }, [id]);
  if (loading)
    return (
      <AppShell>
        <p className="text-sm text-[#787774]">正在整理會前資料…</p>
      </AppShell>
    );
  if (!meeting)
    return (
      <AppShell>
        <p
          role="alert"
          className="rounded-xl bg-red-50 p-4 text-sm text-red-700"
        >
          {error || "找不到此會議。"}
        </p>
      </AppShell>
    );
  return (
    <AppShell>
      <MeetingWorkspaceHeader phase="summary" title={meeting.title} />
      <section className="mt-6 rounded-2xl border border-[#e6e6e3] bg-white p-5 sm:p-7">
        {(notice || error) && (
          <p
            role={error ? "alert" : "status"}
            className={`mt-4 rounded-xl px-4 py-3 text-sm ${error ? "bg-red-50 text-red-700" : "bg-[#e7f7ef] text-[#087e6d]"}`}
          >
            {error || notice}
          </p>
        )}
        <div className="mt-5 flex items-start gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#e7f7ef] text-[#087e6d]">
            <IconSparkles size={20} />
          </span>
          <div>
            <h2 className="text-lg font-semibold">AI 議前整理</h2>
            <p className="mt-1 text-sm leading-6 text-[#787774]">
              在所有參與者完成議前討論後，這裡會彙整共同議程、已確認共識與待解決衝突。
            </p>
          </div>
        </div>
      </section>
      <section className="mt-6 rounded-2xl border border-[#e6e6e3] bg-white p-5 sm:p-7">
        <h2 className="text-lg font-semibold">本場共同議程</h2>
        <ol className="mt-5 space-y-3">
          {agenda.map((item) => (
            <li
              key={item.id}
              className="flex gap-3 rounded-xl bg-[#f7f7f5] p-4"
            >
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-white text-sm font-semibold text-[#087e6d]">
                {item.position}
              </span>
              <div>
                <p className="font-medium">{item.title}</p>
                <p className="mt-1 text-sm text-[#787774]">
                  {item.status === "completed"
                    ? "已完成討論"
                    : "待於會議中確認"}
                </p>
              </div>
            </li>
          ))}
          {agenda.length === 0 && (
            <li className="rounded-xl bg-[#f7f7f5] p-4 text-sm text-[#787774]">
              本場尚未設定議程。
            </li>
          )}
        </ol>
      </section>
    </AppShell>
  );
}
