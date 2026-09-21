import { useEffect, useRef, useState } from "react";
import { getConversation, listUsers } from "../api";
import { WS_BASE_URL } from "../config";
import { useAuth } from "../context/AuthContext";

export default function Chat() {
  const { user, logout } = useAuth();
  const [users, setUsers] = useState([]);
  const [activeUser, setActiveUser] = useState(null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [connected, setConnected] = useState(false);
  const socketRef = useRef(null);
  const messagesEndRef = useRef(null);
  const activeUserRef = useRef(null);

  useEffect(() => {
    listUsers().then((res) => setUsers(res.data.filter((u) => u.id !== user.id)));
  }, [user.id]);

  // keep a ref in sync so the websocket handler always knows who's open, without reconnecting
  useEffect(() => {
    activeUserRef.current = activeUser;
  }, [activeUser]);

  useEffect(() => {
    if (!activeUser) return;
    getConversation(activeUser.id).then((res) => setMessages(res.data));
  }, [activeUser]);

  useEffect(() => {
    const socket = new WebSocket(`${WS_BASE_URL}/ws/chat/${user.id}`);
    socketRef.current = socket;

    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      const otherPartyId =
        payload.sender_id === user.id ? payload.receiver_id : payload.sender_id;

      // only show it if it belongs to the conversation currently open
      if (activeUserRef.current?.id !== otherPartyId) return;

      setMessages((prev) => [
        ...prev,
        {
          id: payload.message_id,
          sender_id: payload.sender_id,
          receiver_id: payload.receiver_id,
          content: payload.content,
        },
      ]);
    };

    return () => socket.close();
  }, [user.id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function sendMessage(e) {
    e.preventDefault();
    if (!draft.trim() || !activeUser || !socketRef.current) return;

    socketRef.current.send(
      JSON.stringify({ receiver_id: activeUser.id, content: draft.trim() })
    );
    setDraft("");
  }

  function usernameFor(senderId) {
    if (senderId === user.id) return "You";
    return users.find((u) => u.id === senderId)?.username || `User ${senderId}`;
  }

  return (
    <div className="chat-layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="avatar">{user.username[0].toUpperCase()}</div>
          <div>
            <div className="me-name">{user.username}</div>
            <div className={`status ${connected ? "online" : "offline"}`}>
              {connected ? "Online" : "Connecting..."}
            </div>
          </div>
          <button className="logout-btn" onClick={logout} title="Log out">
            ⎋
          </button>
        </div>

        <div className="user-list">
          {users.map((u) => (
            <button
              key={u.id}
              className={`user-item ${activeUser?.id === u.id ? "active" : ""}`}
              onClick={() => setActiveUser(u)}
            >
              <div className="avatar small">{u.username[0].toUpperCase()}</div>
              <span>{u.username}</span>
            </button>
          ))}
          {users.length === 0 && <div className="empty-hint">No other users yet</div>}
        </div>
      </aside>

      <main className="chat-panel">
        {activeUser ? (
          <>
            <header className="chat-header">
              <div className="avatar small">{activeUser.username[0].toUpperCase()}</div>
              <span>{activeUser.username}</span>
            </header>

            <div className="message-list">
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={`bubble ${m.sender_id === user.id ? "mine" : "theirs"}`}
                >
                  <span className="bubble-author">{usernameFor(m.sender_id)}</span>
                  {m.content}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            <form className="composer" onSubmit={sendMessage}>
              <input
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder={`Message ${activeUser.username}...`}
              />
              <button type="submit">Send</button>
            </form>
          </>
        ) : (
          <div className="screen-center muted">Select a user to start chatting</div>
        )}
      </main>
    </div>
  );
}
