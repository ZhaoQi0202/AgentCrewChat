import { create } from "zustand";
import type { Task } from "../types";
import { tasksApi } from "../services/api";

interface TaskStore {
  tasks: Task[];
  activeTaskId: string | null;
  loading: boolean;
  fetchTasks: () => Promise<void>;
  createTask: (name: string) => Promise<void>;
  deleteTask: (id: string) => Promise<void>;
  setActiveTask: (id: string | null) => void;
}

export const useTaskStore = create<TaskStore>((set) => ({
  tasks: [],
  activeTaskId: null,
  loading: false,

  fetchTasks: async () => {
    set({ loading: true });
    try {
      const tasks = await tasksApi.list();
      set({ tasks, loading: false });
    } catch (err) {
      console.error("Failed to fetch tasks:", err);
      set({ loading: false });
    }
  },

  createTask: async (name) => {
    const task = await tasksApi.create(name);
    set((s) => ({ tasks: [task, ...s.tasks], activeTaskId: task.id }));
  },

  deleteTask: async (id) => {
    await tasksApi.remove(id);
    set((s) => ({
      tasks: s.tasks.filter((t) => t.id !== id),
      activeTaskId: s.activeTaskId === id ? null : s.activeTaskId,
    }));
  },

  setActiveTask: (id) => set({ activeTaskId: id }),
}));
