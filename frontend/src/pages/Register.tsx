import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../api';

const Register = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await api.post('/auth/register', {
        username,
        email,
        password
      });

      // After successful registration, navigate to login or auto-login
      navigate('/login');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed. Username or email might be taken.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen w-screen bg-slate-950 p-6 relative overflow-hidden">
      {/* Background gradients */}
      <div className="absolute w-[40vw] h-[40vw] bg-indigo-500/20 blur-[120px] rounded-full top-[-10vw] -right-[10vw] pointer-events-none" />
      <div className="absolute w-[40vw] h-[40vw] bg-pink-500/10 blur-[120px] rounded-full bottom-[-10vw] -left-[10vw] pointer-events-none" />

      <div className="bg-slate-900/60 backdrop-blur-xl p-10 md:p-14 w-full max-w-md rounded-3xl border border-white/10 shadow-2xl relative z-10">
        <h2 className="text-4xl font-extrabold text-center mb-8 bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-pink-500">Create Account</h2>
        
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-500 p-4 rounded-xl mb-6 text-sm flex items-center gap-3">
            <span>⚠️</span> {error}
          </div>
        )}

        <form onSubmit={handleRegister} className="flex flex-col gap-5">
          <div className="flex flex-col">
            <label className="mb-2 text-sm font-medium text-slate-300">Username</label>
            <input 
              type="text" 
              className="w-full p-4 bg-slate-800/50 border border-slate-700/50 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all font-mono" 
              placeholder="developer123"
              value={username} 
              onChange={(e) => setUsername(e.target.value)} 
              required 
            />
          </div>
          <div className="flex flex-col">
            <label className="mb-2 text-sm font-medium text-slate-300">Email</label>
            <input 
              type="email" 
              className="w-full p-4 bg-slate-800/50 border border-slate-700/50 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all font-mono" 
              placeholder="you@example.com"
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
              required 
            />
          </div>
          <div className="flex flex-col">
            <label className="mb-2 text-sm font-medium text-slate-300">Password</label>
            <input 
              type="password" 
              className="w-full p-4 bg-slate-800/50 border border-slate-700/50 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all font-mono" 
              placeholder="••••••••"
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              required 
              minLength={6}
            />
          </div>
          
          <button type="submit" className="w-full mt-4 py-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-lg shadow-lg shadow-indigo-600/30 transition-all transform hover:-translate-y-1 active:translate-y-0 disabled:opacity-70 disabled:cursor-not-allowed disabled:transform-none" disabled={loading}>
            {loading ? 'Registering...' : 'Register'}
          </button>
        </form>

        <p className="text-center mt-8 text-slate-400 text-sm">
          Already have an account? <Link to="/login" className="text-indigo-400 font-bold hover:text-pink-500 transition-colors ml-1">Login here</Link>
        </p>
      </div>
    </div>
  );
};

export default Register;
