import { useState, useEffect, useRef } from 'react';
import './App.css';

function makeId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID();
  return 'id-' + Math.random().toString(36).slice(2) + Date.now();
}

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isAITyping, setIsAITyping] = useState(false);
  const [theme, setTheme] = useState('light');
  const messageListRef = useRef(null);
  const aiMsgIdRef = useRef(null);
  const abortRef = useRef(null);

  // Auto‑scroll on new messages
  useEffect(() => {
    if (messageListRef.current) {
      messageListRef.current.scrollTop = messageListRef.current.scrollHeight;
    }
  }, [messages]); // React batches updates; scrolling after render is reliable [web:33][web:122]

  // Apply theme
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme); // attribute selector drives CSS vars [web:80][web:89]
  }, [theme]);

  const toggleTheme = () => setTheme(theme === 'light' ? 'dark' : 'light');

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || isAITyping) return;

    const userText = input.trim();
    setInput('');
    setIsAITyping(true);

    // Insert user bubble (right) and AI placeholder (left)
    const userId = makeId();
    const aiId = makeId();
    aiMsgIdRef.current = aiId;

    setMessages(prev => [
      ...prev,
      { id: userId, text: userText, sender: 'user' },
      { id: aiId, text: '', sender: 'ai' }
    ]); // queue a single render with both entries [web:33][web:122]

    // cancel any existing stream
    if (abortRef.current) abortRef.current.abort();
    abortRef.current = new AbortController();

    try {
      const response = await fetch('http://localhost:8000/api/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: userText, sender_type: 'user' }),
        signal: abortRef.current.signal
      });

      if (!response.body) {
        setIsAITyping(false);
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse SSE: events separated by a blank line; data may span multiple lines
        const events = buffer.split(/\r?\n\r?\n/);
        buffer = events.pop() || '';

        for (const evt of events) {
          const data = evt
            .split(/\r?\n/)
            .filter(l => l.startsWith('data:'))
            .map(l => l.slice(5).trim())
            .join('\n'); // reconstruct payload per spec [web:80][web:153]

          if (!data) continue;
          if (data === '[DONE]') {
            reader.cancel();
            break;
          }

          try {
            const json = JSON.parse(data);
            const piece = json.choices?.[0]?.delta?.content || '';
            if (!piece) continue;

            // Append strictly to the current AI bubble
            setMessages(prev =>
              prev.map(m => (m.id === aiMsgIdRef.current ? { ...m, text: m.text + piece } : m))
            ); // functional update avoids stale state during queued updates [web:33][web:122]
          } catch (err) {
            console.error('Stream parse error:', err);
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('Request failed:', err);
        setMessages(prev =>
          prev.map(m => (m.id === aiMsgIdRef.current ? { ...m, text: 'Sorry, an error occurred.' } : m))
        );
      }
    } finally {
      setIsAITyping(false);
      abortRef.current = null;
    }
  };

  useEffect(() => {
    return () => {
      if (abortRef.current) abortRef.current.abort();
    };
  }, []);

  return (
    <div id="root">
      {/* Theme Toggle */}
      <div style={{ textAlign: 'right', padding: '10px' }}>
        <button onClick={toggleTheme} className="theme-toggle">
          {theme === 'light' ? 'Dark Mode' : 'Light Mode'}
        </button>
      </div>

      {/* Chat Window */}
      <div className="chat-window">
        <div className="message-list" ref={messageListRef}>
          {messages.map((msg) => (
            <div key={msg.id} className={`message ${msg.sender}`}>
              {msg.text}
            </div>
          ))}

          {/* Optional separate typing bubble — keep if desired */}
          {isAITyping && aiMsgIdRef.current && (
            <div className="message ai typing-indicator">
              AI is typing<span className="dot">.</span><span className="dot">.</span><span className="dot">.</span>
            </div>
          )}
        </div>

        <form className="message-input" onSubmit={handleSendMessage}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask your AI assistant..."
            autoFocus
            disabled={isAITyping}
          />
          <button type="submit" disabled={isAITyping || !input.trim()}>
            {isAITyping ? 'Sending...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;
