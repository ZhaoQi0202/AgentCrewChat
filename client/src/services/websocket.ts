import type { ChatEvent } from "../types";

type EventHandler = (event: ChatEvent) => void;

const WS_BASE = "ws://127.0.0.1:9800/api";
const MAX_RECONNECT = 3;

export class GraphSocket {
  private ws: WebSocket | null = null;
  private handlers = new Set<EventHandler>();
  private _sessionId: string | null = null;
  private _reconnectCount = 0;
  private _intentionalClose = false;

  connect(
    sessionId: string,
    options?: {
      initial?: Record<string, unknown>;
      onEvent?: EventHandler;
    },
  ) {
    this._intentionalClose = false;
    this._reconnectCount = 0;
    this._sessionId = sessionId;

    // 先关掉旧连接，但要捕获旧 ws 引用，避免其 onclose 覆盖新 ws
    const oldWs = this.ws;
    if (oldWs) {
      oldWs.onclose = null;
      oldWs.onmessage = null;
      oldWs.onerror = null;
      oldWs.close();
    }
    this.handlers.clear();
    if (options?.onEvent) {
      this.handlers.add(options.onEvent);
    }

    this._doConnect(sessionId, options);
  }

  private _doConnect(
    sessionId: string,
    options?: {
      initial?: Record<string, unknown>;
      onEvent?: EventHandler;
    },
  ) {
    const url = `${WS_BASE}/ws/graph/${sessionId}`;
    const ws = new WebSocket(url);
    this.ws = ws;

    ws.onopen = () => {
      this._reconnectCount = 0;
      if (options?.initial && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(options.initial));
      }
    };

    ws.onmessage = (e) => {
      try {
        const event: ChatEvent = JSON.parse(e.data);
        this.handlers.forEach((h) => h(event));
      } catch {
        console.error("[GraphSocket] Failed to parse message:", e.data);
      }
    };

    ws.onclose = () => {
      if (this.ws === ws) {
        this.ws = null;
        if (!this._intentionalClose) {
          this._tryReconnect(sessionId, options);
        }
      }
    };

    ws.onerror = (err) => {
      console.error("[GraphSocket] Error:", err);
    };
  }

  private _tryReconnect(
    sessionId: string,
    options?: {
      initial?: Record<string, unknown>;
      onEvent?: EventHandler;
    },
  ) {
    if (this._reconnectCount >= MAX_RECONNECT) {
      console.warn("[GraphSocket] Max reconnect attempts reached");
      return;
    }

    this._reconnectCount++;
    const delay = Math.pow(2, this._reconnectCount) * 1000; // 2s, 4s, 8s
    console.log(
      `[GraphSocket] Reconnecting in ${delay}ms (attempt ${this._reconnectCount}/${MAX_RECONNECT})`,
    );

    setTimeout(() => {
      this._doConnect(sessionId, {
        initial: { action: "reconnect", session_id: sessionId },
        onEvent: options?.onEvent,
      });
    }, delay);
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
    this._intentionalClose = true;
    const ws = this.ws;
    if (ws) {
      ws.onclose = null;
      ws.onmessage = null;
      ws.onerror = null;
      ws.close();
      this.ws = null;
    }
  }

  get connected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const graphSocket = new GraphSocket();
