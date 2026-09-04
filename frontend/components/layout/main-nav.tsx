"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";

const items = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/meetings/new", label: "Meetings" },
  { href: "/memory", label: "Team Memory" },
  { href: "/settings", label: "Settings" },
];

export function MainNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const firstLinkRef = useRef<HTMLAnchorElement>(null);

  useEffect(() => {
    if (!open) return;
    firstLinkRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") { setOpen(false); menuButtonRef.current?.focus(); }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open]);

  return <><nav aria-label="主要導覽" className="hidden items-center gap-1 md:flex">{items.map((item) => <NavLink key={item.href} item={item} pathname={pathname} />)}</nav><div className="md:hidden"><button ref={menuButtonRef} type="button" aria-expanded={open} aria-controls="mobile-navigation" className="rounded-lg border border-[var(--border)] px-3 py-2 text-sm font-medium hover:bg-[var(--surface-muted)]" onClick={() => setOpen((value) => !value)}>選單</button>{open ? <nav id="mobile-navigation" aria-label="手機主要導覽" className="absolute inset-x-4 top-[4.5rem] z-20 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-2 shadow-lg">{items.map((item, index) => <NavLink key={item.href} item={item} pathname={pathname} linkRef={index === 0 ? firstLinkRef : undefined} onNavigate={() => setOpen(false)} />)}</nav> : null}</div></>;
}

function NavLink({ item, pathname, linkRef, onNavigate }: { item: (typeof items)[number]; pathname: string; linkRef?: React.RefObject<HTMLAnchorElement | null>; onNavigate?: () => void }) {
  const current = item.href === "/dashboard" ? pathname === item.href : pathname === item.href || pathname.startsWith(`${item.href}/`);
  return <Link ref={linkRef} href={item.href} onClick={onNavigate} aria-current={current ? "page" : undefined} className={`block rounded-lg px-3 py-2 text-sm font-medium no-underline transition ${current ? "bg-[var(--surface-muted)] text-[var(--accent-strong)]" : "text-[var(--muted)] hover:bg-[var(--surface-muted)] hover:text-[var(--foreground)]"}`}>{item.label}</Link>;
}
