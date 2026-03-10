import React, { useState, useEffect } from 'react';
import { sharingApi, FileShare, ShareInvitation } from '../api/sharingApi';
import { formatRelativeTime } from '../utils/fileHelpers';

type SharedTab = 'shared-with-me' | 'shared-by-me' | 'invitations';

const SharedPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<SharedTab>('shared-with-me');
  const [sharedWithMe, setSharedWithMe] = useState<FileShare[]>([]);
  const [sharedByMe, setSharedByMe] = useState<FileShare[]>([]);
  const [invitations, setInvitations] = useState<ShareInvitation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      switch (activeTab) {
        case 'shared-with-me': {
          const data = await sharingApi.getSharedWithMe();
          setSharedWithMe(data.results || data);
          break;
        }
        case 'shared-by-me': {
          const data = await sharingApi.getSharedByMe();
          setSharedByMe(data.results || data);
          break;
        }
        case 'invitations': {
          const data = await sharingApi.getInvitations();
          setInvitations(data.results || data);
          break;
        }
      }
    } catch (err: any) {
      setError('Failed to load shared items');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInvitationResponse = async (
    invitationId: string,
    action: 'accept' | 'decline'
  ) => {
    try {
      await sharingApi.respondToInvitation(invitationId, action);
      setInvitations((prev) => prev.filter((inv) => inv.id !== invitationId));
    } catch (err: any) {
      setError(err.response?.data?.error || `Failed to ${action} invitation`);
    }
  };

  const handleRevokeShare = async (shareId: string) => {
    try {
      await sharingApi.revokeShare(shareId);
      setSharedByMe((prev) => prev.filter((s) => s.id !== shareId));
    } catch {
      setError('Failed to revoke share');
    }
  };

  const permissionBadge = (permission: string) => {
    const colors: Record<string, string> = {
      view: 'bg-gray-100 text-gray-700',
      edit: 'bg-blue-100 text-blue-700',
      download: 'bg-green-100 text-green-700',
    };
    return (
      <span
        className={`px-2 py-0.5 rounded-full text-xs font-medium capitalize ${
          colors[permission] || colors.view
        }`}
      >
        {permission}
      </span>
    );
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Shared Files</h1>

      {/* Tabs */}
      <div className="flex space-x-1 bg-gray-100 rounded-lg p-1 mb-6 w-fit">
        {([
          { key: 'shared-with-me', label: 'Shared with Me' },
          { key: 'shared-by-me', label: 'Shared by Me' },
          { key: 'invitations', label: 'Invitations' },
        ] as const).map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            {tab.label}
            {tab.key === 'invitations' && invitations.length > 0 && (
              <span className="ml-1.5 bg-red-500 text-white text-xs rounded-full px-1.5 py-0.5">
                {invitations.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {error && (
        <div className="mb-4 px-4 py-3 bg-red-50 text-red-700 rounded-lg text-sm">
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center h-48">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      ) : (
        <div className="space-y-3">
          {activeTab === 'shared-with-me' &&
            (sharedWithMe.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <p className="text-lg font-medium">No files shared with you</p>
                <p className="text-sm mt-1">
                  Files that others share with you will appear here
                </p>
              </div>
            ) : (
              sharedWithMe.map((share) => (
                <div
                  key={share.id}
                  className="flex items-center justify-between p-4 bg-white border rounded-lg hover:shadow-sm"
                >
                  <div className="flex items-center space-x-4">
                    <div className="w-10 h-10 rounded bg-blue-100 flex items-center justify-center text-blue-600 text-sm font-medium">
                      F
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-800">
                        {share.shared_by?.full_name || share.shared_by?.email}
                      </p>
                      <p className="text-xs text-gray-500">
                        Shared {formatRelativeTime(share.created_at)}
                      </p>
                    </div>
                  </div>
                  {permissionBadge(share.permission)}
                </div>
              ))
            ))}

          {activeTab === 'shared-by-me' &&
            (sharedByMe.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <p className="text-lg font-medium">You have not shared any files</p>
                <p className="text-sm mt-1">
                  Share files from the file browser to see them here
                </p>
              </div>
            ) : (
              sharedByMe.map((share) => (
                <div
                  key={share.id}
                  className="flex items-center justify-between p-4 bg-white border rounded-lg hover:shadow-sm"
                >
                  <div className="flex items-center space-x-4">
                    <div className="w-10 h-10 rounded bg-green-100 flex items-center justify-center text-green-600 text-sm font-medium">
                      F
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-800">
                        Shared with {share.shared_with?.email || 'Unknown'}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatRelativeTime(share.created_at)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    {permissionBadge(share.permission)}
                    <button
                      onClick={() => handleRevokeShare(share.id)}
                      className="text-red-500 hover:text-red-700 text-sm"
                    >
                      Revoke
                    </button>
                  </div>
                </div>
              ))
            ))}

          {activeTab === 'invitations' &&
            (invitations.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <p className="text-lg font-medium">No pending invitations</p>
              </div>
            ) : (
              invitations.map((invitation) => (
                <div
                  key={invitation.id}
                  className="p-4 bg-white border rounded-lg"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-800">
                        {invitation.invited_by?.full_name || invitation.invited_by?.email}{' '}
                        wants to share{' '}
                        {invitation.file_name
                          ? `"${invitation.file_name}"`
                          : invitation.folder_name
                          ? `folder "${invitation.folder_name}"`
                          : 'an item'}{' '}
                        with you
                      </p>
                      {invitation.message && (
                        <p className="text-sm text-gray-600 mt-1 italic">
                          "{invitation.message}"
                        </p>
                      )}
                      <p className="text-xs text-gray-500 mt-1">
                        {permissionBadge(invitation.permission)} - Expires{' '}
                        {new Date(invitation.expires_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex space-x-2 ml-4">
                      <button
                        onClick={() =>
                          handleInvitationResponse(invitation.id, 'accept')
                        }
                        className="px-4 py-1.5 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
                      >
                        Accept
                      </button>
                      <button
                        onClick={() =>
                          handleInvitationResponse(invitation.id, 'decline')
                        }
                        className="px-4 py-1.5 border border-gray-300 text-gray-700 rounded-lg text-sm hover:bg-gray-50"
                      >
                        Decline
                      </button>
                    </div>
                  </div>
                </div>
              ))
            ))}
        </div>
      )}
    </div>
  );
};

export default SharedPage;
