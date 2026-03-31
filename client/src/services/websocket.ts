import type { ChatEvent } from "../types";

type EventHandler = (event: ChatEvent) => void;

const WS_BASE = "ws://127.0.0.1:9800/api";

export class GraphSocket {
  private ws: WebSocket | null = null;
  private handlers = new Set<EventHandler>();

  connect(
    sessionId: string,
    options?: {
      initial?: Record<string, unknown>;
      onEvent?: EventHandler;
    },
  ) {
    this.disconnect();
    this.handlers.clear();
    if (options?.onEvent) {
      this.handlers.add(options.onEvent);
    }

    const url = `${WS_BASE}/ws/graph/${sessionId}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      if (options?.initial && this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify(options.initial));
      }
    };

    this.ws.onmessage = (e) => {
      try {
        const event: ChatEvent = JSON.parse(e.data);
        this.handlers.forEach((h) => h(event));
      } catch {
        console.error("[GraphSocket] Failed to parse message:", e.data);
      }
    };

    this.ws.onclose = () => {
      this.ws = null;
    };

    this.ws.onerror = (err) => {
      console.error("[GraphSocket] Error:", err);
    };
  }

  send(data: Record<string, unknown>) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  subscribe(handler: EventHandler): () => void {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }

  disconnect() {
    this.ws?.close();
    this.ws = null;
  }

  get connected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const graphSocket = new GraphSocket();
