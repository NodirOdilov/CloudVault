import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { filesApi, CloudFile, FileListParams } from '../api/filesApi';

interface FileState {
  files: CloudFile[];
  currentFile: CloudFile | null;
  isLoading: boolean;
  error: string | null;
  totalCount: number;
  currentPage: number;
  pageSize: number;
  sortField: string;
  sortDirection: 'asc' | 'desc';
  viewMode: 'grid' | 'list';
  selectedFiles: Set<string>;

  // Upload state
  uploadQueue: Array<{
    file: File;
    progress: number;
    status: 'pending' | 'uploading' | 'complete' | 'error';
    error?: string;
  }>;
  isUploading: boolean;

  // Actions
  fetchFiles: (params?: FileListParams) => Promise<void>;
  fetchFile: (fileId: string) => Promise<void>;
  uploadFiles: (files: File[], folderId?: string | null) => Promise<void>;
  deleteFile: (fileId: string) => Promise<void>;
  renameFile: (fileId: string, newName: string) => Promise<void>;
  toggleStar: (fileId: string) => Promise<void>;
  moveFile: (fileId: string, folderId: string | null) => Promise<void>;
  setViewMode: (mode: 'grid' | 'list') => void;
  setSorting: (field: string, direction: 'asc' | 'desc') => void;
  toggleFileSelection: (fileId: string) => void;
  selectAllFiles: () => void;
  clearSelection: () => void;
  clearError: () => void;
}

export const useFileStore = create<FileState>()(
  devtools(
    (set, get) => ({
      files: [],
      currentFile: null,
      isLoading: false,
      error: null,
      totalCount: 0,
      currentPage: 1,
      pageSize: 25,
      sortField: 'updated_at',
      sortDirection: 'desc',
      viewMode: (localStorage.getItem('file_view_mode') as 'grid' | 'list') || 'grid',
      selectedFiles: new Set<string>(),

      uploadQueue: [],
      isUploading: false,

      fetchFiles: async (params = {}) => {
        set({ isLoading: true, error: null });
        try {
          const { sortField, sortDirection } = get();
          const ordering = sortDirection === 'desc' ? `-${sortField}` : sortField;
          const data = await filesApi.listFiles({ ...params, ordering });
          set({
            files: data.results || data,
            totalCount: data.count || (data.results || data).length,
            isLoading: false,
          });
        } catch (err: any) {
          set({
            error: err.response?.data?.message || 'Failed to fetch files',
            isLoading: false,
          });
        }
      },

      fetchFile: async (fileId: string) => {
        set({ isLoading: true, error: null });
        try {
          const data = await filesApi.getFile(fileId);
          set({ currentFile: data, isLoading: false });
        } catch (err: any) {
          set({
            error: err.response?.data?.message || 'Failed to fetch file',
            isLoading: false,
          });
        }
      },

      uploadFiles: async (files: File[], folderId?: string | null) => {
        const queue = files.map((file) => ({
          file,
          progress: 0,
          status: 'pending' as const,
        }));
        set({ uploadQueue: queue, isUploading: true });

        for (let i = 0; i < queue.length; i++) {
          set((state) => {
            const newQueue = [...state.uploadQueue];
            newQueue[i] = { ...newQueue[i], status: 'uploading' };
            return { uploadQueue: newQueue };
          });

          try {
            await filesApi.uploadFile(
              queue[i].file,
              folderId,
              undefined,
              (progress) => {
                set((state) => {
                  const newQueue = [...state.uploadQueue];
                  newQueue[i] = { ...newQueue[i], progress };
                  return { uploadQueue: newQueue };
                });
              }
            );

            set((state) => {
              const newQueue = [...state.uploadQueue];
              newQueue[i] = { ...newQueue[i], status: 'complete', progress: 100 };
              return { uploadQueue: newQueue };
            });
          } catch (err: any) {
            set((state) => {
              const newQueue = [...state.uploadQueue];
              newQueue[i] = {
                ...newQueue[i],
                status: 'error',
                error: err.response?.data?.message || 'Upload failed',
              };
              return { uploadQueue: newQueue };
            });
          }
        }

        set({ isUploading: false });
      },

      deleteFile: async (fileId: string) => {
        try {
          await filesApi.deleteFile(fileId);
          set((state) => ({
            files: state.files.filter((f) => f.id !== fileId),
            selectedFiles: new Set(
              [...state.selectedFiles].filter((id) => id !== fileId)
            ),
          }));
        } catch (err: any) {
          set({ error: err.response?.data?.message || 'Failed to delete file' });
        }
      },

      renameFile: async (fileId: string, newName: string) => {
        try {
          const updated = await filesApi.updateFile(fileId, { name: newName });
          set((state) => ({
            files: state.files.map((f) => (f.id === fileId ? { ...f, ...updated } : f)),
          }));
        } catch (err: any) {
          set({ error: err.response?.data?.message || 'Failed to rename file' });
        }
      },

      toggleStar: async (fileId: string) => {
        try {
          const result = await filesApi.toggleStar(fileId);
          set((state) => ({
            files: state.files.map((f) =>
              f.id === fileId ? { ...f, is_starred: result.is_starred } : f
            ),
          }));
        } catch (err: any) {
          set({ error: err.response?.data?.message || 'Failed to toggle star' });
        }
      },

      moveFile: async (fileId: string, folderId: string | null) => {
        try {
          await filesApi.moveFile(fileId, folderId);
          set((state) => ({
            files: state.files.filter((f) => f.id !== fileId),
          }));
        } catch (err: any) {
          set({ error: err.response?.data?.message || 'Failed to move file' });
        }
      },

      setViewMode: (mode) => {
        localStorage.setItem('file_view_mode', mode);
        set({ viewMode: mode });
      },

      setSorting: (field, direction) => {
        set({ sortField: field, sortDirection: direction });
      },

      toggleFileSelection: (fileId: string) => {
        set((state) => {
          const newSelection = new Set(state.selectedFiles);
          if (newSelection.has(fileId)) {
            newSelection.delete(fileId);
          } else {
            newSelection.add(fileId);
          }
          return { selectedFiles: newSelection };
        });
      },

      selectAllFiles: () => {
        set((state) => ({
          selectedFiles: new Set(state.files.map((f) => f.id)),
        }));
      },

      clearSelection: () => {
        set({ selectedFiles: new Set() });
      },

      clearError: () => set({ error: null }),
    }),
    { name: 'file-store' }
  )
);
