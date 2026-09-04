"use client";

import {
  IconBook,
  IconBriefcase,
  IconChevronRight,
  IconLayoutDashboard,
  IconLayoutSidebarLeftCollapse,
  IconLayoutSidebarLeftExpand,
  IconLogout,
  IconMenu2,
  IconSettings,
  IconX,
} from "@tabler/icons-react";
import { useGSAP } from "@gsap/react";
import { gsap } from "gsap";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { Tooltip } from "./ui/tooltip";

gsap.registerPlugin(useGSAP);

const navigation = [
  [IconLayoutDashboard, "Dashboard", "/dashboard"],
  [IconBriefcase, "工作區", "/workspaces"],
  [IconBook, "Team Memory", "/memory"],
  [IconSettings, "設定", "/settings"],
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const shellRef = useRef<HTMLDivElement>(null);
  const sidebarRef = useRef<HTMLElement>(null);
  const backdropRef = useRef<HTMLButtonElement>(null);
  const menuTriggerRef = useRef<HTMLButtonElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const contentRef = useRef<HTMLElement>(null);
  const pathname = usePathname();
  const breadcrumb =
    pathname === "/dashboard"
      ? "Dashboard"
      : pathname === "/workspaces"
        ? "Workspaces"
        : pathname.startsWith("/meetings")
          ? "Meetings"
          : pathname === "/memory"
            ? "Team Memory"
            : "Settings";

  useGSAP(
    () => {
      const sidebar = sidebarRef.current;
      const backdrop = backdropRef.current;
      if (!sidebar || !backdrop) return;

      const reducedMotion = window.matchMedia(
        "(prefers-reduced-motion: reduce)",
      ).matches;
      const duration = reducedMotion ? 0 : 0.24;

      if (window.matchMedia("(min-width: 768px)").matches) {
        gsap.set(backdrop, { autoAlpha: 0, pointerEvents: "none" });
        gsap.to(sidebar, {
          width: sidebarCollapsed ? 68 : 240,
          x: 0,
          duration,
          ease: "power2.out",
        });
        return;
      }

      gsap.to(sidebar, {
        x: sidebarOpen ? 0 : "-100%",
        duration,
        ease: "power2.out",
      });
      if (sidebarOpen) {
        gsap.set(backdrop, { pointerEvents: "auto" });
        gsap.to(backdrop, { autoAlpha: 1, duration, ease: "power1.out" });
      } else {
        gsap.to(backdrop, {
          autoAlpha: 0,
          duration,
          ease: "power1.out",
          onComplete: () => gsap.set(backdrop, { pointerEvents: "none" }),
        });
      }
    },
    {
      dependencies: [sidebarCollapsed, sidebarOpen],
      scope: shellRef,
      revertOnUpdate: true,
    },
  );

  useGSAP(
    () => {
      const content = contentRef.current;
      if (
        !content ||
        window.matchMedia("(prefers-reduced-motion: reduce)").matches
      )
        return;
      gsap.fromTo(
        content,
        { autoAlpha: 0, y: 8 },
        { autoAlpha: 1, y: 0, duration: 0.28, ease: "power2.out" },
      );
    },
    { dependencies: [pathname], scope: shellRef },
  );

  useEffect(() => {
    if (!sidebarOpen) return;

    previousFocusRef.current =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setSidebarOpen(false);
    };

    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      previousFocusRef.current?.focus();
    };
  }, [sidebarOpen]);

  return (
    <div
      ref={shellRef}
      className="min-h-screen bg-[#fbfbfa] text-[#1f1f1f] md:flex"
    >
      <button
        ref={backdropRef}
        type="button"
        aria-label="關閉導覽"
        onClick={() => setSidebarOpen(false)}
        className="pointer-events-none fixed inset-0 z-30 bg-black/35 opacity-0 md:hidden"
      />
      <aside
        ref={sidebarRef}
        className={`fixed inset-y-0 left-0 z-40 flex w-[250px] -translate-x-full flex-col overflow-y-auto border-r border-[#e6e6e3] bg-[#f7f7f5] md:sticky md:top-0 md:z-auto md:h-screen md:w-60 md:translate-x-0 ${sidebarCollapsed ? "md:w-[68px]" : ""}`}
      >
        <div
          className={`relative flex items-center justify-between px-5 py-5 ${sidebarCollapsed ? "md:px-3 md:justify-center" : ""}`}
        >
          <div className={sidebarCollapsed ? "md:hidden" : ""}>
            <Link
              href="/dashboard"
              onClick={() => setSidebarOpen(false)}
              className="text-base font-semibold tracking-tight"
            >
              Proximate
            </Link>
            <span className="mt-1 block text-xs text-[#9b9a97]">
              AI meeting workspace
            </span>
          </div>
          <Tooltip content={sidebarCollapsed ? "展開側邊欄" : "收合側邊欄"}>
            <button
              type="button"
              aria-label={sidebarCollapsed ? "展開側邊欄" : "收合側邊欄"}
              onClick={() => setSidebarCollapsed((collapsed) => !collapsed)}
              className={`absolute top-3 hidden h-9 w-9 items-center justify-center rounded-md text-[#787774] hover:text-[#1f1f1f] md:inline-flex ${sidebarCollapsed ? "md:left-1/2 md:right-auto md:-translate-x-1/2" : "md:right-2"}`}
            >
              {sidebarCollapsed ? (
                <IconLayoutSidebarLeftExpand size={20} stroke={1.8} />
              ) : (
                <IconLayoutSidebarLeftCollapse size={20} stroke={1.8} />
              )}
            </button>
          </Tooltip>
          <Tooltip content="關閉導覽">
            <button
              type="button"
              aria-label="關閉導覽"
              onClick={() => setSidebarOpen(false)}
              className="rounded p-1 text-[#787774] hover:bg-[#e9e9e7] md:hidden"
            >
              <IconX size={20} stroke={1.8} />
            </button>
          </Tooltip>
        </div>
        <nav
          aria-label="主要導覽"
          className="flex-1 space-y-2 px-3 pt-2 text-sm"
        >
          {navigation.map(([Icon, label, href]) => {
            const isActive =
              href === "/dashboard"
                ? pathname === href
                : pathname.startsWith(href);
            return (
              <Tooltip key={href} content={label}>
                <Link
                  href={href}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center gap-3 rounded-md px-3 py-2.5 ${sidebarCollapsed ? "md:justify-center md:px-2" : ""} ${isActive ? "bg-[#e9e9e7] font-medium" : "text-[#787774] hover:bg-[#e9e9e7] hover:text-[#1f1f1f]"}`}
                >
                  <Icon size={20} stroke={1.8} className="shrink-0" />
                  <span className={sidebarCollapsed ? "md:hidden" : ""}>
                    {label}
                  </span>
                </Link>
              </Tooltip>
            );
          })}
        </nav>
        <div
          className={`border-t border-[#e6e6e3] px-4 py-4 ${sidebarCollapsed ? "md:px-2" : ""}`}
        >
          <div
            className={`flex items-center justify-between gap-3 ${sidebarCollapsed ? "flex-col md:flex-row md:justify-center" : ""}`}
          >
            <div className={`flex items-center gap-2 ${sidebarCollapsed ? "md:flex-col md:gap-0" : ""}`}>
              <span
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#0f9f8a] text-xs font-semibold text-white"
                title="Proximate"
              >
                YC
              </span>
              <div className={sidebarCollapsed ? "md:hidden" : ""}>
                <p className="text-sm font-medium">Proximate</p>
                <p className="text-xs text-[#9b9a97]">Admin</p>
              </div>
            </div>
            <Tooltip content="登出">
              <Link
                href="/sign-in"
                aria-label="登出"
                className="ml-auto rounded-md p-2 text-[#787774] hover:bg-[#e9e9e7] hover:text-[#1f1f1f] md:ml-0"
              >
                <IconLogout size={19} stroke={1.8} />
              </Link>
            </Tooltip>
          </div>
        </div>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col md:h-screen">
        <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-[#e6e6e3] bg-[#fbfbfa]/95 px-4 backdrop-blur">
          <Tooltip content="開啟導覽">
            <button
              ref={menuTriggerRef}
              type="button"
              aria-label="開啟或收合導覽"
              aria-expanded={sidebarOpen}
              onClick={() => setSidebarOpen((open) => !open)}
              className="rounded-md p-2 text-[#4b4b48] hover:bg-[#e9e9e7] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#0f9f8a] md:hidden"
            >
              <IconMenu2 size={20} stroke={1.8} />
            </button>
          </Tooltip>
          <div className="flex items-center gap-2 text-sm">
            <span className="hidden text-[#9b9a97] md:inline">Workspace</span>
            <IconChevronRight
              size={15}
              stroke={1.8}
              className="hidden text-[#b5b5b1] md:inline"
            />
            <span className="font-medium">{breadcrumb}</span>
          </div>
        </header>
        <main
          ref={contentRef}
          className="min-w-0 flex-1 px-5 py-8 sm:px-8 md:overflow-y-auto md:px-10 md:py-10"
        >
          {children}
        </main>
      </div>
    </div>
  );
}
