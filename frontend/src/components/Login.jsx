import { useState } from "react";
import { login, saveSession } from "../api.js";

export default function Login({ onLogin }) {
  const [username, setUsername] = useState("User1");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const { access_token, username: name } = await login(username, password);
      saveSession(access_token, name);
      onLogin(name);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <form className="card login-card" onSubmit={submit}>
        <h1>Cubo Itaú</h1>
        <p className="subtitle">Meeting-room booking assistant</p>

        <label>User</label>
        <select value={username} onChange={(e) => setUsername(e.target.value)}>
          <option>User1</option>
          <option>User2</option>
        </select>

        <label>Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          autoFocus
        />

        {error && <div className="error">{error}</div>}

        <button type="submit" disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}
