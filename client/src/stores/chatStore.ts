import { create } from "zustand";
import type { ChatEvent } from "../types";
import { graphSocket } from "../services/websocket";

interface ChatStore {
  events: ChatEvent[];
  currentPhase: string | null;
  isRunning: boolean;
  isPaused: boolean;
  isInterrupted: boolean;
  isCollecting: boolean;

  addEvent: (event: ChatEvent) => void;
  clearEvents: () => void;
  startGraph: (taskId: string, userRequest?: string) => void;
  pauseGraph: () => void;
  resumeGraph: (feedback: string) => void;
  startCollect: (taskId: string) => void;
  sendCollectMessage: (content: string) => void;
  confirmStart: (taskId: string) => void;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  events: [],
  currentPhase: null,
  isRunning: false,
  isPaused: false,
  isInterrupted: false,
  isCollecting: false,

  addEvent: (event) =>
    set((s) => {
      const isPaused =
        event.type === "phase_complete" && event.content === "项目已暂停"
          ? true
          : s.isPaused;
      const isRunning =
        event.type === "task_complete" || event.type === "error"
          ? false
          : isPaused
            ? false
            : s.isRunning;
      const isCollecting =
        event.type === "task_complete" || event.type === "error"
          ? false
          : s.isCollecting;
      return {
        events: [...s.events, event],
        currentPhase:
          event.type === "phase_start"
            ? (event.phase ?? s.currentPhase)
            : s.currentPhase,
        isInterrupted: event.type === "hitl_interrupt",
        isRunning,
        isPaused,
        isCollecting,
      };
    }),

  clearEvents: () =>
    set({
      events: [],
      currentPhase: null,
      isRunning: false,
      isPaused: false,
      isInterrupted: false,
      isCollecting: false,
    }),

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
    set({ isRunning: true, isPaused: false, isInterrupted: false, events: [] });
  },

  pauseGraph: () => {
    graphSocket.send({ action: "pause" });
  },

  resumeGraph: (feedback) => {
    graphSocket.send({ action: "resume", feedback });
    set({ isInterrupted: false, isPaused: false, isRunning: true });
  },

  startCollect: (taskId) => {
    const sessionId = crypto.randomUUID();
    graphSocket.connect(sessionId, {
      initial: {
        action: "collect",
        task_id: taskId,
      },
      onEvent: (event) => get().addEvent(event),
    });
    set({ isCollecting: true, isRunning: false, isPaused: false, isInterrupted: false, events: [] });
  },

  sendCollectMessage: (content) => {
    get().addEvent({
      type: "user_response",
      timestamp: new Date().toISOString(),
      content,
    });
    graphSocket.send({ action: "collect", content });
  },

  confirmStart: (taskId) => {
    graphSocket.send({ action: "confirm_start", task_id: taskId });
    set({ isCollecting: false, isRunning: true });
  },
}));
