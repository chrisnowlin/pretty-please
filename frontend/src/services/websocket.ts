export interface ProgressMessage {
  type: 'progress' | 'complete' | 'error' | 'ping';
  progress?: number;
  current_file?: string;
  processed_files?: number;
  error?: string;
  errors?: Array<{ file: string; error: string }>;
}

export type ProgressCallback = (message: ProgressMessage) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;

  connect(taskId: string, onMessage: ProgressCallback, onError?: (error: Error) => void): void {
    // Always connect WebSocket directly to backend on port 8000 (bypass dev server proxy)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    const wsUrl = `${protocol}//${host}:8000/ws/progress/${taskId}`;

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        onMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onerror = (event) => {
      if (onError) {
        onError(new Error('WebSocket error'));
      }
    };

    this.ws.onclose = (event) => {
      if (this.reconnectAttempts < this.maxReconnectAttempts && event.code !== 1000) {
        this.reconnectAttempts++;
        setTimeout(() => {
          this.connect(taskId, onMessage, onError);
        }, 1000 * this.reconnectAttempts);
      }
    };
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close(1000);
      this.ws = null;
    }
  }
}
