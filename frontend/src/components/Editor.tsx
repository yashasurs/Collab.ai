import Editor from '@monaco-editor/react';
import { useEffect, useRef, useState } from 'react';
import { io, Socket } from 'socket.io-client';

interface CodeEditorProps {
  sessionId: string;
  initialCode?: string;
  filePath?: string;
  onSave?: (content: string) => void;
}

const getLanguageFromPath = (path: string) => {
  if (!path) return 'python';
  const ext = path.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'py': return 'python';
    case 'js': return 'javascript';
    case 'ts': return 'typescript';
    case 'jsx': return 'javascript';
    case 'tsx': return 'typescript';
    case 'html': return 'html';
    case 'css': return 'css';
    case 'json': return 'json';
    case 'md': return 'markdown';
    case 'sh': return 'shell';
    case 'yml':
    case 'yaml': return 'yaml';
    case 'cpp':
    case 'cc':
    case 'cxx': return 'cpp';
    case 'c': return 'c';
    case 'java': return 'java';
    case 'go': return 'go';
    case 'rs': return 'rust';
    default: return 'plaintext';
  }
};

const CodeEditor = ({ sessionId, initialCode = '', filePath = '', onSave }: CodeEditorProps) => {
  const [code, setCode] = useState(initialCode);
  const [language, setLanguage] = useState(getLanguageFromPath(filePath));
  const socketRef = useRef<Socket | null>(null);
  const isRemoteChange = useRef(false);

  // Sync state when initialCode changes (e.g. user selects a different file)
  useEffect(() => {
    setCode(initialCode);
  }, [initialCode]);

  useEffect(() => {
    setLanguage(getLanguageFromPath(filePath));
  }, [filePath]);

  useEffect(() => {
    const socket = io(import.meta.env.VITE_SOCKET_URL || 'http://localhost:8000', {
        transports: ['websocket'],
    });
    socketRef.current = socket;

    socket.emit('join-session', { sessionId });

    socket.on('editor-sync', (data: any) => {
      if (data.sessionId === sessionId) {
        isRemoteChange.current = true;
        setCode(data.content);
      }
    });

    return () => {
      socket.disconnect();
    };
  }, [sessionId]);

  const handleEditorChange = (value: string | undefined) => {
    const newContent = value || '';
    if (!isRemoteChange.current) {
      setCode(newContent);
      socketRef.current?.emit('editor-change', {
        sessionId,
        content: newContent,
      });
    }
    isRemoteChange.current = false;
  };

  const handleEditorDidMount = (editor: any, monaco: any) => {
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      // We pass the current value directly from the editor instance to ensure we have the latest
      if (onSave) {
        onSave(editor.getValue());
      }
    });
  };

  return (
    <div style={{ height: '100%', width: '100%', borderRadius: '8px', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '4px 12px', background: '#0f172a', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #1e293b' }}>
        <div style={{ fontSize: '13px', color: '#94a3b8', fontFamily: 'monospace' }}>
          {filePath || 'Untitled'}
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <select 
            value={language} 
            onChange={(e) => setLanguage(e.target.value)} 
            style={{ background: '#1e293b', color: '#e2e8f0', border: '1px solid #334155', borderRadius: '4px', padding: '2px 8px', fontSize: '12px', outline: 'none', cursor: 'pointer' }}
          >
            <option value="plaintext">Plain Text</option>
            <option value="python">Python</option>
            <option value="javascript">JavaScript</option>
            <option value="typescript">TypeScript</option>
            <option value="html">HTML</option>
            <option value="css">CSS</option>
            <option value="json">JSON</option>
            <option value="markdown">Markdown</option>
            <option value="shell">Shell</option>
            <option value="cpp">C++</option>
            <option value="c">C</option>
            <option value="java">Java</option>
            <option value="go">Go</option>
            <option value="rust">Rust</option>
            <option value="yaml">YAML</option>
          </select>
          <button 
            onClick={() => { if (onSave) onSave(code); }}
            style={{ background: '#3b82f6', color: 'white', border: 'none', borderRadius: '4px', padding: '2px 12px', fontSize: '12px', cursor: 'pointer', fontWeight: 600, transition: 'background 0.2s' }}
            onMouseOver={(e) => e.currentTarget.style.background = '#2563eb'}
            onMouseOut={(e) => e.currentTarget.style.background = '#3b82f6'}
          >
            Save
          </button>
        </div>
      </div>
      <div style={{ flex: 1 }}>
        <Editor
          height="100%"
          language={language}
          theme="vs-dark"
          value={code}
          onChange={handleEditorChange}
          onMount={handleEditorDidMount}
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            scrollBeyondLastLine: false,
            automaticLayout: true,
          }}
        />
      </div>
    </div>
  );
};

export default CodeEditor;
