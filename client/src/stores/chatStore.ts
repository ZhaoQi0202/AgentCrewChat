import { create } from "zustand";
import type { ChatEvent } from "../types";
import { graphSocket } from "../services/websocket";

interface ChatStore {
  events: ChatEvent[];
  currentPhase: string | null;
  isRunning: boolean;
  isInterrupted: boolean;
  isPaused: boolean;
  isCollecting: boolean;
  isConsultantThinking: boolean;

  addEvent: (event: ChatEvent) => void;
  clearEvents: () => void;
  startCollect: (taskId: string) => void;
  sendCollectMessage: (msg: string) => void;
  startGraph: (taskId: string, userRequest?: string) => void;
  pauseGraph: () => void;
  resumeGraph: (feedback: string) => void;
  restartProject: (taskId: string) => void;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  events: [],
  currentPhase: null,
  isRunning: false,
  isInterrupted: false,
  isPaused: false,
  isCollecting: false,
  isConsultantThinking: false,

  addEvent: (event) =>
    set((s) => {
      const isConsultantThinking =
        event.type === "agent_thinking" && s.isCollecting
          ? true
          : event.type === "agent_output" && s.isCollecting
            ? false
            : s.isConsultantThinking;

      const architectJoin =
        event.type === "agent_join" && event.agent === "architect";

      return {
        events: [...s.events, event],
        currentPhase:
          event.type === "phase_start" || event.type === "agent_join"
            ? (event.phase ?? s.currentPhase)
            : s.currentPhase,
        isInterrupted: event.type === "hitl_interrupt",
        isRunning: architectJoin
          ? true
          : event.type === "task_complete" || event.type === "error"
            ? false
            : s.isRunning,
        isCollecting: architectJoin ? false : s.isCollecting,
        isConsultantThinking,
      };
    }),

  clearEvents: () =>
    set({
      events: [],
      currentPhase: null,
      isRunning: false,
      isInterrupted: false,
      isPaused: false,
      isCollecting: false,
      isConsultantThinking: false,
    }),

  startCollect: (taskId: string) => {
    const sessionId = crypto.randomUUID();
    set({
      isCollecting: true,
      isConsultantThinking: false,
      isPaused: false,
      isRunning: false,
      isInterrupted: false,
      events: [],
    });
    graphSocket.connect(sessionId, {
      initial: { action: "collect", task_id: taskId, message: "" },
      onEvent: (event) => get().addEvent(event),
    });
  },

  sendCollectMessage: (msg) => {
    const trimmed = msg.trim();
    if (!trimmed) return;
    get().addEvent({
      type: "user_response",
      timestamp: new Date().toISOString(),
      content: trimmed,
    });
    graphSocket.send({
      action: "collect",
      task_id: "",
      message: trimmed,
    });
  },

  startGraph: (taskId, userRequest) => {
    const sessionId = crypto.randomUUID();
    graphSocket.connect(sessionId, {
      initial: {
        action: "start",
        task_id: taskId,
        user_request: userRequest || taskId,
      },
      onEvent: (event) => get().addEvent(event),
    });
    set({
      isRunning: true,
      isInterrupted: false,
      isPaused: false,
      isCollecting: false,
      events: [],
    });
  },

  pauseGraph: () => {
    set({ isPaused: true });
  },

  resumeGraph: (feedback) => {
    graphSocket.send({ action: "resume", feedback });
    set({ isInterrupted: false, isPaused: false });
  },

  restartProject: (taskId: string) => {
    graphSocket.disconnect();
    get().clearEvents();
    get().startCollect(taskId);
  },
}));
