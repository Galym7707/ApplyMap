"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useState } from "react";
import { Toaster } from "sonner";
import { OfflineIndicator } from "@/components/OfflineIndicator";
import { I18nProvider } from "@/i18n/I18nProvider";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            retry: 1,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <I18nProvider>
        <OfflineIndicator />
        {children}
      <Toaster
        position="top-right"
        toastOptions={{
          classNames: {
            toast:
              "border border-slate-200 bg-white shadow-lg rounded-xl text-sm font-medium text-slate-900",
            success:
              "border-l-4 border-l-emerald-500 bg-white text-slate-900",
            error:
              "border-l-4 border-l-red-500 bg-white text-slate-900",
            info:
              "border-l-4 border-l-navy-950 bg-white text-slate-900",
            description: "text-slate-500 text-xs",
          },
        }}
      />
        <ReactQueryDevtools initialIsOpen={false} />
      </I18nProvider>
    </QueryClientProvider>
  );
}
