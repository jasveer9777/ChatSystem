"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { apiFetch } from "@/lib/api";

type Conversation = {
  id: string;
  name: string | null;
  is_group: string;
  created_at: string;
};

type OtherUser = {
  id: string;
  username: string;
  email: string;
};

function initials(name: string) {
  return name.slice(0, 2).toUpperCase();
}

export default function HomePage() {
  const { user, loading, logout, deleteAccount } = useAuth();
  const router = useRouter();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [otherUsers, setOtherUsers] = useState<OtherUser[]>([]);
  const [showNewChat, setShowNewChat] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState("");
  const [showMenu, setShowMenu] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deletePassword, setDeletePassword] = useState("");
  const [deleteError, setDeleteError] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");
  const [fetching, setFetching] = useState(true);

  useEffect(() => {
    if (!loading && !user) router.push("/login");
  }, [loading, user, router]);

  useEffect(() => {
    if (!user) return;
    Promise.all([apiFetch("/conversations/"), apiFetch("/users/")])
      .then(([convos, users]) => {
        setConversations(convos);
        setOtherUsers(users);
      })
      .catch((err) => setError(err.message))
      .finally(() => setFetching(false));
  }, [user]);

  function handleLogout() {
    logout();
    router.push("/login");
  }

  async function handleStartChat() {
    if (!selectedUserId) return;
    setError("");
    try {
      const convo = await apiFetch("/conversations/", {
        method: "POST",
        body: JSON.stringify({ participant_ids: [selectedUserId] }),
      });
      router.push(`/chat/${convo.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start chat");
    }
  }

  async function handleDeleteAccount(e: React.FormEvent) {
    e.preventDefault();
    setDeleteError("");
    setDeleting(true);
    try {
      await deleteAccount(deletePassword);
      router.push("/login");
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "Failed to delete account");
    } finally {
      setDeleting(false);
    }
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
    <div className="flex-1 max-w-2xl mx-auto w-full px-4 py-6 flex flex-col">
      <div className="flex justify-between items-center mb-6">
        <h1 className="font-serif text-2xl text-paper">Messages</h1>

        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="w-9 h-9 rounded-full bg-teal/20 text-teal flex items-center justify-center font-serif text-sm hover:bg-teal/30 transition-colors"
          >
            {initials(user.username)}
          </button>

          {showMenu && (
            <div className="absolute right-0 mt-2 w-48 bg-panel border border-white/10 rounded-lg shadow-xl overflow-hidden z-10">
              <div className="px-4 py-3 border-b border-white/5">
                <p className="text-paper text-sm font-medium">{user.username}</p>
                <p className="text-muted text-xs">{user.email}</p>
              </div>
              <button
                onClick={handleLogout}
                className="w-full text-left px-4 py-2.5 text-sm text-paper hover:bg-panel-hover transition-colors"
              >
                Log out
              </button>
              <button
                onClick={() => {
                  setShowMenu(false);
                  setShowDeleteModal(true);
                }}
                className="w-full text-left px-4 py-2.5 text-sm text-danger hover:bg-panel-hover transition-colors"
              >
                Delete account
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="mb-6">
        <button
          onClick={() => setShowNewChat(!showNewChat)}
          className="bg-amber hover:bg-amber-hover text-ink px-4 py-2 rounded-full text-sm font-medium transition-colors"
        >
          {showNewChat ? "Cancel" : "+ New chat"}
        </button>

        {showNewChat && (
          <div className="mt-3 flex gap-2 items-center">
            <select
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
              className="bg-panel border border-white/10 rounded-lg px-3 py-2 text-sm text-paper flex-1 outline-none focus:border-amber"
            >
              <option value="">Choose someone to message…</option>
              {otherUsers.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.username} ({u.email})
                </option>
              ))}
            </select>
            <button
              onClick={handleStartChat}
              disabled={!selectedUserId}
              className="bg-teal text-ink px-4 py-2 rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-40"
            >
              Start
            </button>
          </div>
        )}
      </div>

      {error && <p className="text-danger text-sm mb-4">{error}</p>}

      <div className="flex-1 divide-y divide-white/5">
        {conversations.length === 0 && (
          <p className="text-muted text-sm py-8 text-center">
            No conversations yet — start one above to say hello.
          </p>
        )}
        {conversations.map((c) => (
          <button
            key={c.id}
            onClick={() => router.push(`/chat/${c.id}`)}
            className="w-full flex items-center gap-3 py-3 px-2 hover:bg-panel-hover rounded-lg transition-colors text-left"
          >
            <div className="w-10 h-10 rounded-full bg-amber/20 text-amber flex items-center justify-center font-serif text-sm flex-shrink-0">
              {initials(c.name || "DM")}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-paper text-sm font-medium truncate">
                {c.name || (c.is_group === "true" ? "Group chat" : "Direct message")}
              </p>
              <p className="text-muted text-xs">
                {new Date(c.created_at).toLocaleDateString()}
              </p>
            </div>
          </button>
        ))}
      </div>

      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 px-4">
          <div className="bg-panel border border-white/10 rounded-2xl p-6 max-w-sm w-full">
            <h2 className="font-serif text-xl text-paper mb-2">Delete account</h2>
            <p className="text-muted text-sm mb-4">
              This permanently deletes your account and removes you from all
              conversations. Enter your password to confirm.
            </p>
            <form onSubmit={handleDeleteAccount} className="space-y-3">
              <input
                type="password"
                value={deletePassword}
                onChange={(e) => setDeletePassword(e.target.value)}
                placeholder="Password"
                required
                autoFocus
                className="w-full bg-ink border border-white/10 rounded-lg px-3 py-2 text-paper placeholder:text-muted/60 outline-none focus:border-danger"
              />
              {deleteError && <p className="text-danger text-sm">{deleteError}</p>}
              <div className="flex gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => {
                    setShowDeleteModal(false);
                    setDeletePassword("");
                    setDeleteError("");
                  }}
                  className="flex-1 border border-white/10 text-paper rounded-lg py-2 text-sm hover:bg-panel-hover transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={deleting}
                  className="flex-1 bg-danger text-white rounded-lg py-2 text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
                >
                  {deleting ? "Deleting…" : "Delete"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}