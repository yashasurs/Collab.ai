import { useState, useRef, useEffect } from 'react';
import api from '../api';

interface AIChatProps {
  activeFileName?: string;
  activeFileContent?: string;
}

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

const AIChat = ({ activeFileName, activeFileContent }: AIChatProps) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user' as const, content: input.trim() };
    const newHistory = [...messages, userMessage];
    setMessages(newHistory);
    setInput('');
    setIsLoading(true);

    try {
      // Prepare the payload with the injected context
      let payloadMessages = [...newHistory];
      
      // Inject the active file context as a system message if a file is open
      if (activeFileName && activeFileContent) {
        const systemContext: Message = {
          role: 'system',
          content: `You are a helpful coding assistant. The user is currently viewing/editing the file "${activeFileName}". Here is its current content:\n\n\`\`\`\n${activeFileContent}\n\`\`\`\n\nUse this context to answer their questions accurately. Do not explicitly mention that you were given this context unless asked.`
        };
        // Add system message at the beginning
        payloadMessages = [systemContext, ...payloadMessages];
      }

      const res = await api.post('/ai/chat', { messages: payloadMessages });
      
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: res.data.reply }
      ]);
    } catch (err) {
      console.error("AI Chat Error:", err);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, I encountered an error. Please ensure the AI backend is configured and your API key is valid.' }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-900/50 border-l border-white/5">
      <div className="px-4 py-3 border-b border-white/5 bg-slate-900 shadow-[0_4px_12px_rgba(0,0,0,0.2)] flex-shrink-0">
        <h4 className="m-0 text-sm font-semibold text-slate-200 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-pink-500 animate-pulse shadow-[0_0_8px_rgba(236,72,153,0.5)]"></span>
          AI Assistant
        </h4>
        {activeFileName ? (
           <p className="text-xs text-slate-400 mt-1 truncate">Context: {activeFileName}</p>
        ) : (
           <p className="text-xs text-slate-500 mt-1">No file context</p>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
        {messages.length === 0 && (
          <div className="text-center text-slate-500 text-sm mt-4">
            Ask me anything about your code!
          </div>
        )}
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
            <div className={`px-3 py-2 rounded-lg max-w-[90%] text-sm ${msg.role === 'user' ? 'bg-indigo-600 text-white rounded-br-sm' : 'bg-slate-800 text-slate-200 rounded-bl-sm border border-slate-700 shadow-sm'}`}>
              <pre className="whitespace-pre-wrap font-sans leading-relaxed m-0">{msg.content}</pre>
            </div>
            <span className="text-[10px] text-slate-500 mt-1 px-1">
              {msg.role === 'user' ? 'You' : 'AI Assistant'}
            </span>
          </div>
        ))}
        {isLoading && (
          <div className="flex items-start">
            <div className="px-3 py-2 rounded-lg bg-slate-800 text-slate-400 rounded-bl-sm border border-slate-700 text-sm flex items-center gap-2">
              <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></div>
              <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }}></div>
              <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }}></div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-3 bg-slate-900 border-t border-white/5 flex-shrink-0">
        <div className="flex flex-col gap-2">
          <textarea 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Ask AI..."
            className="w-full bg-slate-950 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 resize-none min-h-[60px]"
          />
          <div className="flex justify-between items-center">
            <span className="text-[10px] text-slate-500">Press Enter to send</span>
            <button 
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-medium rounded transition-colors shadow-sm"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIChat;
