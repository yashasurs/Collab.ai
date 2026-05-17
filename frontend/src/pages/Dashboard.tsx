import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import LabSelector from '../components/LabSelector';
import api from '../api';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const [sessions, setSessions] = useState<any[]>([]);
  const [loadingData, setLoadingData] = useState(true);
  const [showSelector, setShowSelector] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const sessionsRes = await api.get('/sessions');
        setSessions(Array.isArray(sessionsRes.data) ? sessionsRes.data : Object.values(sessionsRes.data) || []);
      } catch (error) {
        console.error("Failed to fetch sessions:", error);
      } finally {
        setLoadingData(false);
      }
    };

    fetchDashboardData();
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const onSessionCreated = (newSession: any) => {
    setShowSelector(false);
    navigate(`/workspace/${newSession.id}`);
  };

  if (loadingData) {
    return (
      <div className="flex items-center justify-center min-h-screen w-screen bg-slate-950">
        <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-pink-500 animate-pulse">Loading Dashboard...</h2>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-screen flex flex-col bg-slate-950 text-white relative">
      {/* Background gradients */}
      <div className="absolute w-[50vw] h-[50vw] bg-indigo-500/10 blur-[150px] rounded-full top-[-25vw] left-[-25vw] pointer-events-none" />

      {/* Selector Modal Overlay */}
      {showSelector && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-8">
          <div className="relative w-full max-w-4xl mx-auto">
            <button 
                onClick={() => setShowSelector(false)} 
                className="absolute -top-12 right-0 text-white hover:text-pink-400 text-3xl font-bold transition-colors"
                title="Close"
            >
              ✕
            </button>
            <LabSelector 
              userId={user?.username || ''} 
              username={user?.username || ''} 
              onSessionCreated={onSessionCreated} 
            />
          </div>
        </div>
      )}

      {/* Navbar */}
      <nav className="bg-slate-900/60 backdrop-blur-md border-b border-white/5 py-4 px-8 flex justify-between items-center z-10 sticky top-0">
        <h2 className="m-0 text-2xl font-black bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-pink-500">Colab.ai Dashboard</h2>
        <div className="flex items-center gap-6">
          <span className="text-slate-300 font-medium">Welcome, <span className="text-indigo-400 font-bold">{user?.username}</span></span>
          <button onClick={handleLogout} className="px-5 py-2.5 rounded-xl border border-slate-700 hover:border-pink-500/50 hover:bg-pink-500/10 text-white transition-all font-semibold">
            Logout
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <div className="p-8 flex-1 w-full max-w-7xl mx-auto z-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
          {/* Active Sessions Card */}
          <div className="bg-slate-900/60 backdrop-blur-xl p-8 rounded-3xl border border-indigo-500/20 shadow-lg shadow-indigo-500/5 flex flex-col justify-between">
            <div>
              <h3 className="mb-2 text-indigo-400 font-bold text-xl">Active Sessions</h3>
              <p className="text-5xl font-black mb-4">{sessions.length}</p>
              <p className="text-slate-400 text-sm leading-relaxed mb-6">Currently running coding environments across your collaborative platform.</p>
            </div>
            <button onClick={() => setShowSelector(true)} className="w-full py-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold transition-all shadow-lg shadow-indigo-600/30 transform hover:-translate-y-1">
              Create New Session
            </button>
          </div>
          
          {/* General info space */}
          <div className="bg-slate-900/60 backdrop-blur-xl p-8 rounded-3xl border border-white/5 flex flex-col col-span-1 md:col-span-2 items-center justify-center text-slate-500 text-center">
            <div className="text-5xl mb-4">🚀</div>
            <p className="text-lg">Select a session above to jump into your workspace or create a new Linux container right in the browser.</p>
          </div>
        </div>

        <div>
          <h3 className="text-2xl font-bold mb-6 text-slate-200 border-b border-white/10 pb-4">Your Recent Sessions</h3>
          {sessions.length === 0 ? (
            <div className="p-12 text-center text-slate-400 bg-slate-900/30 rounded-3xl border border-white/5 border-dashed">
              No sessions found. Create a new session to get started.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {sessions.map(session => (
                <div key={session.id} className="bg-slate-800/40 p-6 rounded-2xl border border-white/5 hover:border-indigo-500/30 transition-all group">
                  <div className="flex justify-between items-start mb-4">
                    <span className="bg-indigo-500/20 text-indigo-300 text-xs px-3 py-1 rounded-full font-mono flex items-center gap-2">
                       <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse"></span>
                       {session.osType}
                    </span>
                    <span className="text-xs text-slate-500 font-mono">{session.id.substring(0,8)}</span>
                  </div>
                  <div className="flex items-center gap-2 mb-6">
                    <div className="text-slate-400 text-sm">Participants:</div>
                    <div className="flex -space-x-2">
                       {(session.participants || []).slice(0,3).map((p: any) => (
                         <div key={p.userId} className="w-8 h-8 rounded-full bg-slate-700 border-2 border-slate-900 flex items-center justify-center text-xs font-bold" title={p.username}>
                           {p.username.charAt(0).toUpperCase()}
                         </div>
                       ))}
                    </div>
                  </div>
                  <button 
                    onClick={() => navigate(`/workspace/${session.id}`)}
                    className="w-full py-2.5 rounded-lg border border-indigo-500/30 hover:bg-indigo-500 hover:text-white text-indigo-400 transition-colors font-medium"
                  >
                    Join Workspace
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
export default Dashboard;
