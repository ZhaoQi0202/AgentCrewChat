import {
  LayoutGrid,
  Sun,
  Plug,
  Star,
  Settings,
} from "lucide-react";
import type { ReactNode } from "react";

export type NavPage = "tasks" | "models" | "mcp" | "skills" | "settings";

interface NavItem {
  id: NavPage;
  icon: ReactNode;
  label: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: "tasks",  icon: <LayoutGrid size={20} />, label: "任务" },
  { id: "models", icon: <Sun size={20} />,        label: "模型" },
  { id: "mcp",    icon: <Plug size={20} />,       label: "MCP" },
  { id: "skills", icon: <Star size={20} />,       label: "技能" },
];

interface IconSidebarProps {
  activePage: NavPage;
  onNavigate: (page: NavPage) => void;
}

export function IconSidebar({ activePage, onNavigate }: IconSidebarProps) {
  return (
    <aside className="w-14 shrink-0 flex flex-col items-center py-3 gap-1 border-r border-border-subtle bg-bg-surface select-none">
      {/* Logo */}
      <button
        onClick={() => onNavigate("tasks")}
        className="w-9 h-9 rounded-lg gradient-brand flex items-center justify-center text-[11px] font-bold text-white mb-4 hover:opacity-90 transition-opacity"
      >
        AL
      </button>

      {/* 导航图标 */}
      {NAV_ITEMS.map((item) => (
        <SidebarIcon
          key={item.id}
          active={activePage === item.id}
          onClick={() => onNavigate(item.id)}
          label={item.label}
        >
          {item.icon}
        </SidebarIcon>
      ))}

      <div className="flex-1" />

      {/* 设置 */}
      <SidebarIcon
        active={activePage === "settings"}
        onClick={() => onNavigate("settings")}
        label="设置"
      >
        <Settings size={20} />
      </SidebarIcon>
    </aside>
  );
}

function SidebarIcon({
  active,
  onClick,
  children,
  label,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      title={label}
      className={`
        relative w-10 h-10 flex items-center justify-center rounded-lg transition-all duration-150
        ${active
          ? "bg-brand-purple/20 text-brand-purple"
          : "text-text-muted hover:text-text-secondary hover:bg-bg-hover"
        }
      `}
    >
      {/* 左侧激活指示条 */}
      {active && (
        <span className="absolute left-0 top-2 bottom-2 w-[3px] rounded-r-full bg-brand-purple" />
      )}
      {children}
    </button>
  );
}
