import type { ReactNode } from "react";
import { MainNav } from "./layout/main-nav";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      <header className="border-b border-black/5 bg-[var(--surface)]">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-4 py-4 sm:px-6 lg:px-8">
          <a href="/dashboard" className="shrink-0 text-lg font-semibold tracking-tight text-[var(--foreground)] no-underline">Proximate</a>
          <MainNav />
          <div className="hidden items-center gap-3 md:flex">
            <span className="text-sm text-[var(--muted)]">開發期工作區</span>
            <a href="/sign-in" className="rounded-lg border border-[var(--border)] px-3 py-2 text-sm font-medium no-underline transition hover:border-[var(--accent)] hover:bg-[var(--surface-muted)]">登入</a>
          </div>
        </div>
      </header>
      <div className="mx-auto max-w-7xl px-4 py-8 pb-24 sm:px-6 lg:px-8 lg:py-10 lg:pb-10">{children}</div>
    </div>
  );
}

export function PageHeader({ eyebrow, title, description, actions }: { eyebrow?: string; title: string; description?: string; actions?: ReactNode }) {
  return <div className="flex flex-col justify-between gap-5 border-b border-[var(--border)] pb-7 sm:flex-row sm:items-end"><div>{eyebrow ? <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--accent)]">{eyebrow}</p> : null}<h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">{title}</h1>{description ? <p className="mt-3 max-w-2xl text-[var(--muted)]">{description}</p> : null}</div>{actions ? <div className="shrink-0">{actions}</div> : null}</div>;
}

export function MeetingWorkspaceHeader({ meetingId, title = "會議工作區" }: { meetingId: string; title?: string }) {
  return <div className="mb-8 flex flex-col gap-4 border-b border-[var(--border)] pb-5 sm:flex-row sm:items-center sm:justify-between"><div><a href="/dashboard" className="text-sm font-medium no-underline">← 返回 Dashboard</a><p className="mt-3 text-lg font-semibold">{title}</p><p className="text-sm text-[var(--muted)]">Meeting ID：{meetingId}</p></div><nav aria-label="會議工作區" className="flex flex-wrap gap-2 text-sm"><a href={`/meetings/${meetingId}/prepare`} className="rounded-lg px-3 py-2 font-medium no-underline hover:bg-[var(--surface-muted)]">會前準備</a><a href={`/meetings/${meetingId}/live`} className="rounded-lg px-3 py-2 font-medium no-underline hover:bg-[var(--surface-muted)]">即時會議</a><a href={`/meetings/${meetingId}/review`} className="rounded-lg px-3 py-2 font-medium no-underline hover:bg-[var(--surface-muted)]">會後回顧</a></nav></div>;
}

export function PlaceholderState({ title, description }: { title: string; description: string }) {
  return <section className="rounded-2xl border border-dashed border-[var(--border)] bg-[var(--surface)] p-8 text-center sm:p-12"><h2 className="text-xl font-semibold">{title}</h2><p className="mx-auto mt-3 max-w-lg text-[var(--muted)]">{description}</p></section>;
}
