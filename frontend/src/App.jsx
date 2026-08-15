import { useState } from "react";
import Login from "./components/Login.jsx";
import Chat from "./components/Chat.jsx";
import ScheduleGrid from "./components/ScheduleGrid.jsx";
import { clearSession, getUser } from "./api.js";

export default function App() {
  const [user, setUser] = useState(getUser());
  // Bumped whenever the chat may have changed a booking, to refresh the grid.
  const [refreshKey, setRefreshKey] = useState(0);

  if (!user) {
    return <Login onLogin={setUser} />;
  }

  function logout() {
    clearSession();
    setUser(null);
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">Cubo Itaú · Room Booking</div>
        <div className="session">
          <span>Signed in as <strong>{user}</strong></span>
          <button className="link" onClick={logout}>Log out</button>
        </div>
      </header>

      <main className="layout">
        <Chat onChanged={() => setRefreshKey((k) => k + 1)} />
        <ScheduleGrid refreshKey={refreshKey} />
      </main>
    </div>
  );
}
