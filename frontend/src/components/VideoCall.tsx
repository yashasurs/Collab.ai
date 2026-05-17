import { useEffect, useRef, useState } from 'react';
import socketio from 'socket.io-client';

const VideoCall = ({ sessionId, username }: { sessionId: string, username: string }) => {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [remoteStreams, setRemoteStreams] = useState<Record<string, MediaStream>>({});
  const pcs = useRef<Record<string, RTCPeerConnection>>({});
  const socketRef = useRef<any>(null);

  useEffect(() => {
    const init = async () => {
      const s = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      setStream(s);

      socketRef.current = socketio(import.meta.env.VITE_SOCKET_URL || 'http://localhost:8000', {
        query: { sessionId, username }
      });

      socketRef.current.on('webrtc-offer', async ({ from, offer }: any) => {
        const pc = createPeerConnection(from);
        await pc.setRemoteDescription(new RTCSessionDescription(offer));
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);
        socketRef.current.emit('webrtc-answer', { to: from, answer });
      });

      socketRef.current.on('webrtc-answer', async ({ from, answer }: any) => {
        const pc = pcs.current[from];
        if (pc) {
          await pc.setRemoteDescription(new RTCSessionDescription(answer));
        }
      });

      socketRef.current.on('webrtc-ice-candidate', async ({ from, candidate }: any) => {
        const pc = pcs.current[from];
        if (pc) {
          await pc.addIceCandidate(new RTCIceCandidate(candidate));
        }
      });

      socketRef.current.on('user-joined-webrtc', (userId: string) => {
        callUser(userId);
      });
    };

    init();

    return () => {
      stream?.getTracks().forEach(t => t.stop());
      Object.values(pcs.current).forEach(pc => pc.close());
      socketRef.current?.disconnect();
    };
  }, [sessionId]);

  const createPeerConnection = (userId: string) => {
    const pc = new RTCPeerConnection({
      iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
    });

    pcs.current[userId] = pc;

    stream?.getTracks().forEach(track => pc.addTrack(track, stream));

    pc.onicecandidate = (event) => {
      if (event.candidate) {
        socketRef.current.emit('webrtc-ice-candidate', { to: userId, candidate: event.candidate });
      }
    };

    pc.ontrack = (event) => {
      setRemoteStreams(prev => ({ ...prev, [userId]: event.streams[0] }));
    };

    return pc;
  };

  const callUser = async (userId: string) => {
    const pc = createPeerConnection(userId);
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    socketRef.current.emit('webrtc-offer', { to: userId, offer });
  };

  return (
    <div className="glass-panel" style={{ padding: '1rem', marginTop: '1rem' }}>
      <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem', opacity: 0.8 }}>Video Call</h4>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
        <div style={{ position: 'relative' }}>
          <video 
            autoPlay 
            muted 
            ref={v => { if (v && stream) v.srcObject = stream; }} 
            style={{ width: '100%', borderRadius: '8px', background: '#000' }} 
          />
          <span style={{ position: 'absolute', bottom: '5px', left: '5px', fontSize: '0.7rem', background: 'rgba(0,0,0,0.5)', padding: '2px 4px', borderRadius: '4px' }}>You</span>
        </div>
        {Object.entries(remoteStreams).map(([userId, s]) => (
          <div key={userId} style={{ position: 'relative' }}>
            <video 
              autoPlay 
              ref={v => { if (v) v.srcObject = s; }} 
              style={{ width: '100%', borderRadius: '8px', background: '#000' }} 
            />
          </div>
        ))}
      </div>
    </div>
  );
};

export default VideoCall;
