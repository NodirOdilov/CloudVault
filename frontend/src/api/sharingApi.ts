import apiClient from './client';

export interface FileShare {
  id: string;
  file: string;
  shared_by: any;
  shared_with: any;
  permission: string;
  created_at: string;
}

export interface SharedLink {
  id: string;
  file: string;
  file_name: string;
  token: string;
  permission: string;
  is_active: boolean;
  is_expired: boolean;
  is_accessible: boolean;
  url: string;
  download_count: number;
  max_downloads: number | null;
  expires_at: string | null;
  created_at: string;
}

export interface ShareInvitation {
  id: string;
  invited_by: any;
  invited_email: string;
  file: string | null;
  folder: string | null;
  file_name: string | null;
  folder_name: string | null;
  permission: string;
  message: string;
  status: string;
  is_expired: boolean;
  expires_at: string;
  created_at: string;
}

export const sharingApi = {
  async shareFile(fileId: string, email: string, permission: string = 'view') {
    const response = await apiClient.post(`/sharing/files/${fileId}/share/`, {
      email,
      permission,
    });
    return response.data;
  },

  async getFileShares(fileId: string) {
    const response = await apiClient.get(`/sharing/files/${fileId}/shares/`);
    return response.data;
  },

  async revokeShare(shareId: string) {
    await apiClient.delete(`/sharing/shares/${shareId}/revoke/`);
  },

  async getSharedWithMe() {
    const response = await apiClient.get('/sharing/shared-with-me/');
    return response.data;
  },

  async getSharedByMe() {
    const response = await apiClient.get('/sharing/shared-by-me/');
    return response.data;
  },

  async createSharedLink(data: {
    file_id: string;
    permission?: string;
    password?: string;
    expires_in_hours?: number | null;
    max_downloads?: number | null;
  }) {
    const response = await apiClient.post('/sharing/links/', data);
    return response.data;
  },

  async getSharedLink(linkId: string) {
    const response = await apiClient.get(`/sharing/links/${linkId}/`);
    return response.data;
  },

  async deactivateSharedLink(linkId: string) {
    await apiClient.delete(`/sharing/links/${linkId}/`);
  },

  async accessSharedLink(token: string, password?: string) {
    if (password) {
      const response = await apiClient.post(`/sharing/access/${token}/`, { password });
      return response.data;
    }
    const response = await apiClient.get(`/sharing/access/${token}/`);
    return response.data;
  },

  async sendInvitation(data: {
    invited_email: string;
    file_id?: string;
    folder_id?: string;
    permission?: string;
    message?: string;
    expires_in_days?: number;
  }) {
    const response = await apiClient.post('/sharing/invitations/send/', data);
    return response.data;
  },

  async getInvitations() {
    const response = await apiClient.get('/sharing/invitations/');
    return response.data;
  },

  async respondToInvitation(invitationId: string, action: 'accept' | 'decline') {
    const response = await apiClient.post(
      `/sharing/invitations/${invitationId}/respond/`,
      { action }
    );
    return response.data;
  },
};
