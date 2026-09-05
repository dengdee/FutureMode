"use client";

import { IconCalendarPlus, IconClock } from "@tabler/icons-react";
import Link from "next/link";
import { redirect, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AppShell } from "../../../../components/app-shell";
import { PageHeader } from "../../../../components/page-header";
import { TeamSubnav } from "../../../../components/team-subnav";
import { listMeetings } from "../../../../lib/api/meetings";
import { listTeams } from "../../../../lib/api/teams";
import type { MeetingSummary, Team } from "../../../../types/api";

const labels: Record<string, string> = {
  draft: "草稿",
  scheduled: "已排程",
  in_progress: "進行中",
  completed: "已結束",
  cancelled: "已取消",
};
const statusClass: Record<string, string> = {
  draft: "bg-slate-100 text-slate-700",
  scheduled: "bg-blue-50 text-blue-700",
  in_progress: "bg-amber-50 text-amber-800",
  completed: "bg-emerald-50 text-emerald-700",
  cancelled: "bg-rose-50 text-rose-700",
};

export default function WorkspaceMeetingsPage() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  redirect(`/workspaces/${workspaceId}`);
  const [team, setTeam] = useState<Team | null>(null);
  const [meetings, setMeetings] = useState<MeetingSummary[]>([]);
  const [summaryReady, setSummaryReady] = useState<Record<string, boolean>>({});
  const [page, setPage] = useState(1);
  const [error, setError] = useState("");
  useEffect(() => {
    Promise.all([listTeams(), listMeetings()])
      .then(([teams, all]) => {
        const filtered = all.filter((item) => item.team_id === workspaceId);
        setTeam(teams.teams.find((item) => item.id === workspaceId) ?? null);
        setMeetings(filtered);
        setSummaryReady(
          Object.fromEntries(
            filtered.map((meeting) => {
              const deadline = localStorage.getItem(
                `proximate:prep-deadline:${meeting.id}`,
              );
              return [
                meeting.id,
                Boolean(deadline) &&
                  new Date(deadline!).getTime() <= Date.now(),
              ];
            }),
          ),
        );
      })
      .catch((cause) =>
        setError(cause instanceof Error ? cause.message : "無法讀取團隊會議。"),
      );
  }, [workspaceId]);
  const pageSize = 10;
  const pageCount = Math.max(1, Math.ceil(meetings.length / pageSize));
  const visibleMeetings = meetings.slice(
    (page - 1) * pageSize,
    page * pageSize,
  );
  return (
    <AppShell>
      <PageHeader
        eyebrow="Team meetings"
        title={team ? `${team.name} 的會議` : "團隊會議"}
        description="每場會議從議前討論開始；期限到後再開放 AI 議前整理與收音設定。"
        backHref={`/workspaces/${workspaceId}`}
        backLabel="返回團隊"
        actions={
          <>
            <Link
              href={`/meetings/new?teamId=${workspaceId}`}
              className="inline-flex items-center gap-2 rounded-primary bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-white"
            >
              <IconCalendarPlus size={17} />
              建立會議
            </Link>
          </>
        }
      />
      <div className="mt-8">
        <TeamSubnav teamId={workspaceId} active="meetings" />
      </div>
      {error ? (
        <p
          role="alert"
          className="mt-6 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          {error}
        </p>
      ) : (
        <section className="mt-6 space-y-3">
          {visibleMeetings.map((meeting) => (
            <article
              key={meeting.id}
              className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-[#e6e6e3] bg-white p-5"
            >
              <div className="min-w-0 flex-1">
                <h2 className="truncate font-semibold">{meeting.title}</h2>
                <p className="mt-2 flex items-center gap-2 text-sm text-[#787774]">
                  <IconClock size={16} />
                  {meeting.scheduled_at
                    ? new Date(meeting.scheduled_at).toLocaleString("zh-TW")
                    : "尚未設定時間"}
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold ${statusClass[meeting.status] ?? statusClass.draft}`}
                >
                  {labels[meeting.status] ?? meeting.status}
                </span>
                <Link
                  href={`/meetings/${meeting.id}/prepare`}
                  className="rounded-lg border border-[#cde5df] px-3 py-2 text-sm font-semibold text-[#087e6d] hover:bg-[#f0fbf8]"
                >
                  議前討論
                </Link>
                {summaryReady[meeting.id] ? (
                  <Link
                    href={`/meetings/${meeting.id}/pre-meeting-summary`}
                    className="rounded-lg bg-[#0f9f8a] px-3 py-2 text-sm font-semibold text-white"
                  >
                    議前整理
                  </Link>
                ) : (
                  <span
                    title="參與者填寫期限到後開放"
                    className="cursor-not-allowed rounded-lg bg-[#e6e6e3] px-3 py-2 text-sm font-semibold text-[#9b9a97]"
                  >
                    議前整理
                  </span>
                )}
              </div>
            </article>
          ))}
          {meetings.length === 0 && (
            <div className="rounded-2xl border border-dashed border-[#d8d8d5] bg-white p-12 text-center">
              <h2 className="font-semibold">尚未建立會議</h2>
              <p className="mt-2 text-sm text-[#787774]">
                建立第一場會議，再讓成員和 Agent 整理會前重點。
              </p>
            </div>
          )}
          {meetings.length > pageSize && (
            <nav
              aria-label="團隊會議分頁"
              className="flex items-center justify-center gap-2 pt-4"
            >
              <button
                type="button"
                disabled={page === 1}
                onClick={() => setPage((current) => current - 1)}
                className="rounded-lg border border-[#dededb] px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-40"
              >
                上一頁
              </button>
              <span className="px-2 text-sm text-[#787774]">
                第 {page} / {pageCount} 頁
              </span>
              <button
                type="button"
                disabled={page === pageCount}
                onClick={() => setPage((current) => current + 1)}
                className="rounded-lg border border-[#dededb] px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-40"
              >
                下一頁
              </button>
            </nav>
          )}
        </section>
      )}
    </AppShell>
  );
}
