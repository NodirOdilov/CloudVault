import React, { useCallback, useRef, useState } from 'react';
import { useFileStore } from '../../store/fileStore';
import { formatFileSize } from '../../utils/fileHelpers';

interface UploadAreaProps {
  folderId?: string | null;
  onUploadComplete?: () => void;
  maxFileSize?: number; // bytes
}

const UploadArea: React.FC<UploadAreaProps> = ({
  folderId = null,
  onUploadComplete,
  maxFileSize = 524288000, // 500MB
}) => {
  const { uploadFiles, uploadQueue, isUploading } = useFileStore();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  const validateFiles = useCallback(
    (files: File[]): { valid: File[]; errors: string[] } => {
      const valid: File[] = [];
      const errors: string[] = [];

      for (const file of files) {
        if (file.size > maxFileSize) {
          errors.push(
            `"${file.name}" exceeds the ${formatFileSize(maxFileSize)} limit`
          );
        } else if (file.size === 0) {
          errors.push(`"${file.name}" is empty`);
        } else {
          valid.push(file);
        }
      }

      return { valid, errors };
    },
    [maxFileSize]
  );

  const handleFiles = useCallback(
    async (fileList: FileList | File[]) => {
      const files = Array.from(fileList);
      const { valid, errors } = validateFiles(files);

      setValidationErrors(errors);

      if (valid.length > 0) {
        await uploadFiles(valid, folderId);
        onUploadComplete?.();
      }
    },
    [validateFiles, uploadFiles, folderId, onUploadComplete]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      if (e.dataTransfer.files.length > 0) {
        handleFiles(e.dataTransfer.files);
      }
    },
    [handleFiles]
  );

  const handleBrowseClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleFileInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        handleFiles(e.target.files);
        e.target.value = '';
      }
    },
    [handleFiles]
  );

  const completedCount = uploadQueue.filter((q) => q.status === 'complete').length;
  const errorCount = uploadQueue.filter((q) => q.status === 'error').length;

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleBrowseClick}
        className={`relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
          isDragging
            ? 'border-blue-500 bg-blue-50 scale-[1.02]'
            : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileInputChange}
          className="hidden"
        />

        <svg
          className={`w-12 h-12 mx-auto mb-3 transition-colors ${
            isDragging ? 'text-blue-500' : 'text-gray-400'
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>

        <p className="text-lg font-medium text-gray-700 mb-1">
          {isDragging ? 'Drop files here' : 'Drag & drop files here'}
        </p>
        <p className="text-sm text-gray-500">
          or <span className="text-blue-600 font-medium">browse files</span>
        </p>
        <p className="text-xs text-gray-400 mt-2">
          Max file size: {formatFileSize(maxFileSize)}
        </p>
      </div>

      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          {validationErrors.map((error, i) => (
            <p key={i} className="text-sm text-red-600">{error}</p>
          ))}
        </div>
      )}

      {/* Upload Progress */}
      {uploadQueue.length > 0 && (
        <div className="bg-white border rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-medium text-gray-800">
              {isUploading ? 'Uploading...' : 'Upload Complete'}
            </h3>
            <span className="text-sm text-gray-500">
              {completedCount}/{uploadQueue.length} files
              {errorCount > 0 && ` (${errorCount} failed)`}
            </span>
          </div>

          {uploadQueue.map((item, index) => (
            <div key={index} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-700 truncate max-w-xs">
                  {item.file.name}
                </span>
                <span
                  className={`font-medium ${
                    item.status === 'complete'
                      ? 'text-green-600'
                      : item.status === 'error'
                      ? 'text-red-600'
                      : 'text-blue-600'
                  }`}
                >
                  {item.status === 'complete'
                    ? 'Done'
                    : item.status === 'error'
                    ? 'Failed'
                    : item.status === 'uploading'
                    ? `${item.progress}%`
                    : 'Pending'}
                </span>
              </div>

              {item.status === 'uploading' && (
                <div className="w-full bg-gray-200 rounded-full h-1.5">
                  <div
                    className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                    style={{ width: `${item.progress}%` }}
                  />
                </div>
              )}

              {item.status === 'error' && item.error && (
                <p className="text-xs text-red-500">{item.error}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default UploadArea;
