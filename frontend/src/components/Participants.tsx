import { useState, useEffect } from 'react';
import { useSocket } from '../contexts/SocketContext';

interface Participant {
  socketId: string;
  username?: string;
}

const Participants = () => {
  const [participants, setParticipants] = useState<Participant[]>([]);

  const { socket, isConnected } = useSocket();

  useEffect(() => {
    if (!socket || !isConnected) return;

    socket.on('participants-update', (list: Participant[]) => {
      setParticipants(list);
    });

    return () => {
      socket.off('participants-update');
    };
  }, [socket, isConnected]);

  return (
    <div className="glass-panel" style={{ padding: '1rem', marginBottom: '1rem' }}>
      <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem', opacity: 0.8 }}>Collaborators</h4>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
        {participants.map((p) => (
          <div 
            key={p.socketId} 
            title={p.username || 'Anonymous'}
            style={{ 
              width: '32px', 
              height: '32px', 
              borderRadius: '50%', 
              background: 'var(--primary)', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              fontSize: '0.8rem',
              fontWeight: 'bold',
              border: '2px solid var(--border-color)'
            }}
          >
            {(p.username || 'A').charAt(0).toUpperCase()}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Participants;
