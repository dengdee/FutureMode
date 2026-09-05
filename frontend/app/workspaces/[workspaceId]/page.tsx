"use client";

import {
  IconCalendarPlus,
  IconChevronRight,
  IconUsersGroup,
} from "@tabler/icons-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AppShell } from "../../../components/app-shell";
import { PageHeader } from "../../../components/page-header";
import { TeamSubnav } from "../../../components/team-subnav";
import { listMeetings } from "../../../lib/api/meetings";
import { listTeamMembers, listTeams } from "../../../lib/api/teams";
import type { MeetingSummary, Team, TeamMember } from "../../../types/api";

function statusLabel(status: string) {
  return (
    (
      {
        draft: "草稿",
        scheduled: "已排程",
        in_progress: "進行中",
        completed: "已結束",
        cancelled: "已取消",
      } as Record<string, string>
    )[status] ?? status
  );
}
function statusClass(status: string) {
  return (
    (
      {
        draft: "bg-slate-100 text-slate-700",
        scheduled: "bg-blue-50 text-blue-700",
        in_progress: "bg-amber-50 text-amber-800",
        completed: "bg-emerald-50 text-emerald-700",
        cancelled: "bg-rose-50 text-rose-700",
      } as Record<string, string>
    )[status] ?? "bg-slate-100 text-slate-700"
  );
}

export default function TeamOverviewPage() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const [team, setTeam] = useState<Team | null>(null);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [meetings, setMeetings] = useState<MeetingSummary[]>([]);
  const [summaryReady, setSummaryReady] = useState<Record<string, boolean>>({});
  const [meetingPage, setMeetingPage] = useState(1);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    Promise.all([listTeams(), listTeamMembers(workspaceId), listMeetings()])
      .then(([teamResult, memberResult, meetingResult]) => {
        if (!active) return;
        setTeam(
          teamResult.teams.find((item) => item.id === workspaceId) ?? null,
        );
        setMembers(memberResult.members);
        const teamMeetings = meetingResult.filter(
          (item) => item.team_id === workspaceId,
        );
        setMeetings(teamMeetings);
        setSummaryReady(
          Object.fromEntries(
            teamMeetings.map((meeting) => {
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
      .catch(
        (cause) =>
          active &&
          setError(
            cause instanceof Error ? cause.message : "無法讀取團隊資料。",
          ),
      );
    return () => {
      active = false;
    };
  }, [workspaceId]);

  const upcoming = meetings.filter((meeting) => meeting.status !== "cancelled");
  const meetingPageSize = 10;
  const meetingPageCount = Math.max(
    1,
    Math.ceil(upcoming.length / meetingPageSize),
  );
  const visibleUpcoming = upcoming.slice(
    (meetingPage - 1) * meetingPageSize,
    meetingPage * meetingPageSize,
  );

  return (
    <AppShell>
      <PageHeader
        eyebrow="Team"
        title={team?.name ?? "團隊"}
        description="集中管理成員、共用資料與本團隊的會議流程。"
        backHref="/workspaces"
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
        <TeamSubnav teamId={workspaceId} active="overview" />
      </div>
      {error ? (
        <p
          role="alert"
          className="mt-6 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          {error}
        </p>
      ) : (
        <>
          <section className="mt-6 max-w-xl">
            <Link
              href={`/workspaces/${workspaceId}/members`}
              className="rounded-2xl border border-[#e6e6e3] bg-white p-5 transition hover:border-[#9ddbc8] hover:shadow-sm"
            >
              <IconUsersGroup className="text-[#0f9f8a]" size={22} />
              <p className="mt-5 text-sm text-[#787774]">團隊成員</p>
              <p className="mt-1 text-3xl font-semibold">{members.length}</p>
              <p className="mt-2 text-sm text-[#087e6d]">
                管理角色與邀請 <IconChevronRight className="inline" size={15} />
              </p>
            </Link>
          </section>
          <section className="mt-8 rounded-2xl border border-[#e6e6e3] bg-white p-5 sm:p-6">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold">團隊會議</h2>
                <p className="mt-1 text-sm text-[#787774]">
                  查看最近會議並繼續議前準備，或建立新的會議。
                </p>
              </div>
            </div>
            {visibleUpcoming.length ? (
              <div className="mt-5 space-y-3">
                {visibleUpcoming.map((meeting) => (
                  <article
                    key={meeting.id}
                    className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[#ededeb] p-4"
                  >
                    <div className="min-w-0">
                      <h3 className="font-medium">{meeting.title}</h3>
                      <p className="mt-1 text-sm text-[#787774]">
                        {meeting.scheduled_at
                          ? new Date(meeting.scheduled_at).toLocaleString(
                              "zh-TW",
                            )
                          : "尚未設定時間"}
                      </p>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={`rounded-full px-3 py-1 text-xs font-semibold ${statusClass(meeting.status)}`}
                      >
                        {statusLabel(meeting.status)}
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
                {upcoming.length > meetingPageSize && (
                  <nav
                    aria-label="團隊會議分頁"
                    className="flex items-center justify-center gap-2 pt-3"
                  >
                    <button
                      type="button"
                      disabled={meetingPage === 1}
                      onClick={() => setMeetingPage((current) => current - 1)}
                      className="rounded-lg border border-[#dededb] px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      上一頁
                    </button>
                    <span className="px-2 text-sm text-[#787774]">
                      第 {meetingPage} / {meetingPageCount} 頁
                    </span>
                    <button
                      type="button"
                      disabled={meetingPage === meetingPageCount}
                      onClick={() => setMeetingPage((current) => current + 1)}
                      className="rounded-lg border border-[#dededb] px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      下一頁
                    </button>
                  </nav>
                )}
              </div>
            ) : (
              <div className="mt-5 rounded-xl border border-dashed border-[#d8d8d5] p-7 text-center">
                <p className="font-medium">還沒有會議</p>
                <p className="mt-1 text-sm text-[#787774]">
                  先建立一場會議，再由 AI 協助整理會前事項。
                </p>
              </div>
            )}
          </section>
        </>
      )}
    </AppShell>
  );
}
