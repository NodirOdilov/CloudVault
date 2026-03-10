import React, { useEffect, useState, useCallback } from 'react';
import { filesApi } from '../../api/filesApi';
import { CloudFile } from '../../api/filesApi';

interface PreviewViewerProps {
  file: CloudFile;
  isOpen: boolean;
  onClose: () => void;
  onDownload?: (file: CloudFile) => void;
}

interface PreviewData {
  preview_type: string;
  url?: string;
  content?: string;
  mime_type: string;
  name: string;
  size?: number;
  truncated?: boolean;
}

const PreviewViewer: React.FC<PreviewViewerProps> = ({
  file,
  isOpen,
  onClose,
  onDownload,
}) => {
  const [previewData, setPreviewData] = useState<PreviewData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && file.is_previewable) {
      loadPreview();
    }
    return () => {
      setPreviewData(null);
      setError(null);
    };
  }, [isOpen, file.id]);

  const loadPreview = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await filesApi.previewFile(file.id);
      setPreviewData(data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Preview not available');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = useCallback(async () => {
    if (onDownload) {
      onDownload(file);
    } else {
      try {
        const data = await filesApi.downloadFile(file.id);
        window.open(data.download_url, '_blank');
      } catch (err) {
        setError('Failed to start download');
      }
    }
  }, [file, onDownload]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    },
    [onClose]
  );

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'auto';
    };
  }, [isOpen, handleKeyDown]);

  if (!isOpen) return null;

  const renderPreviewContent = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-white" />
        </div>
      );
    }

    if (error || !file.is_previewable) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-white">
          <svg className="w-20 h-20 mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="text-lg font-medium">{error || 'Preview not available'}</p>
          <p className="text-sm text-gray-400 mt-1">
            You can still download this file
          </p>
          <button
            onClick={handleDownload}
            className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Download File
          </button>
        </div>
      );
    }

    if (!previewData) return null;

    switch (previewData.preview_type) {
      case 'image':
        return (
          <div className="flex items-center justify-center h-full p-4">
            <img
              src={previewData.url}
              alt={previewData.name}
              className="max-h-full max-w-full object-contain rounded shadow-lg"
              loading="lazy"
            />
          </div>
        );

      case 'pdf':
        return (
          <iframe
            src={previewData.url}
            className="w-full h-full rounded"
            title={previewData.name}
          />
        );

      case 'text':
        return (
          <div className="h-full overflow-auto p-6">
            <pre className="text-sm text-gray-200 font-mono whitespace-pre-wrap bg-gray-900 p-4 rounded-lg">
              {previewData.content}
            </pre>
            {previewData.truncated && (
              <p className="text-yellow-400 text-sm mt-2 text-center">
                File truncated for preview. Download to view the full content.
              </p>
            )}
          </div>
        );

      case 'audio':
        return (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="w-64 h-64 bg-gray-800 rounded-full flex items-center justify-center mb-6">
              <svg className="w-24 h-24 text-blue-400" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z" />
              </svg>
            </div>
            <audio
              controls
              src={previewData.url}
              className="w-96"
              preload="metadata"
            >
              Your browser does not support audio playback.
            </audio>
          </div>
        );

      case 'video':
        return (
          <div className="flex items-center justify-center h-full p-4">
            <video
              controls
              src={previewData.url}
              className="max-h-full max-w-full rounded shadow-lg"
              preload="metadata"
            >
              Your browser does not support video playback.
            </video>
          </div>
        );

      default:
        return (
          <div className="flex flex-col items-center justify-center h-full text-white">
            <p>Preview not supported for this file type</p>
          </div>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/90 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-black/50">
        <div className="flex items-center space-x-4">
          <h2 className="text-white font-medium text-lg truncate max-w-md">
            {file.name}
          </h2>
          <span className="text-gray-400 text-sm">
            {file.size_display}
          </span>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleDownload}
            className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
          >
            Download
          </button>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-white transition-colors"
            aria-label="Close preview"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {/* Preview Content */}
      <div className="flex-1 overflow-hidden">
        {renderPreviewContent()}
      </div>
    </div>
  );
};

export default PreviewViewer;
