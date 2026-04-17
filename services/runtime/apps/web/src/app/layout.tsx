import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "PFIOS Console",
  description: "Personal Financial Intelligence Operating System"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
