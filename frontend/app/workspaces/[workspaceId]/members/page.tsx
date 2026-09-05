"use client";

import { IconMailPlus, IconTrash, IconUserMinus, IconUsersGroup } from "@tabler/icons-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { AppShell } from "../../../../components/app-shell";
import { PageHeader } from "../../../../components/page-header";
import { TeamSubnav } from "../../../../components/team-subnav";
import { toast } from "../../../../components/ui/toast";
import { ApiClientError } from "../../../../lib/api/client";
import { cancelInvitation, createInvitation, listInvitations, listTeamMembers, listTeams, removeTeamMember, updateTeamMember } from "../../../../lib/api/teams";
import type { Invitation, Team, TeamMember } from "../../../../types/api";

const roleLabel = (role: string) => role === "admin" ? "管理員" : "成員";

function showInvitationError(cause: unknown) {
  if (cause instanceof ApiClientError && cause.status === 401) {
    toast.error("目前登入憑證無法被 API 驗證，請重新登入後再建立邀請。", { action: { label: "重新登入", onClick: () => window.location.assign("/sign-in") } });
    return;
  }
  if (cause instanceof ApiClientError && cause.status === 404) {
    toast.error("找不到此帳號；受邀者需要先註冊並登入 Proximate 一次。");
    return;
  }
  toast.error(cause instanceof Error ? cause.message : "建立邀請失敗。");
}

export default function WorkspaceMembersPage() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const [team, setTeam] = useState<Team | null>(null);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"member" | "admin">("member");
  const [busy, setBusy] = useState(false);

  function load() {
    Promise.all([listTeams(), listTeamMembers(workspaceId)])
      .then(async ([teamResult, memberResult]) => { const current = teamResult.teams.find((item) => item.id === workspaceId) ?? null; setTeam(current); setMembers(memberResult.members); try { setInvitations(current?.role === "admin" ? await listInvitations(workspaceId) : []); } catch { setInvitations([]); } })
      .catch((cause) => toast.error(cause instanceof Error ? cause.message : "無法讀取成員資料。"));
  }
  useEffect(load, [workspaceId]);

  async function invite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!email.trim()) return;
    setBusy(true);
    try { await createInvitation(workspaceId, { email: email.trim(), role }); setEmail(""); setRole("member"); toast.success("邀請已建立；對方登入後會在站內看到邀請。"); load(); }
    catch (cause) { showInvitationError(cause); }
    finally { setBusy(false); }
  }
  async function updateRole(member: TeamMember, nextRole: string) {
    try { await updateTeamMember(workspaceId, member.user_id, { role: nextRole }); setMembers((items) => items.map((item) => item.user_id === member.user_id ? { ...item, role: nextRole } : item)); toast.success("成員角色已更新。"); }
    catch (cause) { toast.error(cause instanceof Error ? cause.message : "更新角色失敗。 "); }
  }
  async function remove(member: TeamMember) {
    if (!window.confirm(`確定移除「${member.display_name || "此成員"}」？`)) return;
    try { await removeTeamMember(workspaceId, member.user_id); setMembers((items) => items.filter((item) => item.user_id !== member.user_id)); toast.success("成員已移除。"); }
    catch (cause) { toast.error(cause instanceof Error ? cause.message : "移除成員失敗。 "); }
  }
  async function cancel(invitation: Invitation) {
    try { await cancelInvitation(workspaceId, invitation.id); setInvitations((items) => items.filter((item) => item.id !== invitation.id)); toast.success("邀請已取消。"); }
    catch (cause) { toast.error(cause instanceof Error ? cause.message : "取消邀請失敗。 "); }
  }

  return <AppShell><PageHeader eyebrow="Team" title={team ? `${team.name} 的成員` : "成員與邀請"} description="管理團隊中的角色，並以站內邀請加入新成員。" actions={<Link href={`/workspaces/${workspaceId}/meetings`} className="rounded-primary border border-[#d7e8e5] px-4 py-2.5 text-sm font-semibold text-[#087e6d]">查看團隊會議</Link>} />
    <div className="mt-8"><TeamSubnav teamId={workspaceId} active="members" /></div>
    <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]"><section className="rounded-2xl border border-[#e6e6e3] bg-white p-5 sm:p-6"><div className="flex items-center gap-2"><IconUsersGroup className="text-[#0f9f8a]" size={20} /><h2 className="font-semibold">目前成員</h2></div><div className="mt-5 space-y-3">{members.map((member) => <article key={member.user_id} className="flex flex-wrap items-center gap-3 rounded-xl border border-[#ededeb] p-4"><span className="flex h-10 w-10 items-center justify-center rounded-full bg-[#e7f7ef] font-semibold text-[#087e6d]">{Array.from(member.display_name || "成")[0]}</span><div className="min-w-0 flex-1"><h3 className="truncate font-medium">{member.display_name || "未設定名稱"}</h3><p className="mt-1 text-xs text-[#787774]">{roleLabel(member.role)}</p></div><select value={member.role} onChange={(event) => void updateRole(member, event.target.value)} className="control-primary w-auto py-2 text-xs" aria-label={`${member.display_name} 的角色`}><option value="member">成員</option><option value="admin">管理員</option></select><button type="button" onClick={() => void remove(member)} className="inline-flex items-center gap-1 rounded-lg px-2 py-2 text-xs font-medium text-red-700 hover:bg-red-50"><IconUserMinus size={15} />移除</button></article>)}{members.length === 0 && <p className="rounded-xl bg-[#f7f7f5] p-5 text-sm text-[#787774]">尚無可顯示成員。</p>}</div></section>
      <aside className="space-y-6"><section className="rounded-2xl border border-[#e6e6e3] bg-white p-5"><div className="flex items-center gap-2"><IconMailPlus className="text-[#0f9f8a]" size={20} /><h2 className="font-semibold">邀請成員</h2></div><p className="mt-2 text-sm leading-6 text-[#787774]">輸入對方登入用 Email。邀請不會寄信，對方登入後會在 Proximate 看到它。</p><form onSubmit={invite} className="mt-4 space-y-3"><label className="block text-sm font-medium">Email<input required type="email" value={email} onChange={(event) => setEmail(event.target.value)} className="control-primary mt-2" placeholder="name@example.com" /></label><label className="block text-sm font-medium">角色<select value={role} onChange={(event) => setRole(event.target.value as "member" | "admin")} className="control-primary mt-2"><option value="member">成員</option><option value="admin">管理員</option></select></label><button disabled={busy} className="w-full rounded-lg bg-[#0f9f8a] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60">{busy ? "建立中…" : "建立邀請"}</button></form></section><section className="rounded-2xl border border-[#e6e6e3] bg-white p-5"><h2 className="font-semibold">待接受邀請</h2><div className="mt-4 space-y-3">{invitations.filter((item) => item.status === "pending").map((item) => <div key={item.id} className="rounded-xl bg-[#f7f7f5] p-3"><p className="truncate text-sm font-medium">{item.email}</p><p className="mt-1 text-xs text-[#787774]">{roleLabel(item.role)} · 等待接受</p><button type="button" onClick={() => void cancel(item)} className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-red-700"><IconTrash size={14} />取消邀請</button></div>)}{!invitations.some((item) => item.status === "pending") && <p className="text-sm text-[#787774]">目前沒有待接受邀請。</p>}</div></section></aside></div>
  </AppShell>;
}
