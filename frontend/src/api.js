// Thin API client. Token is kept in localStorage and sent as a Bearer header.

const TOKEN_KEY = "cubo_token";
const USER_KEY = "cubo_user";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}
export function getUser() {
  return localStorage.getItem(USER_KEY);
}
export function saveSession(token, username) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, username);
}
export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 60_000);

  try {
    const res = await fetch(path, { ...options, headers, signal: controller.signal });
    if (res.status === 204) return null;

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.detail || `Request failed (${res.status})`);
    }
    return data;
  } catch (err) {
    if (err.name === "AbortError") throw new Error("Request timed out (60 s). Check the backend.");
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

export function login(username, password) {
  return request("/api/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function sendChat(message, history) {
  return request("/api/chat", {
    method: "POST",
    body: JSON.stringify({ message, history }),
  });
}

export function listRooms() {
  return request("/api/rooms");
}

export function roomSchedule(room, startISO, endISO) {
  const q = new URLSearchParams({ start: startISO, end: endISO });
  return request(`/api/rooms/${room}/schedule?${q}`);
}
