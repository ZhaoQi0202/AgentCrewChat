import { useState } from "react";
import { IconSidebar, type NavPage } from "./components/layout/IconSidebar";
import { TaskList } from "./components/layout/TaskList";
import { RightPanel } from "./components/layout/RightPanel";
import { ChatArea } from "./components/chat/ChatArea";
import { ModelsPage } from "./components/config/ModelsPage";
import { McpPage } from "./components/config/McpPage";
import { SkillsPage } from "./components/config/SkillsPage";
import { SettingsPage } from "./components/config/SettingsPage";
import { TitleBar } from "./components/layout/TitleBar";

export default function App() {
  const [page, setPage] = useState<NavPage>("tasks");
  const isTaskPage = page === "tasks";

  const mainContent: Record<NavPage, React.ReactNode> = {
    tasks: <ChatArea />,
    models: <ModelsPage />,
    mcp: <McpPage />,
    skills: <SkillsPage />,
    settings: <SettingsPage />,
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-bg-base">
      <TitleBar />
      <div className="flex flex-1 min-h-0">
        <IconSidebar activePage={page} onNavigate={setPage} />
        {isTaskPage && <TaskList />}
        <main className="flex-1 flex flex-col min-w-0">
          {mainContent[page]}
        </main>
        {isTaskPage && <RightPanel />}
      </div>
    </div>
  );
}
