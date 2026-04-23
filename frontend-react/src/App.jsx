import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Sparkles, User, Bot, Loader2, Calendar, Settings, MoreHorizontal } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

const Message = ({ text, role, isStreaming }) => {
  const isUser = role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
      className={cn(
        "flex w-full mb-8 group",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div className={cn(
        "flex max-w-[85%] sm:max-w-[75%] gap-4",
        isUser ? "flex-row-reverse" : "flex-row"
      )}>
        <div className={cn(
          "w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg transition-transform duration-300 group-hover:scale-110",
          isUser
            ? "bg-sky-500 text-white shadow-sky-100"
            : "bg-white border border-slate-200 text-sky-600 shadow-slate-100"
        )}>
          {isUser ? <User size={18} /> : <Bot size={18} />}
        </div>

        <div className="flex flex-col gap-1.5">
          <span className={cn(
            "text-[10px] font-bold uppercase tracking-widest text-slate-400 px-1",
            isUser ? "text-right" : "text-left"
          )}>
            {isUser ? "You" : "Planorama AI"}
          </span>
          <div className={cn(
            "relative px-5 py-3.5 rounded-2xl text-[0.95rem] leading-relaxed transition-all",
            isUser
              ? "bg-sky-500 text-white rounded-tr-none shadow-md shadow-sky-100"
              : "bg-white border border-slate-100 text-slate-800 rounded-tl-none shadow-sm shadow-slate-50"
          )}>
            <div
              className="whitespace-pre-wrap break-words"
              dangerouslySetInnerHTML={{
                __html: text.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-sky-700">$1</strong>')
              }}
            />
            {isStreaming && (
              <span className="inline-flex gap-1 ml-2">
                <span className="w-1.5 h-1.5 bg-sky-300 rounded-full animate-bounce [animation-delay:-0.3s]" />
                <span className="w-1.5 h-1.5 bg-sky-300 rounded-full animate-bounce [animation-delay:-0.15s]" />
                <span className="w-1.5 h-1.5 bg-sky-300 rounded-full animate-bounce" />
              </span>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: "Hello! I'm your Planorama AI assistant. How can I help you with your wedding planning today? ✨" }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId] = useState(() => {
    const saved = localStorage.getItem('planorama_session');
    if (saved) return saved;
    const fresh = 'session_' + Math.random().toString(36).substring(2, 11);
    localStorage.setItem('planorama_session', fresh);
    return fresh;
  });

  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages, isStreaming]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const trimmedInput = input.trim();
    if (!trimmedInput || isLoading) return;

    const userMessage = { role: 'user', text: trimmedInput };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8001/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmedInput, session_id: sessionId })
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedText = "";

      setMessages(prev => [...prev, { role: 'assistant', text: '' }]);
      setIsStreaming(true);
      setIsLoading(false);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim();
            if (dataStr === '[DONE]') continue;

            try {
              const data = JSON.parse(dataStr);
              if (data.chunk) {
                accumulatedText += data.chunk;
                setMessages(prev => {
                  const updated = [...prev];
                  updated[updated.length - 1].text = accumulatedText;
                  return updated;
                });
              }
            } catch (e) {}
          }
        }
      }
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: "⚠️ I'm having trouble connecting to the brain. Please ensure the backend is running."
      }]);
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 font-sans antialiased text-slate-900 overflow-hidden justify-center">
      <main className="w-full max-w-5xl flex flex-col relative bg-white sm:m-4 sm:rounded-[32px] sm:border sm:border-slate-200/50 sm:shadow-xl sm:shadow-slate-100/50">
        <header className="h-20 px-8 flex items-center justify-between border-b border-slate-50 shrink-0">
          <div className="flex items-center gap-4">
            <div className="w-9 h-9 bg-sky-500 rounded-xl flex items-center justify-center shadow-lg shadow-sky-100">
              <Sparkles className="text-white" size={18} />
            </div>
            <div className="flex flex-col">
              <h2 className="text-sm font-bold text-slate-800 tracking-tight">Planorama AI Assistant</h2>
              <div className="flex items-center gap-2 mt-0.5">
                <div className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </div>
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">System Online</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button className="p-2.5 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-xl transition-all">
              <Settings size={20} />
            </button>
            <button className="p-2.5 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-xl transition-all">
              <MoreHorizontal size={20} />
            </button>
          </div>
        </header>

        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto px-6 sm:px-12 py-10 scroll-smooth"
        >
          <div className="max-w-3xl mx-auto">
            <AnimatePresence initial={false}>
              {messages.map((msg, idx) => (
                <Message
                  key={idx}
                  text={msg.text}
                  role={msg.role}
                  isStreaming={isStreaming && idx === messages.length - 1}
                />
              ))}
            </AnimatePresence>
            {isLoading && !isStreaming && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3 items-center text-slate-400 text-sm pl-14 font-medium italic">
                <Loader2 className="animate-spin text-sky-500" size={18} />
                <span>AI is thinking...</span>
              </motion.div>
            )}
          </div>
        </div>

        <div className="p-6 sm:p-8 pt-0 shrink-0">
          <div className="max-w-3xl mx-auto">
            <form
              onSubmit={handleSubmit}
              className="relative flex items-center bg-slate-50 border border-slate-200/60 p-2 rounded-3xl shadow-sm focus-within:bg-white focus-within:border-sky-400 focus-within:ring-4 focus-within:ring-sky-50 transition-all duration-300"
            >
              <button type="button" className="p-3 text-slate-400 hover:text-sky-500 transition-colors">
                <Calendar size={20} />
              </button>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask Planorama anything about your wedding..."
                className="flex-1 bg-transparent border-none outline-none px-2 py-3 text-[0.95rem] text-slate-800 placeholder:text-slate-400"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className={cn(
                  "p-3 rounded-2xl transition-all duration-300 shadow-lg active:scale-95",
                  input.trim()
                    ? "bg-sky-500 text-white shadow-sky-100 hover:bg-sky-600"
                    : "bg-slate-200 text-slate-400 shadow-none cursor-not-allowed"
                )}
              >
                <Send size={18} />
              </button>
            </form>
            <p className="text-[9px] text-center text-slate-400 mt-5 font-bold uppercase tracking-[0.3em]">
              AI Wedding Intelligence • Planorama
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}