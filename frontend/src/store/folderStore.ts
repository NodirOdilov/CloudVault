import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { foldersApi, Folder, FolderTreeNode, FolderContents } from '../api/foldersApi';

interface FolderState {
  folders: Folder[];
  currentFolder: Folder | null;
  folderContents: FolderContents | null;
  folderTree: FolderTreeNode[];
  breadcrumb: Array<{ id: string; name: string }>;
  isLoading: boolean;
  error: string | null;

  fetchFolders: (params?: { parent?: string; root?: boolean }) => Promise<void>;
  fetchFolderContents: (folderId: string) => Promise<void>;
  fetchFolderTree: () => Promise<void>;
  createFolder: (data: { name: string; parent?: string | null; color?: string }) => Promise<Folder>;
  renameFolder: (folderId: string, newName: string) => Promise<void>;
  deleteFolder: (folderId: string) => Promise<void>;
  moveFolder: (folderId: string, destinationId: string | null) => Promise<void>;
  toggleStar: (folderId: string) => Promise<void>;
  navigateToFolder: (folderId: string | null) => void;
  clearError: () => void;
}

export const useFolderStore = create<FolderState>()(
  devtools(
    (set, get) => ({
      folders: [],
      currentFolder: null,
      folderContents: null,
      folderTree: [],
      breadcrumb: [],
      isLoading: false,
      error: null,

      fetchFolders: async (params = {}) => {
        set({ isLoading: true, error: null });
        try {
          const data = await foldersApi.listFolders(params);
          set({
            folders: data.results || data,
            isLoading: false,
          });
        } catch (err: any) {
          set({
            error: err.response?.data?.message || 'Failed to fetch folders',
            isLoading: false,
          });
        }
      },

      fetchFolderContents: async (folderId: string) => {
        set({ isLoading: true, error: null });
        try {
          const contents = await foldersApi.getFolderContents(folderId);
          set({
            folderContents: contents,
            currentFolder: contents.folder,
            breadcrumb: contents.breadcrumb,
            isLoading: false,
          });
        } catch (err: any) {
          set({
            error: err.response?.data?.message || 'Failed to fetch folder contents',
            isLoading: false,
          });
        }
      },

      fetchFolderTree: async () => {
        try {
          const tree = await foldersApi.getFolderTree();
          set({ folderTree: tree });
        } catch (err: any) {
          set({ error: err.response?.data?.message || 'Failed to fetch folder tree' });
        }
      },

      createFolder: async (data) => {
        try {
          const folder = await foldersApi.createFolder(data);
          set((state) => ({
            folders: [...state.folders, folder],
          }));
          get().fetchFolderTree();
          return folder;
        } catch (err: any) {
          set({ error: err.response?.data?.message || 'Failed to create folder' });
          throw err;
        }
      },

      renameFolder: async (folderId, newName) => {
        try {
          const updated = await foldersApi.updateFolder(folderId, { name: newName });
          set((state) => ({
            folders: state.folders.map((f) =>
              f.id === folderId ? { ...f, ...updated } : f
            ),
          }));
          get().fetchFolderTree();
        } catch (err: any) {
          set({ error: err.response?.data?.message || 'Failed to rename folder' });
        }
      },

      deleteFolder: async (folderId) => {
        try {
          await foldersApi.deleteFolder(folderId);
          set((state) => ({
            folders: state.folders.filter((f) => f.id !== folderId),
          }));
          get().fetchFolderTree();
        } catch (err: any) {
          set({ error: err.response?.data?.message || 'Failed to delete folder' });
        }
      },

      moveFolder: async (folderId, destinationId) => {
        try {
          await foldersApi.moveFolder(folderId, destinationId);
          set((state) => ({
            folders: state.folders.filter((f) => f.id !== folderId),
          }));
          get().fetchFolderTree();
        } catch (err: any) {
          set({ error: err.response?.data?.message || 'Failed to move folder' });
        }
      },

      toggleStar: async (folderId) => {
        try {
          const result = await foldersApi.toggleStar(folderId);
          set((state) => ({
            folders: state.folders.map((f) =>
              f.id === folderId ? { ...f, is_starred: result.is_starred } : f
            ),
          }));
        } catch (err: any) {
          set({ error: err.response?.data?.message || 'Failed to toggle star' });
        }
      },

      navigateToFolder: (folderId) => {
        if (folderId) {
          get().fetchFolderContents(folderId);
        } else {
          set({ currentFolder: null, breadcrumb: [], folderContents: null });
          get().fetchFolders({ root: true });
        }
      },

      clearError: () => set({ error: null }),
    }),
    { name: 'folder-store' }
  )
);
