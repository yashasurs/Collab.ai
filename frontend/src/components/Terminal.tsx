import { useEffect, useRef } from 'react';
import { Terminal as XTerm } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';
import { useSocket } from '../contexts/SocketContext';

interface TerminalProps {
  sessionId?: string;
  containerId: string | undefined;
  onFileOpen?: (path: string) => void;
}

const Terminal = ({ containerId, onFileOpen }: TerminalProps) => {
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<XTerm | null>(null);
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

    return () => {
      term.dispose();
    };
  }, []);

  const { socket, isConnected } = useSocket();

  useEffect(() => {
    if (!socket || !isConnected || !xtermRef.current || !containerId) return;

    const term = xtermRef.current;
    term.write('\x1b[32mConnected to session terminal...\x1b[0m\r\n');
    socket.emit('start-terminal', { containerId });

    const onTerminalData = (data: string) => {
      term.write(data);
    };

    const onTermData = (data: string) => {
      socket.emit('terminal-input', data);
    };

    socket.on('terminal-data', onTerminalData);
    const dataDisposable = term.onData(onTermData);

    term.onTitleChange((title) => {
      if (title.startsWith('EDIT:')) {
        const path = title.slice(5);
        if (onFileOpenRef.current) onFileOpenRef.current(path);
      }
    });

    const resizeObserver = new ResizeObserver(() => {
      if (terminalRef.current && terminalRef.current.clientWidth > 0 && xtermRef.current) {
        // xterm needs a moment before fit can be called on resize sometimes
        setTimeout(() => {
          if (!xtermRef.current) return;
          try {

            // Actually, fitAddon was not stored. We don't need to re-fit if xterm handles resize.
            // But we do need to emit resize events to the backend
            socket.emit('terminal-resize', { cols: xtermRef.current.cols, rows: xtermRef.current.rows });
          } catch {
            // ignore
          }
        }, 100);
      }
    });

    if (terminalRef.current) {
      resizeObserver.observe(terminalRef.current);
    }

    return () => {
      resizeObserver.disconnect();
      socket.off('terminal-data', onTerminalData);
      dataDisposable.dispose();
    };
  }, [socket, isConnected, containerId]);

  return (
    <div style={{ width: '100%', height: '100%', padding: '10px', background: '#0f172a', borderRadius: '8px', overflow: 'hidden' }}>
      <div ref={terminalRef} style={{ height: '100%' }} />
    </div>
  );
};

export default Terminal;
