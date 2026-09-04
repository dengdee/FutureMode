"use client";

import { IconFileText, IconFolderOpen, IconSearch, IconUpload } from "@tabler/icons-react";
import { AppShell } from "../../components/app-shell";
import { PageHeader } from "../../components/page-header";
import { useRef, useState } from "react";

export default function MemoryPage() {
  const inputRef = useRef<HTMLInputElement>(null); const [uploadedFiles, setUploadedFiles] = useState<string[]>([]); const [collection, setCollection] = useState("全部文件");
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => { const file = event.target.files?.[0]; if (file) setUploadedFiles((files) => [...files, file.name]); event.target.value = ""; };
  return <AppShell><PageHeader eyebrow="Team memory" title="團隊記憶" description="集中管理 AI 在會議中可引用的團隊文件與既有決策。" actions={<><input ref={inputRef} className="hidden" type="file" accept=".pdf,.txt" onChange={handleFileChange} /><button type="button" onClick={() => inputRef.current?.click()} className="inline-flex items-center gap-2 rounded-lg bg-[var(--accent)] px-4 py-2.5 text-sm font-semibold text-white"><IconUpload size={18} />上傳文件</button></>} />
    <div className="mt-8 grid gap-6 lg:grid-cols-[240px_minmax(0,1fr)]"><aside className="rounded-2xl border border-[#e6e6e3] bg-white p-3"><p className="px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-[#8b8b87]">Collections</p>{["全部文件", "會議決策", "產品研究", "團隊規範"].map((item) => <button type="button" onClick={() => setCollection(item)} key={item} className={`flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm ${collection === item ? "bg-[#efefec] font-medium" : "text-[#787774] hover:bg-[#f7f7f5]"}`}><IconFolderOpen size={17} />{item}</button>)}</aside><section><label className="relative block"><IconSearch className="absolute left-3 top-3 text-[#8b8b87]" size={18} /><input className="w-full rounded-xl border border-[#e0e0dd] bg-white py-2.5 pl-10 pr-3 text-sm outline-none focus:border-[var(--accent)]" placeholder="搜尋文件、決策或關鍵字" /></label><div className="mt-5 rounded-2xl border border-[#e6e6e3] bg-white p-5">{uploadedFiles.length > 0 ? <div className="space-y-2">{uploadedFiles.map((file) => <div key={file} className="flex items-center gap-3 rounded-xl bg-[#f7f7f5] px-4 py-3 text-sm"><IconFileText className="text-[var(--accent)]" size={20} /><span className="truncate">{file}</span><span className="ml-auto text-xs text-[#8b8b87]">已加入團隊記憶</span></div>)}</div> : <div className="py-12 text-center"><IconFileText className="mx-auto text-[#8b8b87]" size={32} /><h2 className="mt-4 font-semibold">還沒有可用的團隊文件</h2><p className="mx-auto mt-2 max-w-sm text-sm leading-6 text-[#787774]">首版支援 PDF 與純文字上傳。請使用右上角「上傳文件」加入團隊共用資料。</p></div>}</div></section></div>
  </AppShell>;
}
