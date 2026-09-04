import { Navigation } from "@/components/navigation";

export function AppShell({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <div className="app-shell">
      <Navigation />
      <div className="main">{children}</div>
    </div>
  );
}