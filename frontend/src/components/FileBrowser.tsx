import { useState, useEffect, useCallback } from 'react';
import api from '../api';

interface FileItem {
  name: string;
  isDir: boolean;
  path: string;
}

interface FileBrowserProps {
  containerId: string | undefined;
  onFileSelect: (path: string) => void;
}

const FileBrowser = ({ containerId, onFileSelect }: FileBrowserProps) => {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [currentPath, setCurrentPath] = useState('/');
  const [loading, setLoading] = useState(true);

  const fetchFiles = useCallback(async (path: string) => {
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
  }, [containerId]);

  useEffect(() => {
    if (containerId) {
      fetchFiles('/');
    }
  }, [containerId, fetchFiles]);

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
    <div className="flex flex-col h-full p-4 text-slate-300">
      <div className="flex justify-between items-center mb-4">
        <h4 className="m-0 text-sm font-bold uppercase tracking-wider text-slate-400">Files</h4>
        {currentPath !== '/' && (
          <button
            onClick={goBack}
            className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors font-medium bg-transparent border-none cursor-pointer"
          >
            ← Back
          </button>
        )}
      </div>
      <div className="overflow-y-auto flex-1 custom-scrollbar -mx-2 px-2">
        {loading ? (
          <div className="opacity-50 text-xs">Loading...</div>
        ) : files.length === 0 ? (
          <div className="opacity-50 text-xs italic">No files found</div>
        ) : (
          <ul className="list-none p-0 m-0 space-y-1">
            {files.map((file) => (
              <li
                key={file.path}
                onClick={() => handleItemClick(file)}
                className="p-2 cursor-pointer rounded-md flex items-center gap-3 text-sm overflow-hidden text-ellipsis whitespace-nowrap hover:bg-white/5 transition-colors"
              >
                <span className="text-lg opacity-80">{file.isDir ? '📁' : '📄'}</span>
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
