import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Terminal from '../components/Terminal';
import CodeEditor from '../components/Editor';
import FileBrowser from '../components/FileBrowser';
import api from '../api';
import Participants from '../components/Participants';
import VideoCall from '../components/VideoCall';

const Workspace = () => {
  const { sessionId } = useParams();
  const { user } = useAuth();
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedFilePath, setSelectedFilePath] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchSession = async () => {
      try {
        const res = await api.get(`/sessions/${sessionId}`);
        setSession(res.data.session);
      } catch (err) {
        console.error("Failed to fetch session:", err);
        navigate('/dashboard');
      } finally {
        setLoading(false);
      }
    };
    fetchSession();
  }, [sessionId, navigate]);

  const handleFileSelect = async (path: string) => {
    setSelectedFilePath(path);
    try {
      const res = await api.get(`/containers/${session.containerId}/files/read`, {
        params: { path }
      });
      if (res.data.success) {
        setFileContent(res.data.content);
      }
    } catch (err) {
      console.error("Failed to read file:", err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[100vh] w-screen bg-slate-950">
        <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-pink-500 animate-pulse">Loading Workspace...</h2>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-slate-950 text-white font-sans">
      {/* Header */}
      <nav className="bg-slate-900 border-b border-white/10 px-6 py-3 flex justify-between items-center z-10 shrink-0 shadow-sm shadow-indigo-900/10">
        <div className="flex items-center gap-4">
          <h3 className="m-0 text-xl font-black bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-pink-500">Colab.ai</h3>
          <div className="w-[1px] h-6 bg-white/10 hidden sm:block"></div>
          <div className="flex items-center gap-3">
            <span className="text-slate-400 text-sm font-mono flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]"></span>
              {session?.id.slice(0, 8)}
            </span>
            <span className="text-xs px-2.5 py-1 bg-indigo-500/10 border border-indigo-500/20 rounded-md text-indigo-400 font-mono font-bold uppercase tracking-wider">{session?.osType}</span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-slate-400 text-sm font-medium hidden sm:block">{user?.username}</span>
          <button 
            onClick={async () => {
              const name = prompt("Enter snapshot name:", `Snapshot ${new Date().toLocaleString()}`);
              if (!name) return;
              try {
                const res = await api.post('/snapshots/create', {
                  sessionId: sessionId,
                  name: name,
                  description: "Manual snapshot from workspace"
                });
                if (res.data.success) {
                  alert("Snapshot saved successfully!");
                }
              } catch (err) {
                console.error("Failed to save snapshot:", err);
                alert("Failed to save snapshot.");
              }
            }}
            className="px-4 py-1.5 text-sm rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition-colors shadow-sm shadow-indigo-600/20" 
          >
            Save Snapshot
          </button>
          <button onClick={() => navigate('/dashboard')} className="px-4 py-1.5 text-sm rounded-lg bg-transparent border border-white/10 hover:border-pink-500/40 hover:bg-pink-500/10 text-slate-300 hover:text-white transition-all font-medium">
            Exit
          </button>
        </div>
      </nav>

      {/* Workspace Area */}
      <div className="flex flex-1 overflow-hidden bg-[#0d1322]">
        {/* Left Sidebar: File Browser & Collaboration */}
        <aside className="w-72 bg-slate-900/50 flex-shrink-0 flex flex-col border-r border-white/5 shadow-2xl z-10 transition-all">
          <div className="flex-1 overflow-y-auto w-full custom-scrollbar">
            <FileBrowser containerId={session?.containerId} onFileSelect={handleFileSelect} />
          </div>
          <div className="p-4 border-t border-white/5 bg-slate-900 shadow-[0_-4px_12px_rgba(0,0,0,0.2)]">
            <Participants sessionId={sessionId!} currentUsername={user?.username || 'Anonymous'} />
            <VideoCall sessionId={sessionId!} username={user?.username || 'Anonymous'} />
          </div>
        </aside>

        {/* Main Content: Split Editor and Terminal */}
        <main className="flex-1 flex flex-col overflow-hidden relative">
          <div className="absolute inset-0 bg-indigo-500/5 pointer-events-none blur-3xl opacity-30"></div>
          
          {/* Editor Area */}
          <div className="flex-[2] overflow-hidden p-1 relative z-0">
             <div className="w-full h-full rounded-b-none border-b-0 overflow-hidden shadow-2xl">
               <CodeEditor sessionId={sessionId!} initialCode={fileContent} />
             </div>
          </div>

          {/* Terminal Area */}
          <div className="flex-1 border-t-2 border-indigo-500/20 min-h-[250px] relative z-10 bg-[#0a0f1c] p-1 shadow-[0_-10px_30px_rgba(0,0,0,0.3)]">
             <Terminal sessionId={sessionId!} containerId={session?.containerId} />
          </div>
        </main>
      </div>
    </div>
  );
};

export default Workspace;
