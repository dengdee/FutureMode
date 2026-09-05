"use client";

import {
  IconUsersGroup,
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
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { Tooltip } from "./ui/tooltip";
import { authClient } from "../lib/auth/client";
import { InvitationInbox } from "./invitation-inbox";
import { getCurrentUser } from "../lib/api/me";
import { listTeamMembers, listTeams } from "../lib/api/teams";

gsap.registerPlugin(useGSAP, ScrollTrigger);

const navigation = [
  [IconLayoutDashboard, "儀表板", "/dashboard"],
  [IconUsersGroup, "團隊", "/teams"],
  [IconSettings, "設定", "/settings"],
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { data: authSession } = authClient.useSession();
  const [apiProfileName, setApiProfileName] = useState<string | null>(null);
  useEffect(() => {
    const refreshProfile = async (event?: Event) => {
      const updatedName = event instanceof CustomEvent && typeof event.detail === "string" ? event.detail : window.localStorage.getItem("proximate:profile-name");
      if (updatedName) setApiProfileName(updatedName);
      try {
        const currentUser = await getCurrentUser();
        const teams = await listTeams();
        const memberLists = await Promise.all(teams.teams.map((team) => listTeamMembers(team.id)));
        const currentMember = memberLists.flatMap((result) => result.members).find((member) => member.external_id === currentUser.id);
        const currentName = currentMember?.display_name ?? currentUser.display_name ?? updatedName;
        if (currentName) { window.localStorage.setItem("proximate:profile-name", currentName); setApiProfileName(currentName); }
      } catch { /* Keep the authenticated or cached label if the profile lookup is unavailable. */ }
    };
    refreshProfile();
    window.addEventListener("proximate:profile-updated", refreshProfile);
    return () => window.removeEventListener("proximate:profile-updated", refreshProfile);
  }, [authSession?.user?.id]);
  const profileName = apiProfileName ?? authSession?.user?.name ?? authSession?.user?.email ?? "Proximate";
  const profileInitial = Array.from(profileName.trim())[0]?.toUpperCase() ?? "P";
  const shellRef = useRef<HTMLDivElement>(null);
  const sidebarRef = useRef<HTMLElement>(null);
  const backdropRef = useRef<HTMLButtonElement>(null);
  const menuTriggerRef = useRef<HTMLButtonElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const contentRef = useRef<HTMLElement>(null);
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const router = useRouter();
  const meetingPhase = pathname.startsWith("/meetings/")
    ? ({ new: "建立會議", prepare: "議前討論", "pre-meeting-summary": "議前整理", "audio-setup": "收音設定", addon: "Meet Add-on", live: "即時會議", review: "會後回顧" } as Record<string, string>)[pathname.split("/").at(-1) ?? ""]
    : undefined;
  const memoryScope = searchParams.get("scope");
  const breadcrumbGroup = meetingPhase
    ? pathname === "/meetings/new" ? "團隊" : "會議"
    : pathname === "/memory" ? "團隊" : undefined;
  const breadcrumb = meetingPhase ?? (pathname === "/memory"
    ? memoryScope === "meeting" ? "會議文件" : memoryScope === "shared" ? "共用文件" : "團隊記憶"
    : ({ "/dashboard": "工作總覽", "/teams": "團隊", "/workspaces": "團隊", "/settings": "設定" } as Record<string, string>)[pathname] ?? "頁面");

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

  useGSAP(() => {
    const content = contentRef.current;
    if (!content || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const sections = Array.from(content.children);
    if (!sections.length) return;
    gsap.set(sections, { autoAlpha: 0, y: 18 });
    ScrollTrigger.batch(sections, {
      scroller: content,
      start: "top 88%",
      once: true,
      onEnter: (elements) => gsap.to(elements, { autoAlpha: 1, y: 0, duration: 0.42, stagger: 0.08, ease: "power2.out", overwrite: "auto" }),
    });
    ScrollTrigger.refresh();
  }, { dependencies: [pathname], scope: shellRef, revertOnUpdate: true });

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

  async function handleSignOut() {
    await authClient.signOut();
    router.push("/sign-in");
  }

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
        className={`fixed inset-y-0 left-0 z-40 flex w-[min(250px,calc(100vw-16px))] -translate-x-full flex-col overflow-y-auto border-r border-[#e6e6e3] bg-[#f7f7f5] md:sticky md:top-0 md:z-auto md:h-screen md:w-60 md:translate-x-0 ${sidebarCollapsed ? "md:w-[68px]" : ""}`}
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
              AI meeting collaboration
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
              className="cursor-pointer rounded p-1 text-[#787774] hover:bg-[#e9e9e7] md:hidden"
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
            className={`flex items-center justify-between gap-3 ${sidebarCollapsed ? "flex-col md:justify-center md:gap-3" : ""}`}
          >
            <div className={`flex items-center gap-2 ${sidebarCollapsed ? "md:flex-col md:gap-2" : ""}`}>
              <span
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#0f9f8a] text-xs font-semibold text-white"
                title="Proximate"
              >
                {profileInitial}
              </span>
              <div className={sidebarCollapsed ? "md:hidden" : ""}>
                <p className="max-w-28 truncate text-sm font-medium">{profileName}</p>
              </div>
            </div>
            <Tooltip content="登出">
              <button
                type="button"
                aria-label="登出"
                onClick={handleSignOut}
                className="ml-auto cursor-pointer rounded-md p-2 text-[#787774] hover:bg-[#e9e9e7] hover:text-[#1f1f1f] md:ml-0"
              >
                <IconLogout size={19} stroke={1.8} />
              </button>
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
            {breadcrumbGroup && <><span className="hidden text-[#9b9a97] md:inline">{breadcrumbGroup}</span><IconChevronRight size={15} stroke={1.8} className="hidden text-[#b5b5b1] md:inline" /></>}
            <span className="font-medium">{breadcrumb}</span>
          </div>
        </header>
        <main
          ref={contentRef}
          className="min-w-0 flex-1 px-5 py-8 sm:px-8 md:overflow-y-auto md:px-10 md:py-10"
        >
          <InvitationInbox />
          {children}
        </main>
      </div>
    </div>
  );
}
