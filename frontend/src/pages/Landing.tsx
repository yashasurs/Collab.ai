import { Link } from 'react-router-dom';

const Landing = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 overflow-x-hidden selection:bg-slate-700">
      {/* Navbar Minimal */}
      <nav className="fixed top-0 w-full z-50 bg-slate-950/80 backdrop-blur-md border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="text-2xl font-black tracking-tight text-white">COLAB<span className="text-slate-500">.AI</span></div>
          <div className="flex gap-4">
            <Link to="/login" className="px-5 py-2.5 text-sm font-medium text-slate-300 hover:text-white transition-colors">SignIn</Link>
            <Link to="/register" className="px-5 py-2.5 text-sm font-semibold bg-white text-slate-950 rounded-full hover:bg-slate-200 transition-transform hover:scale-105">Get Started</Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-40 pb-20 px-6 lg:pt-56 lg:pb-32 flex flex-col items-center text-center">
        <div className="absolute inset-0 top-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]"></div>
        
        <div className="relative z-10 max-w-5xl mx-auto flex flex-col items-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-slate-900 border border-slate-700 text-xs font-medium uppercase tracking-widest text-slate-400 mb-8">
            <span className="w-2 h-2 rounded-full bg-slate-400 animate-pulse"></span>
            Now in Public Beta
          </div>
          
          <h1 className="text-5xl md:text-7xl lg:text-8xl font-black text-white leading-tight md:leading-none tracking-tighter mb-8">
            The Cloud IDE <br className="hidden sm:block" />
            <span className="text-slate-500">Built for Teams.</span>
          </h1>
          
          <p className="text-lg md:text-xl text-slate-400 max-w-2xl mb-12 leading-relaxed">
            Instantly spin up isolated Docker environments, collaborate in real-time via secure tunnels, and leverage AI to code faster. All perfectly synced.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
            <Link to="/register" className="w-full sm:w-auto px-8 py-4 rounded-full bg-white text-slate-950 font-bold text-lg hover:bg-slate-200 transition-all hover:scale-105 shadow-xl shadow-white/10 flex items-center justify-center gap-2">
              Start Building Now
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinelinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" /></svg>
            </Link>
            <a href="#features" className="w-full sm:w-auto px-8 py-4 rounded-full bg-slate-900 border border-slate-700 text-white font-bold text-lg hover:bg-slate-800 transition-all flex items-center justify-center">
              View Features
            </a>
          </div>
        </div>
      </section>

      {/* Product Preview / Features */}
      <section id="features" className="py-24 px-6 bg-slate-950 relative">
        <div className="max-w-7xl mx-auto">
          <div className="mb-20 text-center">
            <h2 className="text-3xl md:text-5xl font-black text-white mb-6">Everything you need. <br/> Nothing you don't.</h2>
            <p className="text-slate-400 text-lg max-w-2xl mx-auto">A powerful suite of tools designed to remove friction from your collaborative development workflow.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Feature 1 */}
            <div className="bg-slate-900 border border-slate-800 p-8 rounded-3xl group hover:bg-slate-800/50 transition-colors">
              <div className="w-14 h-14 bg-white/10 rounded-2xl flex items-center justify-center mb-6 text-2xl group-hover:scale-110 transition-transform">🤖</div>
              <h3 className="text-xl font-bold text-white mb-3">AI Pair Programming</h3>
              <p className="text-slate-400 leading-relaxed">Integrated AI assistant that understands your workspace context, ready to debug, explain, and write code alongside you.</p>
            </div>
            
            {/* Feature 2 */}
            <div className="bg-slate-900 border border-slate-800 p-8 rounded-3xl group hover:bg-slate-800/50 transition-colors">
              <div className="w-14 h-14 bg-white/10 rounded-2xl flex items-center justify-center mb-6 text-2xl group-hover:scale-110 transition-transform">⚡</div>
              <h3 className="text-xl font-bold text-white mb-3">Instant OS Labs</h3>
              <p className="text-slate-400 leading-relaxed">Launch isolated Alpine, Ubuntu, Debian, Fedora, or Arch Linux containers in milliseconds. No local setup required.</p>
            </div>
            
            {/* Feature 3 */}
            <div className="bg-slate-900 border border-slate-800 p-8 rounded-3xl group hover:bg-slate-800/50 transition-colors">
              <div className="w-14 h-14 bg-white/10 rounded-2xl flex items-center justify-center mb-6 text-2xl group-hover:scale-110 transition-transform">🔒</div>
              <h3 className="text-xl font-bold text-white mb-3">Secure Networking</h3>
              <p className="text-slate-400 leading-relaxed">Every session is automatically assigned an ephemeral Cloudflared tunnel, allowing secure global access without exposing ports.</p>
            </div>

            {/* Feature 4 */}
            <div className="bg-slate-900 border border-slate-800 p-8 rounded-3xl group hover:bg-slate-800/50 transition-colors lg:col-span-2">
              <div className="w-14 h-14 bg-white/10 rounded-2xl flex items-center justify-center mb-6 text-2xl group-hover:scale-110 transition-transform">🤝</div>
              <h3 className="text-xl font-bold text-white mb-3">Real-Time Multiplayer</h3>
              <p className="text-slate-400 leading-relaxed">Code, run commands, and preview changes synchronously using WebSocket and Monaco Editor. Built-in WebRTC enables seamless face-to-face communication right in the IDE.</p>
            </div>

            {/* Feature 5 */}
            <div className="bg-slate-900 border border-slate-800 p-8 rounded-3xl group hover:bg-slate-800/50 transition-colors">
              <div className="w-14 h-14 bg-white/10 rounded-2xl flex items-center justify-center mb-6 text-2xl group-hover:scale-110 transition-transform">💾</div>
              <h3 className="text-xl font-bold text-white mb-3">Stateful Snapshots</h3>
              <p className="text-slate-400 leading-relaxed">Freeze your workspace state at any moment into a Docker image and restore it later instantly. Total environment portability.</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-32 px-6 relative overflow-hidden">
        <div className="absolute inset-0 bg-slate-900"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-white opacity-[0.03] rounded-full blur-3xl"></div>
        
        <div className="relative z-10 max-w-4xl mx-auto text-center">
          <h2 className="text-4xl md:text-6xl font-black text-white mb-8">Ready to revolutionize your workflow?</h2>
          <p className="text-xl text-slate-400 mb-12">Stop fighting environments. Start building the future.</p>
          <Link to="/register" className="inline-block px-10 py-5 rounded-full bg-white text-slate-950 font-bold text-xl hover:bg-slate-200 transition-transform hover:scale-105 shadow-2xl">
            Create Free Account
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-950 py-12 px-6 border-t border-slate-900">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="text-2xl font-black tracking-tight text-white">COLAB<span className="text-slate-600">.AI</span></div>
          <div className="text-slate-500 text-sm">
            © {new Date().getFullYear()} Colab.ai. Powered by Open Source.
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
