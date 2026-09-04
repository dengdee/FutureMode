import Link from "next/link";
import type { ReactNode } from "react";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      <header className="border-b border-black/5 bg-[var(--surface)]">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link href="/dashboard" className="font-semibold tracking-tight">Proximate</Link>
          <nav className="flex gap-4 text-sm text-[var(--muted)]">
            <Link href="/dashboard" className="hover:text-[var(--foreground)]">Dashboard</Link>
            <Link href="/meetings/new" className="hover:text-[var(--foreground)]">建立會議</Link>
            <Link href="/memory" className="hover:text-[var(--foreground)]">Team Memory</Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-10">{children}</main>
    </div>
  );
}
