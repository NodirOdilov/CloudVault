import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import { formatRelativeTime } from '../utils/fileHelpers';

interface TrashedItem {
  id: string;
  name: string;
  size_display?: string;
  file_type_category?: string;
  trashed_at?: string;
  updated_at: string;
}

const TrashPage: React.FC = () => {
  const [trashedFiles, setTrashedFiles] = useState<TrashedItem[]>([]);
  const [trashedFolders, setTrashedFolders] = useState<TrashedItem[]>([]);
  const [summary, setSummary] = useState<{
    file_count: number;
    folder_count: number;
    total_size_display: string;
    retention_days: number;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [confirmEmpty, setConfirmEmpty] = useState(false);

  useEffect(() => {
    loadTrash();
  }, []);

  const loadTrash = async () => {
    setIsLoading(true);
    try {
      const [trashResponse, summaryResponse] = await Promise.all([
        apiClient.get('/trash/'),
        apiClient.get('/trash/summary/'),
      ]);
      setTrashedFiles(trashResponse.data.files || []);
      setTrashedFolders(trashResponse.data.folders || []);
      setSummary(summaryResponse.data);
    } catch (err) {
      setError('Failed to load trash');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRestoreFile = async (fileId: string) => {
    try {
      await apiClient.post(`/trash/files/${fileId}/restore/`);
      setTrashedFiles((prev) => prev.filter((f) => f.id !== fileId));
    } catch (err) {
      setError('Failed to restore file');
    }
  };

  const handleDeleteFile = async (fileId: string) => {
    try {
      await apiClient.delete(`/trash/files/${fileId}/delete/`);
      setTrashedFiles((prev) => prev.filter((f) => f.id !== fileId));
    } catch (err) {
      setError('Failed to permanently delete file');
    }
  };

  const handleRestoreFolder = async (folderId: string) => {
    try {
      await apiClient.post(`/trash/folders/${folderId}/restore/`);
      setTrashedFolders((prev) => prev.filter((f) => f.id !== folderId));
    } catch (err) {
      setError('Failed to restore folder');
    }
  };

  const handleDeleteFolder = async (folderId: string) => {
    try {
      await apiClient.delete(`/trash/folders/${folderId}/delete/`);
      setTrashedFolders((prev) => prev.filter((f) => f.id !== folderId));
    } catch (err) {
      setError('Failed to permanently delete folder');
    }
  };

  const handleEmptyTrash = async () => {
    try {
      await apiClient.post('/trash/empty/');
      setTrashedFiles([]);
      setTrashedFolders([]);
      setConfirmEmpty(false);
      loadTrash();
    } catch (err) {
      setError('Failed to empty trash');
    }
  };

  const totalItems = trashedFiles.length + trashedFolders.length;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Trash</h1>
          <p className="text-gray-500 text-sm mt-1">
            {summary
              ? `${summary.file_count} files, ${summary.folder_count} folders (${summary.total_size_display}) - Auto-delete after ${summary.retention_days} days`
              : 'Items moved to trash'}
          </p>
        </div>
        {totalItems > 0 && (
          <button
            onClick={() => setConfirmEmpty(true)}
            className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700"
          >
            Empty Trash
          </button>
        )}
      </div>

      {error && (
        <div className="mb-4 px-4 py-3 bg-red-50 text-red-700 rounded-lg text-sm">
          {error}
          <button onClick={() => setError(null)} className="ml-4 underline">
            Dismiss
          </button>
        </div>
      )}

      {totalItems === 0 ? (
        <div className="text-center py-16 text-gray-500">
          <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          <p className="text-lg font-medium">Trash is empty</p>
          <p className="text-sm mt-1">Items you delete will appear here</p>
        </div>
      ) : (
        <div className="space-y-2">
          {/* Trashed Folders */}
          {trashedFolders.map((folder) => (
            <div
              key={folder.id}
              className="flex items-center justify-between p-4 bg-white border rounded-lg"
            >
              <div className="flex items-center space-x-3">
                <svg className="w-6 h-6 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" />
                </svg>
                <div>
                  <p className="text-sm font-medium text-gray-800">{folder.name}</p>
                  <p className="text-xs text-gray-500">
                    Folder - Deleted {formatRelativeTime(folder.updated_at)}
                  </p>
                </div>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => handleRestoreFolder(folder.id)}
                  className="px-3 py-1.5 text-blue-600 border border-blue-300 rounded text-sm hover:bg-blue-50"
                >
                  Restore
                </button>
                <button
                  onClick={() => handleDeleteFolder(folder.id)}
                  className="px-3 py-1.5 text-red-600 border border-red-300 rounded text-sm hover:bg-red-50"
                >
                  Delete Forever
                </button>
              </div>
            </div>
          ))}

          {/* Trashed Files */}
          {trashedFiles.map((file) => (
            <div
              key={file.id}
              className="flex items-center justify-between p-4 bg-white border rounded-lg"
            >
              <div className="flex items-center space-x-3">
                <div className="w-6 h-6 flex items-center justify-center text-gray-400 text-sm">
                  [F]
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-800">{file.name}</p>
                  <p className="text-xs text-gray-500">
                    {file.size_display || ''} - Deleted{' '}
                    {formatRelativeTime(file.updated_at)}
                  </p>
                </div>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => handleRestoreFile(file.id)}
                  className="px-3 py-1.5 text-blue-600 border border-blue-300 rounded text-sm hover:bg-blue-50"
                >
                  Restore
                </button>
                <button
                  onClick={() => handleDeleteFile(file.id)}
                  className="px-3 py-1.5 text-red-600 border border-red-300 rounded text-sm hover:bg-red-50"
                >
                  Delete Forever
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Confirm Empty Trash Modal */}
      {confirmEmpty && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Empty Trash?
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              This will permanently delete {totalItems} item(s). This action
              cannot be undone.
            </p>
            <div className="flex space-x-3 justify-end">
              <button
                onClick={() => setConfirmEmpty(false)}
                className="px-4 py-2 border rounded-lg text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleEmptyTrash}
                className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700"
              >
                Empty Trash
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TrashPage;
