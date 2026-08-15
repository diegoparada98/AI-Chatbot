import { useEffect, useRef, useState } from "react";
import { sendChat } from "../api.js";

const WELCOME = {
  role: "assistant",
  content:
    "Hi! I can help you book a meeting room at Cubo Itaú. Try: " +
    "\"Book room B tomorrow 10:00–11:00 for a standup with 4 people\", " +
    "\"which rooms are free tomorrow 3–4pm?\", or \"show room A's schedule tomorrow\".",
};

export default function Chat({ onChanged }) {
  const [messages, setMessages] = useState([WELCOME]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight);
  }, [messages, busy]);

  async function send(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || busy) return;

    const history = messages.filter((m) => m !== WELCOME);
    const next = [...messages, { role: "user", content: text }];
    setMessages(next);
    setInput("");
    setBusy(true);
    try {
      const { reply } = await sendChat(text, history);
      setMessages((m) => [...m, { role: "assistant", content: reply }]);
      // A booking may have changed — let the schedule refresh.
      onChanged?.();
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: `⚠️ ${err.message}` },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="chat card">
      <div className="messages" ref={scrollRef}>
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}`}>
            {m.content}
          </div>
        ))}
        {busy && <div className="bubble assistant typing">…</div>}
      </div>
      <form className="composer" onSubmit={send}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask me to book, list or cancel a room…"
          disabled={busy}
        />
        <button type="submit" disabled={busy || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
