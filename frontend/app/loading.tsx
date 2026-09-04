export default function Loading() {
  return <main className="min-h-screen bg-[#fbfbfa] p-8"><div className="mx-auto max-w-6xl animate-pulse space-y-6"><div className="h-8 w-32 rounded bg-[#e9e9e7]" /><div className="h-12 w-72 rounded bg-[#e9e9e7]" /><div className="grid gap-4 sm:grid-cols-3">{Array.from({ length: 3 }).map((_, index) => <div key={index} className="h-36 rounded-2xl bg-[#efefed]" />)}</div></div></main>;
}
