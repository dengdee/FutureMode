import Link from "next/link";
import { AppShell } from "../../components/app-shell";

const meetings = [
  { id: "demo", title: "Q3 產品策略會議", status: "準備中", date: "今天 14:00", participants: 6 },
  { id: "review-demo", title: "團隊週會", status: "待確認", date: "昨天 10:30", participants: 4 },
];

export default function DashboardPage() {
  return (
    <AppShell>
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--accent)]">Workspace</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">你的會議</h1>
          <p className="mt-2 text-[var(--muted)]">集中查看會前準備、即時討論與會後決策。</p>
        </div>
        <Link href="/meetings/new" className="rounded-xl bg-[var(--accent)] px-4 py-2.5 text-center text-sm font-semibold text-white">建立會議</Link>
      </div>
      <section className="mt-8 grid gap-4 sm:grid-cols-3">
        {[['進行中會議', '0'], ['待確認共識', '2'], ['我的行動項目', '4']].map(([label, value]) => (
          <div key={label} className="rounded-2xl bg-[var(--surface)] p-5 ring-1 ring-black/5"><p className="text-sm text-[var(--muted)]">{label}</p><p className="mt-2 text-3xl font-semibold">{value}</p></div>
        ))}
      </section>
      <section className="mt-10">
        <div className="mb-4 flex items-center justify-between"><h2 className="text-xl font-semibold">近期會議</h2><span className="text-sm text-[var(--muted)]">Mock Data</span></div>
        <div className="grid gap-4 md:grid-cols-2">
          {meetings.map((meeting) => (
            <Link key={meeting.id} href={`/meetings/${meeting.id}/prepare`} className="rounded-2xl bg-[var(--surface)] p-5 ring-1 ring-black/5 transition hover:-translate-y-0.5 hover:ring-[var(--accent)]">
              <div className="flex items-start justify-between gap-4"><h3 className="font-semibold">{meeting.title}</h3><span className="rounded-full bg-[var(--background)] px-3 py-1 text-xs text-[var(--accent)]">{meeting.status}</span></div>
              <p className="mt-4 text-sm text-[var(--muted)]">{meeting.date} · {meeting.participants} 位參與者</p>
            </Link>
          ))}
        </div>
      </section>
    </AppShell>
  );
}
