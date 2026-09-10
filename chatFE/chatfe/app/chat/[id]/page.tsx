"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { apiFetch } from "@/lib/api";

type Message = {
  id: string;
  conversation_id: string;
  sender_id: string;
  content: string;
  created_at: string;
};

export default function ChatPage() {
  const { id: conversationId } = useParams<{ id: string }>();
  const { user, loading } = useAuth();
  const router = useRouter();

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState("");

  const wsRef = useRef<WebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  useEffect(() => {
    if (!user || !conversationId) return;
    apiFetch(`/conversations/${conversationId}/messages/`)
      .then((data) => setMessages(data))
      .catch((err) => setError(err.message))
      .finally(() => setFetching(false));
  }, [user, conversationId]);

  useEffect(() => {
    if (!user || !conversationId) return;

    const token = localStorage.getItem("token");
    if (!token) return;

    let ws: WebSocket | undefined;
    let heartbeatInterval: ReturnType<typeof setInterval> | undefined;
    let reconnectTimeout: ReturnType<typeof setTimeout> | undefined;
    let unmounted = false;

    function connect() {
      const wsUrl = process.env.NEXT_PUBLIC_API_URL!.replace(/^http/, "ws");
      const socket = new WebSocket(
        `${wsUrl}/ws/conversations/${conversationId}?token=${token}`
      );
      ws = socket;

      socket.onopen = () => {
        heartbeatInterval = setInterval(() => {
          if (socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({ type: "ping" }));
          }
        }, 25000);
      };

      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setMessages((prev) => [...prev, data]);
      };

      socket.onclose = () => {
        if (heartbeatInterval) clearInterval(heartbeatInterval);
        if (!unmounted) {
          reconnectTimeout = setTimeout(connect, 2000);
        }
      };

      socket.onerror = () => {
        socket.close();
      };

      wsRef.current = socket;
    }

    connect();

    return () => {
      unmounted = true;
      if (heartbeatInterval) clearInterval(heartbeatInterval);
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (wsRef.current) {
        wsRef.current.onmessage = null;
        wsRef.current.onerror = null;
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, [user, conversationId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || !wsRef.current) return;

    const optimisticMessage: Message = {
      id: crypto.randomUUID(),
      conversation_id: conversationId,
      sender_id: user!.id,
      content: input,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticMessage]);
    wsRef.current.send(JSON.stringify({ content: input }));
    setInput("");
  }

  if (loading || fetching) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-muted text-sm">Loading…</p>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="flex-1 flex flex-col max-w-2xl mx-auto w-full">
      <div className="flex items-center gap-3 px-4 py-4 border-b border-white/5">
        <button
          onClick={() => router.push("/")}
          className="text-muted hover:text-paper transition-colors text-sm"
        >
          ← Back
        </button>
        <h2 className="font-serif text-lg text-paper">Conversation</h2>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-2">
        {error && <p className="text-danger text-sm">{error}</p>}
        {messages.length === 0 && !error && (
          <p className="text-muted text-sm text-center py-8">
            No messages yet — say hello.
          </p>
        )}
        {messages.map((m) => {
          const isMine = m.sender_id === user.id;
          return (
            <div
              key={m.id}
              className={`flex ${isMine ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-xs px-4 py-2 text-sm ${
                  isMine
                    ? "bg-amber text-ink rounded-2xl rounded-br-sm"
                    : "bg-panel border border-white/10 text-paper rounded-2xl rounded-bl-sm"
                }`}
              >
                <p>{m.content}</p>
                <p
                  className={`text-[10px] mt-1 ${
                    isMine ? "text-ink/60" : "text-muted"
                  }`}
                >
                  {new Date(m.created_at).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={handleSend}
        className="flex gap-2 p-4 border-t border-white/5"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message…"
          className="flex-1 bg-panel border border-white/10 rounded-full px-4 py-2 text-sm text-paper placeholder:text-muted/60 outline-none focus:border-amber transition-colors"
        />
        <button
          type="submit"
          disabled={!input.trim()}
          className="bg-amber hover:bg-amber-hover text-ink px-5 py-2 rounded-full text-sm font-medium transition-colors disabled:opacity-40"
        >
          Send
        </button>
      </form>
    </div>
  );
}