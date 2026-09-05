"use client";

import * as ToastPrimitive from "@radix-ui/react-toast";
import { IconCircleCheck, IconInfoCircle, IconX } from "@tabler/icons-react";
import { useEffect, useState } from "react";

type ToastVariant = "success" | "error" | "info";
type ToastDetail = { message: string; variant?: ToastVariant };
type ToastItem = ToastDetail & { id: number };
const eventName = "proximate:toast";

function show(message: string, variant: ToastVariant) {
  if (typeof window !== "undefined" && message.trim()) window.dispatchEvent(new CustomEvent<ToastDetail>(eventName, { detail: { message, variant } }));
}

export const toast = {
  success: (message: string) => show(message, "success"),
  error: (message: string) => show(message, "error"),
  message: (message: string) => show(message, "info"),
};

export function Toaster() {
  const [items, setItems] = useState<ToastItem[]>([]);
  useEffect(() => {
    const onToast = (event: Event) => {
      const detail = (event as CustomEvent<ToastDetail>).detail;
      if (!detail?.message) return;
      const item = { id: Date.now() + Math.floor(Math.random() * 1000), message: detail.message, variant: detail.variant ?? "info" };
      setItems((current) => [...current.slice(-3), item]);
    };
    window.addEventListener(eventName, onToast);
    return () => window.removeEventListener(eventName, onToast);
  }, []);
  const close = (id: number) => setItems((current) => current.filter((item) => item.id !== id));
  return <ToastPrimitive.Provider duration={5000} swipeDirection="right"><ToastPrimitive.Viewport className="fixed bottom-4 right-4 z-[100] flex max-h-screen w-[min(23rem,calc(100vw-2rem))] flex-col-reverse gap-2 outline-none">{items.map((item) => { const isError = item.variant === "error"; const isSuccess = item.variant === "success"; return <ToastPrimitive.Root key={item.id} open onOpenChange={(open) => !open && close(item.id)} role={isError ? "alert" : "status"} className={`flex items-start gap-3 rounded-xl border p-4 shadow-lg ${isError ? "border-red-200 bg-red-50 text-red-800" : isSuccess ? "border-[#9ddbc8] bg-white text-[#075f52]" : "border-[#d7e8e5] bg-white text-[#1f1f1f]"}`}><span className={`mt-0.5 shrink-0 ${isError ? "text-red-600" : "text-[#0f9f8a]"}`}>{isSuccess ? <IconCircleCheck size={19} /> : <IconInfoCircle size={19} />}</span><ToastPrimitive.Description className="min-w-0 flex-1 text-sm leading-5">{item.message}</ToastPrimitive.Description><ToastPrimitive.Close aria-label="關閉通知" className="rounded p-1 text-[#787774] hover:bg-black/5"><IconX size={16} /></ToastPrimitive.Close></ToastPrimitive.Root>; })}</ToastPrimitive.Viewport></ToastPrimitive.Provider>;
}
