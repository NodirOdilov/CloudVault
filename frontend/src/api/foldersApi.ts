import apiClient from './client';

export interface Folder {
  id: string;
  parent: string | null;
  name: string;
  color: string;
  description: string;
  path: string;
  breadcrumb: Array<{ id: string; name: string }>;
  depth: number;
  total_size: number;
  file_count: number;
  subfolder_count: number;
  is_starred: boolean;
  created_at: string;
  updated_at: string;
}

export interface FolderTreeNode {
  id: string;
  name: string;
  color: string;
  children: FolderTreeNode[];
  file_count: number;
}

export interface FolderContents {
  folder: Folder;
  subfolders: Folder[];
  files: any[];
  breadcrumb: Array<{ id: string; name: string }>;
}

export const foldersApi = {
  async listFolders(params: { parent?: string; root?: boolean; starred?: boolean } = {}) {
    const queryParams: Record<string, string> = {};
    if (params.parent) queryParams.parent = params.parent;
    if (params.root) queryParams.root = 'true';
    if (params.starred) queryParams.starred = 'true';

    const response = await apiClient.get('/folders/', { params: queryParams });
    return response.data;
  },

  async getFolder(folderId: string) {
    const response = await apiClient.get(`/folders/${folderId}/`);
    return response.data;
  },

  async createFolder(data: { name: string; parent?: string | null; color?: string; description?: string }) {
    const response = await apiClient.post('/folders/', data);
    return response.data;
  },

  async updateFolder(folderId: string, data: Partial<Folder>) {
    const response = await apiClient.patch(`/folders/${folderId}/`, data);
    return response.data;
  },

  async deleteFolder(folderId: string) {
    await apiClient.delete(`/folders/${folderId}/`);
  },

  async getFolderContents(folderId: string): Promise<FolderContents> {
    const response = await apiClient.get(`/folders/${folderId}/contents/`);
    return response.data;
  },

  async moveFolder(folderId: string, destinationParent: string | null) {
    const response = await apiClient.post(`/folders/${folderId}/move/`, {
      destination_parent: destinationParent,
    });
    return response.data;
  },

  async toggleStar(folderId: string) {
    const response = await apiClient.post(`/folders/${folderId}/star/`);
    return response.data;
  },

  async getFolderTree(): Promise<FolderTreeNode[]> {
    const response = await apiClient.get('/folders/tree/');
    return response.data;
  },
};
