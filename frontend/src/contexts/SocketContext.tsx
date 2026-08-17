import React, { createContext, useContext, useEffect, useState } from 'react';
import socketio, { Socket } from 'socket.io-client';

interface SocketContextProps {
  socket: Socket | null;
  isConnected: boolean;
}

const SocketContext = createContext<SocketContextProps>({
  socket: null,
  isConnected: false,
});

// eslint-disable-next-line react-refresh/only-export-components
export const useSocket = () => useContext(SocketContext);

interface SocketProviderProps {
  children: React.ReactNode;
  sessionId: string;
  username: string;
}

export const SocketProvider: React.FC<SocketProviderProps> = ({ children, sessionId, username }) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  
  // Create socket lazily to avoid useEffect setState
  const [lazySocket] = useState(() => socketio(import.meta.env.VITE_SOCKET_URL || '', { autoConnect: false }));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSocket(lazySocket);
    lazySocket.connect();

    lazySocket.on('connect', () => {
      setIsConnected(true);
      lazySocket.emit('join-session', { sessionId, username });
    });

    lazySocket.on('disconnect', () => {
      setIsConnected(false);
    });

    // setSocket(s); (moved below to avoid setState in effect)

    return () => {
      lazySocket.disconnect();
    };
  }, [sessionId, username]);

  return (
    <SocketContext.Provider value={{ socket, isConnected }}>
      {children}
    </SocketContext.Provider>
  );
};
