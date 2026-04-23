import "./globals.css";
import type { ReactNode } from "react";
import { WorkspaceProvider } from '@/components/workspace/WorkspaceProvider';

export const metadata = {
  title: "AegisOS Console",
  description: "Governance-first AI workflow operating system console"
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
