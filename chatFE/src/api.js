import axios from "axios";
import { API_BASE_URL } from "./config";

const api = axios.create({
  baseURL: API_BASE_URL,
});

// attaches the saved JWT to every outgoing request so protected routes work
api.interceptors.request.use((requestConfig) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    requestConfig.headers.Authorization = `Bearer ${token}`;
  }
  return requestConfig;
});

export function signup({ username, email, password }) {
  return api.post("/users/", { username, email, password });
}

export function login({ username, password }) {
  return api.post("/users/login", { username, password });
}

export function getCurrentUser() {
  return api.get("/users/me");
}

export function logout() {
  return api.post("/users/logout");
}

export function listUsers() {
  return api.get("/users/");
}

export function getConversation(otherUserId) {
  return api.get(`/messages/${otherUserId}`);
}

export default api;
