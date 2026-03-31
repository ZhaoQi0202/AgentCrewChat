import { create } from "zustand";
import type { ChatEvent } from "../types";
import { graphSocket } from "../services/websocket";

interface ChatStore {
  events: ChatEvent[];
  currentPhase: string | null;
  isRunning: boolean;
  isInterrupted: boolean;

  addEvent: (event: ChatEvent) => void;
  clearEvents: () => void;
  startGraph: (taskId: string) => void;
  resumeGraph: (feedback: string) => void;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  events: [],
  currentPhase: null,
  isRunning: false,
  isInterrupted: false,

  addEvent: (event) =>
    set((s) => ({
      events: [...s.events, event],
      currentPhase:
        event.type === "phase_start"
          ? (event.phase ?? s.currentPhase)
          : s.currentPhase,
      isInterrupted: event.type === "hitl_interrupt",
      isRunning:
        event.type === "task_complete" || event.type === "error"
          ? false
          : s.isRunning,
    })),

  clearEvents: () =>
    set({
      events: [],
      currentPhase: null,
      isRunning: false,
      isInterrupted: false,
    }),

  startGraph: (taskId) => {
    const sessionId = crypto.randomUUID();
    graphSocket.connect(sessionId);
    graphSocket.subscribe((event) => get().addEvent(event));
    graphSocket.send({ action: "start", task_id: taskId });
    set({ isRunning: true, isInterrupted: false, events: [] });
  },

  resumeGraph: (feedback) => {
    graphSocket.send({ action: "resume", feedback });
    set({ isInterrupted: false });
  },
}));
