"use client";

import { useEffect, useCallback, useState } from "react";
import { useWebSocket } from "@/providers/websocket-provider";

export function useWebSocketSubscription<T = unknown>(
  channel: string,
  eventType: string,
  handler: (data: T) => void
) {
  const { client } = useWebSocket();

  const stableHandler = useCallback(handler, [handler]);

  useEffect(() => {
    if (!client) return;

    client.subscribe(channel);
    client.on(eventType, stableHandler as (data: unknown) => void);

    return () => {
      client.unsubscribe(channel);
      client.off(eventType, stableHandler as (data: unknown) => void);
    };
  }, [client, channel, eventType, stableHandler]);
}

export function useWebSocketChannel<T = unknown>(
  channel: string,
  eventType: string
): { data: T | null; messages: T[] } {
  const [data, setData] = useState<T | null>(null);
  const [messages, setMessages] = useState<T[]>([]);

  const handler = useCallback((incoming: T) => {
    setData(incoming);
    setMessages((prev) => [incoming, ...prev].slice(0, 100));
  }, []);

  useWebSocketSubscription<T>(channel, eventType, handler);

  return { data, messages };
}
