import React, { useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import FileBrowser from '../components/files/FileBrowser';
import UploadArea from '../components/files/UploadArea';
import PreviewViewer from '../components/files/PreviewViewer';
import SharingModal from '../components/sharing/SharingModal';
import { CloudFile } from '../api/filesApi';
import { useFileStore } from '../store/fileStore';
import { useFolderStore } from '../store/folderStore';

const FilesPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const folderId = searchParams.get('folder');

  const [showUpload, setShowUpload] = useState(false);
  const [previewFile, setPreviewFile] = useState<CloudFile | null>(null);
  const [sharingFile, setSharingFile] = useState<CloudFile | null>(null);
  const [showNewFolder, setShowNewFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');

  const { fetchFiles } = useFileStore();
  const { createFolder, currentFolder } = useFolderStore();

  const handleFileOpen = useCallback((file: CloudFile) => {
    if (file.is_previewable) {
      setPreviewFile(file);
    }
  }, []);

  const handleCreateFolder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFolderName.trim()) return;

    try {
      await createFolder({
        name: newFolderName.trim(),
        parent: folderId,
      });
      setNewFolderName('');
      setShowNewFolder(false);
      fetchFiles({ folder: folderId || undefined, root: !folderId });
    } catch (err) {
      // Error handled in store
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      {/* Page Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {currentFolder ? currentFolder.name : 'My Files'}
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Manage and organize your files
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowNewFolder(true)}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm hover:bg-gray-50"
          >
            New Folder
          </button>
          <button
            onClick={() => setShowUpload(!showUpload)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
          >
            Upload Files
          </button>
        </div>
      </div>

      {/* Upload Area */}
      {showUpload && (
        <div className="mb-6">
          <UploadArea
            folderId={folderId}
            onUploadComplete={() => {
              fetchFiles({ folder: folderId || undefined, root: !folderId });
            }}
          />
        </div>
      )}

      {/* New Folder Dialog */}
      {showNewFolder && (
        <div className="mb-4 p-4 bg-gray-50 border rounded-lg">
          <form onSubmit={handleCreateFolder} className="flex items-center space-x-3">
            <input
              type="text"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              placeholder="Folder name"
              className="flex-1 border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm"
            >
              Create
            </button>
            <button
              type="button"
              onClick={() => setShowNewFolder(false)}
              className="px-4 py-2 border rounded-lg text-sm"
            >
              Cancel
            </button>
          </form>
        </div>
      )}

      {/* File Browser */}
      <FileBrowser
        folderId={folderId}
        onFileOpen={handleFileOpen}
        onFileSelect={(file) => {/* optional selection handler */}}
      />

      {/* Preview Overlay */}
      {previewFile && (
        <PreviewViewer
          file={previewFile}
          isOpen={!!previewFile}
          onClose={() => setPreviewFile(null)}
        />
      )}

      {/* Sharing Modal */}
      {sharingFile && (
        <SharingModal
          file={sharingFile}
          isOpen={!!sharingFile}
          onClose={() => setSharingFile(null)}
        />
      )}
    </div>
  );
};

export default FilesPage;
