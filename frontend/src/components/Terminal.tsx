import { useEffect, useRef } from 'react';
import { Terminal as XTerm } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';
import { io, Socket } from 'socket.io-client';

interface TerminalProps {
  sessionId: string;
  containerId: string;
  onFileOpen?: (path: string) => void;
}

const Terminal = ({ sessionId, containerId, onFileOpen }: TerminalProps) => {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<XTerm | null>(null);
  const socketRef = useRef<Socket | null>(null);
  const onFileOpenRef = useRef(onFileOpen);

  useEffect(() => {
    onFileOpenRef.current = onFileOpen;
  }, [onFileOpen]);

  useEffect(() => {
    if (!terminalRef.current) return;

    // Initialize xterm
    const term = new XTerm({
      cursorBlink: true,
      theme: {
        background: '#0f172a',
        foreground: '#f8fafc',
      },
      fontFamily: 'Menlo, Monaco, "Courier New", monospace',
      fontSize: 14,
    });
    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.open(terminalRef.current);
    fitAddon.fit();
    xtermRef.current = term;

    // Connect to Socket.io
    const socket = io(import.meta.env.VITE_SOCKET_URL || 'http://localhost:8000', {
        transports: ['websocket'],
    });
    socketRef.current = socket;

    socket.on('connect', () => {
      term.write('\x1b[32mConnected to session terminal...\x1b[0m\r\n');
      socket.emit('join-session', { sessionId, containerId });
    });

    socket.on('terminal-data', (data: string) => {
      term.write(data);
    });

    term.onData((data) => {
      socket.emit('terminal-input', data);
    });

    term.onTitleChange((title) => {
      if (title.startsWith('EDIT:')) {
        const path = title.slice(5);
        if (onFileOpenRef.current) onFileOpenRef.current(path);
      }
    });

    const resizeObserver = new ResizeObserver(() => {
      if (terminalRef.current && terminalRef.current.clientWidth > 0) {
        fitAddon.fit();
        socketRef.current?.emit('terminal-resize', { cols: term.cols, rows: term.rows });
      }
    });

    if (terminalRef.current) {
      resizeObserver.observe(terminalRef.current);
    }

    return () => {
      resizeObserver.disconnect();
      term.dispose();
      socket.disconnect();
    };
  }, [sessionId, containerId]);

  return (
    <div style={{ width: '100%', height: '100%', padding: '10px', background: '#0f172a', borderRadius: '8px', overflow: 'hidden' }}>
      <div ref={terminalRef} style={{ height: '100%' }} />
    </div>
  );
};

export default Terminal;
