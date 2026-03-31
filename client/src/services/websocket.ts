import type { ChatEvent } from "../types";

type EventHandler = (event: ChatEvent) => void;

export class GraphSocket {
  private ws: WebSocket | null = null;
  private handlers = new Set<EventHandler>();

  connect(sessionId: string) {
    this.disconnect();
    this.ws = new WebSocket(`ws://127.0.0.1:9800/ws/graph/${sessionId}`);

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
