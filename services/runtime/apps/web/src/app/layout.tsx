import "./globals.css";
import type { ReactNode } from "react";
import { WorkspaceProvider } from '@/components/workspace/WorkspaceProvider';

export const metadata = {
  title: "PFIOS Console",
  description: "Personal Financial Intelligence Operating System"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <WorkspaceProvider>{children}</WorkspaceProvider>
      </body>
    </html>
  );
}
