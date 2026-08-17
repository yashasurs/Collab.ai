import { useEffect, useRef, useState } from 'react';
import { useSocket } from '../contexts/SocketContext';

const VideoCall = () => {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [remoteStreams, setRemoteStreams] = useState<Record<string, MediaStream>>({});
  const pcs = useRef<Record<string, RTCPeerConnection>>({});
  const { socket, isConnected } = useSocket();

  useEffect(() => {
    const init = async () => {
      try {
        const s = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        setStream(s);
        streamRef.current = s;
      } catch (err) {
        console.error("Failed to get user media", err);
      }
    };
    init();

    const currentPcs = pcs.current;
    return () => {
      streamRef.current?.getTracks().forEach(t => t.stop());
      Object.values(currentPcs).forEach(pc => pc.close());
    };
  }, []);

  useEffect(() => {
    if (!socket || !isConnected) return;

    const createPeerConnection = (userId: string) => {
      const pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
      });

      pcs.current[userId] = pc;

      streamRef.current?.getTracks().forEach(track => {
        if (streamRef.current) {
           pc.addTrack(track, streamRef.current);
        }
      });

      pc.onicecandidate = (event) => {
        if (event.candidate && socket) {
          socket.emit('webrtc-ice-candidate', { to: userId, candidate: event.candidate });
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
      if (socket) {
          socket.emit('webrtc-offer', { to: userId, offer });
      }
    };

    socket.on('webrtc-offer', async ({ from, offer }: { from: string; offer: RTCSessionDescriptionInit }) => {
      const pc = createPeerConnection(from);
      await pc.setRemoteDescription(new RTCSessionDescription(offer));
      const answer = await pc.createAnswer();
      await pc.setLocalDescription(answer);
      socket.emit('webrtc-answer', { to: from, answer });
    });

    socket.on('webrtc-answer', async ({ from, answer }: { from: string; answer: RTCSessionDescriptionInit }) => {
      const pc = pcs.current[from];
      if (pc) {
        await pc.setRemoteDescription(new RTCSessionDescription(answer));
      }
    });

    socket.on('webrtc-ice-candidate', async ({ from, candidate }: { from: string; candidate: RTCIceCandidateInit }) => {
      const pc = pcs.current[from];
      if (pc) {
        await pc.addIceCandidate(new RTCIceCandidate(candidate));
      }
    });

    socket.on('user-joined-webrtc', (userId: string) => {
      callUser(userId);
    });

    return () => {
      socket.off('webrtc-offer');
      socket.off('webrtc-answer');
      socket.off('webrtc-ice-candidate');
      socket.off('user-joined-webrtc');
    };
  }, [socket, isConnected]);

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
