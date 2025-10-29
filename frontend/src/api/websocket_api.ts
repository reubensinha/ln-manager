import { notifications } from "@mantine/notifications";

interface NotificationPayload {
  message: string;
  type: "info" | "success" | "warning" | "error";
}

interface WebSocketMessage {
  event: string;
  payload: string;
}

class WebSocketAPI {
    private ws: WebSocket | null = null;
    private reconnectTimeout: NodeJS.Timeout | null = null;
    private reconnectAttempt= 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 3000; // 3 seconds

    connect() {
        const wsUrl = "/ws/notifications";

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log("WebSocket connection established");
                this.reconnectAttempt = 0; // Reset reconnect attempts on successful connection
                notifications.show({
                    title: "WebSocket Connected",
                    message: "Real-time notifications are now enabled.",
                    color: "green",
                    autoClose: 2000,
                });
            };

            this.ws.onmessage = (event) => {
                this.handleMessage(event.data);
            };

            this.ws.onerror = (error) => {
                console.error("WebSocket error:", error);
            };

            this.ws.onclose = () => {
                console.warn("WebSocket connection closed");
                this.attemptReconnect();
            };
        } catch (error) {
            console.error("WebSocket connection failed:", error);
            this.attemptReconnect();
        }
    }

    private handleMessage(data: string) {
        try {
            const message: WebSocketMessage = JSON.parse(data);

            if (message.event === "notification") {
                const notification: NotificationPayload = JSON.parse(message.payload);
                notifications.show({
                    title: this.getTitle(notification.type),
                    message: notification.message,
                    color: this.getColor(notification.type),
                    autoClose: 5000,
                });
            }
        } catch (error) {
            console.error("Error handling WebSocket message:", error);
        }
    }

    private getTitle(type: string): string {
        const titles: Record<string, string> = {
            info: "Info",
            success: "Success",
            warning: "Warning",
            error: "Error",
        };
        return titles[type] || "Notification";
    }

    private getColor(type: string): string {
        const colors: Record<string, string> = {
            info: "blue",
            success: "green",
            warning: "yellow",
            error: "red",
        };
        return colors[type] || "gray";
    }

    private attemptReconnect() {
        if (this.reconnectAttempt >= this.maxReconnectAttempts) {
            console.error("Max WebSocket reconnect attempts reached");
            notifications.show({
                title: "WebSocket Disconnected",
                message: "Failed to reconnect to real-time notifications.",
                color: "red",
                autoClose: false,
            });
            return;
        }

        this.reconnectAttempt++;
        console.log(`Attempting to reconnect... (${this.reconnectAttempt}/${this.maxReconnectAttempts})`);

        this.reconnectTimeout = setTimeout(() => {
            this.connect();
        }, this.reconnectDelay * this.reconnectAttempt); // Exponential backoff
    }

    disconnect() {
        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
            this.reconnectTimeout = null;
        }

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    isConnected(): boolean {
        return this.ws?.readyState === WebSocket.OPEN;
    }
}

export const websocketAPI = new WebSocketAPI();