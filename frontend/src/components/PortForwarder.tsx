import { useState, useEffect } from 'react';
import api from '../api';

interface PortForwarderProps {
  sessionId: string;
}

const PortForwarder = ({ sessionId }: PortForwarderProps) => {
  const [port, setPort] = useState<string>('8080');
  const [tunnelUrl, setTunnelUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Check if there's an active tunnel on mount
    const checkActiveTunnel = async () => {
      try {
        const res = await api.get(`/tunnels/${sessionId}`);
        if (res.data.success && res.data.tunnelUrl) {
          setTunnelUrl(res.data.tunnelUrl);
          setPort(res.data.localPort.toString());
        }
      } catch {
        // 404 means no active tunnel, which is fine
      }
    };
    checkActiveTunnel();
  }, [sessionId]);

  const handleCreate = async () => {
    if (!port || isNaN(Number(port))) return;
    setIsLoading(true);
    try {
      const res = await api.post('/tunnels/create', {
        sessionId,
        localPort: Number(port)
      });
      if (res.data.success) {
        setTunnelUrl(res.data.tunnelUrl);
      }
    } catch (err) {
      alert((err as { response?: { data?: { detail?: string } } }).response?.data?.detail || "Failed to create tunnel");
    } finally {
      setIsLoading(false);
    }
  };

  const handleStop = async () => {
    setIsLoading(true);
    try {
      await api.delete(`/tunnels/${sessionId}`);
      setTunnelUrl(null);
    } catch (err) {
      alert((err as { response?: { data?: { detail?: string } } }).response?.data?.detail || "Failed to stop tunnel");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex items-center gap-3">
      {tunnelUrl ? (
        <>
          <div className="flex items-center gap-2 text-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]"></span>
            <span className="text-slate-300 font-mono">Port {port} forwarded to:</span>
            <a 
              href={tunnelUrl} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-indigo-400 hover:text-indigo-300 font-mono font-medium underline underline-offset-2 transition-colors"
            >
              {tunnelUrl.replace('https://', '')}
            </a>
          </div>
          <button 
            onClick={handleStop}
            disabled={isLoading}
            className="px-2 py-1 bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/20 rounded text-xs font-semibold transition-colors disabled:opacity-50 ml-2 shadow-sm"
          >
            {isLoading ? '...' : 'Stop'}
          </button>
        </>
      ) : (
        <>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-mono font-medium">Forward Port:</span>
            <input 
              type="number" 
              value={port}
              onChange={(e) => setPort(e.target.value)}
              className="w-16 bg-slate-950 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
              placeholder="8080"
              disabled={isLoading}
            />
          </div>
          <button 
            onClick={handleCreate}
            disabled={isLoading || !port}
            className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-semibold transition-colors disabled:opacity-50 shadow-sm"
          >
            {isLoading ? 'Creating...' : 'Preview'}
          </button>
        </>
      )}
    </div>
  );
};

export default PortForwarder;
