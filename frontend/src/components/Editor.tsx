import Editor from '@monaco-editor/react';
import { useEffect, useRef, useState } from 'react';
import { io, Socket } from 'socket.io-client';

interface CodeEditorProps {
  sessionId: string;
  initialCode?: string;
}

const CodeEditor = ({ sessionId, initialCode = '' }: CodeEditorProps) => {
  const [code, setCode] = useState(initialCode);
  const socketRef = useRef<Socket | null>(null);
  const isRemoteChange = useRef(false);

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

  return (
    <div style={{ height: '100%', width: '100%', borderRadius: '8px', overflow: 'hidden' }}>
      <Editor
        height="100%"
        defaultLanguage="python"
        theme="vs-dark"
        value={code}
        onChange={handleEditorChange}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          scrollBeyondLastLine: false,
          automaticLayout: true,
        }}
      />
    </div>
  );
};

export default CodeEditor;
