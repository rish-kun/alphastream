"use client";

import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  useCallback,
} from "react";
import { useSession } from "next-auth/react";
import { WebSocketClient } from "@/lib/ws";

interface WebSocketMessage {
  type: string;
  data: unknown;
}

interface WebSocketContextType {
  client: WebSocketClient | null;
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  sendMessage: (data: unknown) => void;
}

const WebSocketContext = createContext<WebSocketContextType>({
  client: null,
  isConnected: false,
  lastMessage: null,
  sendMessage: () => {},
});

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession();
  const clientRef = useRef<WebSocketClient | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  useEffect(() => {
    if (status !== "authenticated") {
      return;
    }

    const accessToken = (session as unknown as Record<string, unknown> | null)
      ?.accessToken as string | undefined;
    const client = new WebSocketClient("/ws/feed", accessToken ?? null);

    client.onConnect(() => {
      setIsConnected(true);
    });

    client.onDisconnect(() => {
      setIsConnected(false);
    });

    client.onMessage((type, data) => {
      setLastMessage({ type, data });
    });

    client.connect();
    clientRef.current = client;

    return () => {
      client.disconnect();
      clientRef.current = null;
      setIsConnected(false);
    };
  }, [session, status]);

  const sendMessage = useCallback((data: unknown) => {
    clientRef.current?.send(data);
  }, []);

  return (
    <WebSocketContext.Provider
      value={{
        client: clientRef.current,
        isConnected,
        lastMessage,
        sendMessage,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  return useContext(WebSocketContext);
}
