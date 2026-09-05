import { IconFileText, IconHome2, IconUsersGroup } from "@tabler/icons-react";
import Link from "next/link";

type TeamSubnavProps = {
  teamId: string;
  active: "overview" | "members" | "memory";
};

const items = [
  {
    id: "overview",
    label: "團隊總覽",
    icon: IconHome2,
    href: (id: string) => `/workspaces/${id}`,
  },
  {
    id: "members",
    label: "成員與邀請",
    icon: IconUsersGroup,
    href: (id: string) => `/workspaces/${id}/members`,
  },
  {
    id: "memory",
    label: "團隊歷史文件",
    icon: IconFileText,
    href: (id: string) => `/workspaces/${id}/memory/shared`,
  },
] as const;

export function TeamSubnav({ teamId, active }: TeamSubnavProps) {
  return (
    <nav
      aria-label="團隊功能"
      className="flex flex-wrap gap-2 border-b border-[#e6e6e3] pb-5"
    >
      {items.map((item) => {
        const Icon = item.icon;
        const selected = item.id === active;
        return (
          <Link
            key={item.id}
            href={item.href(teamId)}
            aria-current={selected ? "page" : undefined}
            className={`inline-flex min-h-10 items-center gap-2 rounded-lg border px-3 py-2 text-sm font-medium transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#0f9f8a] ${selected ? "border-[#0f9f8a] bg-[#e7f7ef] text-[#087e6d]" : "border-[#dededb] bg-white text-[#5f5f5b] hover:border-[#9ddbc8] hover:bg-[#f6fbf9]"}`}
          >
            <Icon size={17} stroke={1.8} />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
