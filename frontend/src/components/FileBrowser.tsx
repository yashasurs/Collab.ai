import { useState, useEffect } from 'react';
import api from '../api';

interface FileItem {
  name: string;
  isDir: boolean;
  path: string;
}

interface FileBrowserProps {
  containerId: string;
  onFileSelect: (path: string) => void;
}

const FileBrowser = ({ containerId, onFileSelect }: FileBrowserProps) => {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [currentPath, setCurrentPath] = useState('/');
  const [loading, setLoading] = useState(true);

  const fetchFiles = async (path: string) => {
    setLoading(true);
    try {
      const res = await api.get(`/containers/${containerId}/files`, {
        params: { path }
      });
      if (res.data.success) {
        setFiles(res.data.files);
        setCurrentPath(path);
      }
    } catch (err) {
      console.error("Failed to fetch files:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (containerId) {
      fetchFiles('/');
    }
  }, [containerId]);

  const handleItemClick = (item: FileItem) => {
    if (item.isDir) {
      fetchFiles(item.path);
    } else {
      onFileSelect(item.path);
    }
  };

  const goBack = () => {
    if (currentPath === '/') return;
    const parts = currentPath.split('/').filter(Boolean);
    parts.pop();
    fetchFiles('/' + parts.join('/'));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', borderRight: '1px solid var(--border-color)', padding: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h4 style={{ margin: 0 }}>Files</h4>
        {currentPath !== '/' && (
          <button onClick={goBack} style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontSize: '0.8rem' }}>
            ← Back
          </button>
        )}
      </div>
      <div style={{ overflowY: 'auto', flex: 1 }}>
        {loading ? (
          <div style={{ opacity: 0.5, fontSize: '0.8rem' }}>Loading...</div>
        ) : (
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {files.map((file) => (
              <li 
                key={file.path}
                onClick={() => handleItemClick(file)}
                style={{
                  padding: '0.5rem',
                  cursor: 'pointer',
                  borderRadius: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  fontSize: '0.9rem',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <span>{file.isDir ? '📁' : '📄'}</span>
                <span>{file.name}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default FileBrowser;
