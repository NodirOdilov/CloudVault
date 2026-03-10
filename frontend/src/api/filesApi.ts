import apiClient, { uploadClient } from './client';

export interface CloudFile {
  id: string;
  name: string;
  size: number;
  size_display: string;
  mime_type: string;
  extension: string;
  file_type_category: string;
  is_previewable: boolean;
  is_starred: boolean;
  folder: string | null;
  folder_name: string | null;
  current_version: number;
  created_at: string;
  updated_at: string;
}

export interface FileUploadProgress {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'complete' | 'error';
  error?: string;
}

export interface FileListParams {
  folder?: string;
  root?: boolean;
  type?: string;
  starred?: boolean;
  search?: string;
  ordering?: string;
  page?: number;
  page_size?: number;
}

export const filesApi = {
  async listFiles(params: FileListParams = {}) {
    const queryParams: Record<string, string> = {};
    if (params.folder) queryParams.folder = params.folder;
    if (params.root) queryParams.root = 'true';
    if (params.type) queryParams.type = params.type;
    if (params.starred) queryParams.starred = 'true';
    if (params.search) queryParams.search = params.search;
    if (params.ordering) queryParams.ordering = params.ordering;
    if (params.page) queryParams.page = String(params.page);
    if (params.page_size) queryParams.page_size = String(params.page_size);

    const response = await apiClient.get('/files/', { params: queryParams });
    return response.data;
  },

  async getFile(fileId: string) {
    const response = await apiClient.get(`/files/${fileId}/`);
    return response.data;
  },

  async uploadFile(
    file: File,
    folderId?: string | null,
    description?: string,
    onProgress?: (progress: number) => void
  ) {
    const formData = new FormData();
    formData.append('file', file);
    if (folderId) formData.append('folder', folderId);
    if (description) formData.append('description', description);

    const response = await uploadClient.post('/files/upload/', formData, {
      onUploadProgress: (event) => {
        if (event.total && onProgress) {
          const progress = Math.round((event.loaded * 100) / event.total);
          onProgress(progress);
        }
      },
    });
    return response.data;
  },

  async updateFile(fileId: string, data: Partial<CloudFile>) {
    const response = await apiClient.patch(`/files/${fileId}/`, data);
    return response.data;
  },

  async deleteFile(fileId: string) {
    await apiClient.delete(`/files/${fileId}/`);
  },

  async downloadFile(fileId: string) {
    const response = await apiClient.get(`/files/${fileId}/download/`);
    return response.data;
  },

  async previewFile(fileId: string) {
    const response = await apiClient.get(`/files/${fileId}/preview/`);
    return response.data;
  },

  async moveFile(fileId: string, destinationFolder: string | null) {
    const response = await apiClient.post(`/files/${fileId}/move/`, {
      destination_folder: destinationFolder,
    });
    return response.data;
  },

  async copyFile(fileId: string, destinationFolder?: string | null, newName?: string) {
    const response = await apiClient.post(`/files/${fileId}/copy/`, {
      destination_folder: destinationFolder,
      new_name: newName,
    });
    return response.data;
  },

  async toggleStar(fileId: string) {
    const response = await apiClient.post(`/files/${fileId}/star/`);
    return response.data;
  },

  async getVersions(fileId: string) {
    const response = await apiClient.get(`/files/${fileId}/versions/`);
    return response.data;
  },

  async uploadVersion(fileId: string, file: File, comment?: string) {
    const formData = new FormData();
    formData.append('file', file);
    if (comment) formData.append('comment', comment);

    const response = await uploadClient.post(
      `/files/${fileId}/versions/upload/`,
      formData
    );
    return response.data;
  },

  async restoreVersion(fileId: string, versionNumber: number) {
    const response = await apiClient.post(
      `/files/${fileId}/versions/${versionNumber}/restore/`
    );
    return response.data;
  },

  async getRecentFiles() {
    const response = await apiClient.get('/files/recent/');
    return response.data;
  },
};
