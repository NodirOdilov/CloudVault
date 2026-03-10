import { useState, useCallback } from 'react';
import { filesApi, CloudFile } from '../api/filesApi';
import { useFileStore } from '../store/fileStore';

interface FileOperationResult {
  success: boolean;
  message: string;
  data?: any;
}

/**
 * Hook that provides common file operations with loading/error state management.
 * Wraps the file API calls with consistent error handling and store updates.
 */
export function useFileOperations() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [operationError, setOperationError] = useState<string | null>(null);
  const { fetchFiles } = useFileStore();

  const clearOperationError = useCallback(() => {
    setOperationError(null);
  }, []);

  const downloadFile = useCallback(async (file: CloudFile): Promise<FileOperationResult> => {
    setIsProcessing(true);
    setOperationError(null);
    try {
      const data = await filesApi.downloadFile(file.id);
      const link = document.createElement('a');
      link.href = data.download_url;
      link.download = file.name;
      link.target = '_blank';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      return { success: true, message: 'Download started' };
    } catch (err: any) {
      const message = err.response?.data?.message || 'Download failed';
      setOperationError(message);
      return { success: false, message };
    } finally {
      setIsProcessing(false);
    }
  }, []);

  const renameFile = useCallback(
    async (fileId: string, newName: string): Promise<FileOperationResult> => {
      setIsProcessing(true);
      setOperationError(null);
      try {
        await filesApi.updateFile(fileId, { name: newName });
        return { success: true, message: 'File renamed' };
      } catch (err: any) {
        const message = err.response?.data?.message || 'Rename failed';
        setOperationError(message);
        return { success: false, message };
      } finally {
        setIsProcessing(false);
      }
    },
    []
  );

  const moveFile = useCallback(
    async (fileId: string, folderId: string | null): Promise<FileOperationResult> => {
      setIsProcessing(true);
      setOperationError(null);
      try {
        await filesApi.moveFile(fileId, folderId);
        return { success: true, message: 'File moved' };
      } catch (err: any) {
        const message = err.response?.data?.message || 'Move failed';
        setOperationError(message);
        return { success: false, message };
      } finally {
        setIsProcessing(false);
      }
    },
    []
  );

  const copyFile = useCallback(
    async (
      fileId: string,
      folderId?: string | null,
      newName?: string
    ): Promise<FileOperationResult> => {
      setIsProcessing(true);
      setOperationError(null);
      try {
        const data = await filesApi.copyFile(fileId, folderId, newName);
        return { success: true, message: 'File copied', data };
      } catch (err: any) {
        const message = err.response?.data?.message || 'Copy failed';
        setOperationError(message);
        return { success: false, message };
      } finally {
        setIsProcessing(false);
      }
    },
    []
  );

  const deleteFile = useCallback(
    async (fileId: string): Promise<FileOperationResult> => {
      setIsProcessing(true);
      setOperationError(null);
      try {
        await filesApi.deleteFile(fileId);
        return { success: true, message: 'File moved to trash' };
      } catch (err: any) {
        const message = err.response?.data?.message || 'Delete failed';
        setOperationError(message);
        return { success: false, message };
      } finally {
        setIsProcessing(false);
      }
    },
    []
  );

  const toggleStar = useCallback(
    async (fileId: string): Promise<FileOperationResult> => {
      try {
        const data = await filesApi.toggleStar(fileId);
        return {
          success: true,
          message: data.is_starred ? 'File starred' : 'Star removed',
          data,
        };
      } catch (err: any) {
        const message = err.response?.data?.message || 'Failed to toggle star';
        setOperationError(message);
        return { success: false, message };
      }
    },
    []
  );

  const uploadNewVersion = useCallback(
    async (
      fileId: string,
      file: File,
      comment?: string
    ): Promise<FileOperationResult> => {
      setIsProcessing(true);
      setOperationError(null);
      try {
        const data = await filesApi.uploadVersion(fileId, file, comment);
        return { success: true, message: 'New version uploaded', data };
      } catch (err: any) {
        const message = err.response?.data?.message || 'Version upload failed';
        setOperationError(message);
        return { success: false, message };
      } finally {
        setIsProcessing(false);
      }
    },
    []
  );

  const restoreVersion = useCallback(
    async (
      fileId: string,
      versionNumber: number
    ): Promise<FileOperationResult> => {
      setIsProcessing(true);
      setOperationError(null);
      try {
        const data = await filesApi.restoreVersion(fileId, versionNumber);
        return { success: true, message: `Restored to version ${versionNumber}`, data };
      } catch (err: any) {
        const message = err.response?.data?.message || 'Version restore failed';
        setOperationError(message);
        return { success: false, message };
      } finally {
        setIsProcessing(false);
      }
    },
    []
  );

  const batchDelete = useCallback(
    async (fileIds: string[]): Promise<FileOperationResult> => {
      setIsProcessing(true);
      setOperationError(null);
      let successCount = 0;
      let failCount = 0;

      for (const id of fileIds) {
        try {
          await filesApi.deleteFile(id);
          successCount++;
        } catch {
          failCount++;
        }
      }

      setIsProcessing(false);

      if (failCount === 0) {
        return { success: true, message: `${successCount} files moved to trash` };
      }
      const message = `${successCount} moved to trash, ${failCount} failed`;
      setOperationError(message);
      return { success: failCount === 0, message };
    },
    []
  );

  return {
    isProcessing,
    operationError,
    clearOperationError,
    downloadFile,
    renameFile,
    moveFile,
    copyFile,
    deleteFile,
    toggleStar,
    uploadNewVersion,
    restoreVersion,
    batchDelete,
  };
}
