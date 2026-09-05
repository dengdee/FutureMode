"use client";

import {
  IconArrowRight,
  IconCalendarPlus,
  IconUsersGroup,
} from "@tabler/icons-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "../../components/app-shell";
import { InvitationInbox } from "../../components/invitation-inbox";
import { listMeetings } from "../../lib/api/meetings";
import { listTeams } from "../../lib/api/teams";
import type { MeetingSummary, Team } from "../../types/api";

const statusLabel: Record<string, string> = {
  draft: "等待準備",
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
const timeValue = (meeting: MeetingSummary) =>
  meeting.scheduled_at
    ? new Date(meeting.scheduled_at).getTime()
    : Number.MAX_SAFE_INTEGER;

export default function DashboardPage() {
  const [meetings, setMeetings] = useState<MeetingSummary[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [summaryReady, setSummaryReady] = useState<Record<string, boolean>>({});
  const [error, setError] = useState("");
  useEffect(() => {
    Promise.all([listMeetings(), listTeams()])
      .then(([meetingResult, teamResult]) => {
        const ordered = meetingResult.sort(
          (a, b) => timeValue(a) - timeValue(b),
        );
        setMeetings(ordered);
        setTeams(teamResult.teams);
        setSummaryReady(
          Object.fromEntries(
            ordered.map((meeting) => {
              const deadline = window.localStorage.getItem(
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
        setError(cause instanceof Error ? cause.message : "無法讀取工作總覽。"),
      );
  }, []);
  const activeMeetings = meetings.filter(
    (item) => item.status !== "completed" && item.status !== "cancelled",
  );
  const nextMeeting = activeMeetings[0];
  const teamName = (id: string) =>
    teams.find((item) => item.id === id)?.name ?? "所屬團隊";
  return (
    <AppShell>
      <InvitationInbox />
      <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--accent)]">
            Overview
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
            今天要推進什麼？
          </h1>
          <p className="mt-2 text-[#787774]">
            從下一場會議開始準備，或直接進入團隊管理資料與成員。
          </p>
        </div>
        <Link
          href="/meetings/new"
          className="inline-flex w-fit items-center gap-2 rounded-primary bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-white"
        >
          <IconCalendarPlus size={17} />
          建立會議
        </Link>
      </div>
      {error && (
        <p
          role="alert"
          className="mt-6 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          {error}
        </p>
      )}
      <section className="mt-8 grid gap-5 lg:grid-cols-[minmax(0,1.5fr)_minmax(280px,0.8fr)]">
        <div className="rounded-2xl border border-[#cde5df] bg-[#f0fbf8] p-6">
          <p className="text-sm font-semibold text-[#087e6d]">下一場會議</p>
          {nextMeeting ? (
            <>
              <h2 className="mt-3 text-2xl font-semibold">
                {nextMeeting.title}
              </h2>
              <p className="mt-2 text-sm text-[#4c6e65]">
                {teamName(nextMeeting.team_id)} ·{" "}
                {nextMeeting.scheduled_at
                  ? new Date(nextMeeting.scheduled_at).toLocaleString("zh-TW")
                  : "尚未設定時間"}
              </p>
              <div className="mt-6 flex flex-wrap gap-2">
                <Link
                  href={`/meetings/${nextMeeting.id}/prepare`}
                  className="inline-flex items-center gap-2 rounded-lg bg-[#0f9f8a] px-4 py-2.5 text-sm font-semibold text-white"
                >
                  議前討論 <IconArrowRight size={17} />
                </Link>
                {summaryReady[nextMeeting.id] ? (
                  <Link
                    href={`/meetings/${nextMeeting.id}/pre-meeting-summary`}
                    className="inline-flex items-center gap-2 rounded-lg border border-[#9ddbc8] px-4 py-2.5 text-sm font-semibold text-[#087e6d]"
                  >
                    議前準備
                  </Link>
                ) : (
                  <span
                    title="參與者填寫期限到後開放"
                    className="cursor-not-allowed rounded-lg bg-white/60 px-4 py-2.5 text-sm font-semibold text-[#8ba89f]"
                  >
                    議前準備
                  </span>
                )}
              </div>
            </>
          ) : (
            <>
              <h2 className="mt-3 text-xl font-semibold">還沒有待處理會議</h2>
              <p className="mt-2 text-sm text-[#4c6e65]">
                從團隊開始建立一場會議，設定議程與會前準備期限。
              </p>
              <Link
                href="/workspaces"
                className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[#087e6d]"
              >
                前往團隊 <IconArrowRight size={16} />
              </Link>
            </>
          )}
        </div>
        <Link
          href="/workspaces"
          className="rounded-2xl border border-[#e6e6e3] bg-white p-6 transition hover:border-[#9ddbc8] hover:shadow-sm"
        >
          <IconUsersGroup className="text-[#0f9f8a]" size={23} />
          <p className="mt-6 text-sm text-[#787774]">我的團隊</p>
          <p className="mt-1 text-3xl font-semibold">{teams.length}</p>
          <p className="mt-2 text-sm text-[#087e6d]">
            管理成員、會議與共用資料{" "}
            <IconArrowRight className="inline" size={15} />
          </p>
        </Link>
      </section>
      <section className="mt-10">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold">近期會議</h2>
            <p className="mt-1 text-sm text-[#787774]">
              優先顯示尚需準備或正在進行的會議。
            </p>
          </div>
          <Link
            href="/workspaces"
            className="text-sm font-medium text-[#087e6d]"
          >
            依團隊查看
          </Link>
        </div>
        {activeMeetings.length ? (
          <div className="mt-5 grid gap-3">
            {activeMeetings.slice(0, 6).map((meeting) => (
              <article
                key={meeting.id}
                className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-[#e6e6e3] bg-white p-5"
              >
                <div>
                  <h3 className="font-semibold">{meeting.title}</h3>
                  <p className="mt-2 text-sm text-[#787774]">
                    {teamName(meeting.team_id)} ·{" "}
                    {meeting.scheduled_at
                      ? new Date(meeting.scheduled_at).toLocaleString("zh-TW")
                      : "尚未設定時間"}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-semibold ${statusClass[meeting.status] ?? "bg-slate-100 text-slate-700"}`}
                  >
                    {statusLabel[meeting.status] ?? meeting.status}
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
                  議前準備
                    </Link>
                  ) : (
                    <span
                      title="參與者填寫期限到後開放"
                      className="cursor-not-allowed rounded-lg bg-[#e6e6e3] px-3 py-2 text-sm font-semibold text-[#9b9a97]"
                    >
                  議前準備
                    </span>
                  )}
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="mt-5 rounded-2xl border border-dashed border-[#d8d8d5] bg-white p-10 text-center">
            <p className="font-medium">目前沒有待處理會議</p>
            <p className="mt-2 text-sm text-[#787774]">
              先選擇一個團隊，建立下一場需要討論的會議。
            </p>
          </div>
        )}
      </section>
    </AppShell>
  );
}
