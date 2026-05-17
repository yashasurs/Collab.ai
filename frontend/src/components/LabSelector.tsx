import { useState, useEffect } from 'react';
import api from '../api';

interface OSOption {
  id: string;
  name: string;
  description: string;
  icon: string;
}

interface LabSelectorProps {
  onSessionCreated: (session: any) => void;
  userId: string;
  username: string;
}

interface Snapshot {
  id: string;
  name: string;
  description: string;
  dockerImage: string;
}

const LabSelector = ({ onSessionCreated, userId, username }: LabSelectorProps) => {
  const [options, setOptions] = useState<OSOption[]>([]);
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [selectedOS, setSelectedOS] = useState<string>('alpine');
  const [selectedSnapshot, setSelectedSnapshot] = useState<Snapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [osRes, snapRes] = await Promise.all([
          api.get('/sessions/os-options'),
          api.get('/snapshots/')
        ]);
        setOptions(osRes.data.osOptions);
        setSnapshots(snapRes.data);
      } catch (err) {
        console.error("Failed to fetch lab options:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleCreate = async () => {
    setCreating(true);
    try {
      const osType = selectedSnapshot ? 'custom' : selectedOS;
      const snapshotId = selectedSnapshot ? selectedSnapshot.dockerImage : null;

      // 1. Create session
      const sessionRes = await api.post('/sessions/create', {
        osType,
        snapshotId,
        userId,
        username
      });
      
      const session = sessionRes.data.session;
      
      // 2. Create container for that session
      const containerRes = await api.post('/containers/', {
        osType,
        snapshotId
      });
      
      const containerId = containerRes.data.containerId;
      
      // 3. Link container to session
      await api.patch(`/sessions/${session.id}`, null, {
        params: { container_id: containerId }
      });
      
      onSessionCreated({ ...session, containerId });
      
    } catch (err) {
      console.error("Failed to create lab:", err);
      alert("Error creating lab environment. Make sure Docker is running.");
    } finally {
      setCreating(false);
    }
  };

  if (loading) return <div>Loading options...</div>;

  return (
    <div className="glass-panel" style={{ padding: '2rem', maxWidth: '800px', width: '100%' }}>
      <h3 style={{ marginBottom: '1.5rem' }} className="gradient-text">Launch Workspace</h3>
      
      <div style={{ marginBottom: '2rem' }}>
        <h4 style={{ opacity: 0.8, marginBottom: '1rem' }}>Standard OS Images</h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.75rem' }}>
          {options.map((os) => (
            <div 
              key={os.id}
              onClick={() => { setSelectedOS(os.id); setSelectedSnapshot(null); }}
              style={{
                padding: '1rem',
                textAlign: 'center',
                cursor: 'pointer',
                border: `2px solid ${!selectedSnapshot && selectedOS === os.id ? 'var(--primary)' : 'var(--border-color)'}`,
                background: !selectedSnapshot && selectedOS === os.id ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
                borderRadius: '12px',
                transition: 'all 0.2s ease'
              }}
            >
              <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{os.icon}</div>
              <div style={{ fontWeight: 'bold', fontSize: '0.9rem' }}>{os.name}</div>
            </div>
          ))}
        </div>
      </div>

      {snapshots.length > 0 && (
        <div style={{ marginBottom: '2rem' }}>
          <h4 style={{ opacity: 0.8, marginBottom: '1rem' }}>Your Snapshots</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            {snapshots.map((snap) => (
              <div 
                key={snap.id}
                onClick={() => { setSelectedSnapshot(snap); }}
                style={{
                  padding: '1rem',
                  cursor: 'pointer',
                  border: `2px solid ${selectedSnapshot?.id === snap.id ? 'var(--primary)' : 'var(--border-color)'}`,
                  background: selectedSnapshot?.id === snap.id ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
                  borderRadius: '12px',
                  transition: 'all 0.2s ease'
                }}
              >
                <div style={{ fontWeight: 'bold' }}>💾 {snap.name}</div>
                <div style={{ fontSize: '0.75rem', opacity: 0.7, marginTop: '0.25rem' }}>{snap.description}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <button 
        className="btn" 
        style={{ width: '100%', padding: '1rem' }} 
        onClick={handleCreate}
        disabled={creating}
      >
        {creating ? 'Spinning up container...' : `Launch ${selectedSnapshot ? 'Snapshot' : selectedOS}`}
      </button>
    </div>
  );
};

export default LabSelector;
