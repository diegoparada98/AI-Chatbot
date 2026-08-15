import { useCallback, useEffect, useState } from "react";
import { roomSchedule } from "../api.js";

const ROOMS = ["A", "B", "C", "D", "E"];
const OPEN_HOUR = 8;
const CLOSE_HOUR = 20;

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

export default function ScheduleGrid({ refreshKey }) {
  const [room, setRoom] = useState("A");
  const [date, setDate] = useState(todayISO());
  const [slots, setSlots] = useState([]);
  const [capacity, setCapacity] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const start = `${date}T${String(OPEN_HOUR).padStart(2, "0")}:00:00`;
      const end = `${date}T${String(CLOSE_HOUR).padStart(2, "0")}:00:00`;
      const data = await roomSchedule(room, start, end);
      setSlots(data.slots);
      setCapacity(data.capacity);
    } catch (err) {
      setError(err.message);
      setSlots([]);
    } finally {
      setLoading(false);
    }
  }, [room, date]);

  useEffect(() => {
    load();
  }, [load, refreshKey]);

  return (
    <div className="schedule card">
      <div className="schedule-controls">
        <h2>Schedule</h2>
        <div className="controls-row">
          <select value={room} onChange={(e) => setRoom(e.target.value)}>
            {ROOMS.map((r) => (
              <option key={r} value={r}>
                Room {r}
              </option>
            ))}
          </select>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
          <button onClick={load} disabled={loading}>
            ↻
          </button>
        </div>
        {capacity != null && (
          <p className="subtitle">Room {room} · capacity {capacity}</p>
        )}
      </div>

      {error && <div className="error">{error}</div>}

      <div className="slots">
        {slots.map((s) => {
          const time = s.start.slice(11, 16);
          return (
            <div key={s.start} className={`slot ${s.status}`} title={s.title || ""}>
              <span className="slot-time">{time}</span>
              <span className="slot-label">
                {s.status === "occupied" ? s.title || "Occupied" : "Free"}
              </span>
            </div>
          );
        })}
        {!loading && slots.length === 0 && !error && (
          <p className="subtitle">No slots to show.</p>
        )}
      </div>
    </div>
  );
}
