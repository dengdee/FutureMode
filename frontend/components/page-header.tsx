import type { ReactNode } from "react";
import { IconArrowLeft } from "@tabler/icons-react";
import Link from "next/link";

type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description: string;
  actions?: ReactNode;
  backHref?: string;
  backLabel?: string;
};

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  backHref,
  backLabel = "返回上一頁",
}: PageHeaderProps) {
  return (
    <div>
      {backHref && (
        <Link
          href={backHref}
          className="mb-5 inline-flex items-center gap-1 text-sm text-[#787774] hover:text-[#1f1f1f]"
        >
          <IconArrowLeft size={17} />
          {backLabel}
        </Link>
      )}
      <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
        <div>
          {eyebrow && (
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[var(--accent)]">
              {eyebrow}
            </p>
          )}
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-[#1f1f1f] sm:text-4xl">
            {title}
          </h1>
          <p className="mt-2 max-w-2xl text-[#787774]">{description}</p>
        </div>
        {actions && (
          <div className="flex shrink-0 flex-wrap gap-2">{actions}</div>
        )}
      </div>
    </div>
  );
}
