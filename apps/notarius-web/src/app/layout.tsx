import type { Metadata } from "next";
import "./globals.css";
import { QueryProvider } from "@/providers/QueryProvider";
import { ThemeProvider } from "@/providers/ThemeProvider";
import { ErrorBoundary } from "@/components/common/ErrorBoundary";
import { ApiErrorToast } from "@/components/common/ApiErrorToast";

export const metadata: Metadata = {
  title: "Notarius - Cartório Digital",
  description: "AI-powered notary system for Brazil",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body className="antialiased">
        <ErrorBoundary>
          <ThemeProvider>
            <QueryProvider>
              <ApiErrorToast />
              {children}
            </QueryProvider>
          </ThemeProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
