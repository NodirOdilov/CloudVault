import React, { useState, useEffect, useCallback } from 'react';
import { sharingApi, FileShare, SharedLink } from '../../api/sharingApi';
import { CloudFile } from '../../api/filesApi';

interface SharingModalProps {
  file: CloudFile;
  isOpen: boolean;
  onClose: () => void;
}

type TabType = 'people' | 'link';

const SharingModal: React.FC<SharingModalProps> = ({ file, isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<TabType>('people');
  const [shares, setShares] = useState<FileShare[]>([]);
  const [sharedLinks, setSharedLinks] = useState<SharedLink[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // People sharing form
  const [shareEmail, setShareEmail] = useState('');
  const [sharePermission, setSharePermission] = useState('view');

  // Link sharing form
  const [linkPermission, setLinkPermission] = useState('view');
  const [linkPassword, setLinkPassword] = useState('');
  const [linkExpiresHours, setLinkExpiresHours] = useState<number | ''>('');
  const [linkMaxDownloads, setLinkMaxDownloads] = useState<number | ''>('');

  useEffect(() => {
    if (isOpen) {
      loadShares();
    }
  }, [isOpen, file.id]);

  const loadShares = async () => {
    setIsLoading(true);
    try {
      const data = await sharingApi.getFileShares(file.id);
      setShares(data.results || data);
    } catch (err) {
      setError('Failed to load sharing info');
    } finally {
      setIsLoading(false);
    }
  };

  const handleShareWithUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!shareEmail.trim()) return;

    setError(null);
    setSuccess(null);
    try {
      await sharingApi.shareFile(file.id, shareEmail.trim(), sharePermission);
      setSuccess(`Shared with ${shareEmail}`);
      setShareEmail('');
      loadShares();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to share file');
    }
  };

  const handleRevokeShare = async (shareId: string) => {
    try {
      await sharingApi.revokeShare(shareId);
      setShares((prev) => prev.filter((s) => s.id !== shareId));
      setSuccess('Share access removed');
    } catch (err) {
      setError('Failed to revoke share');
    }
  };

  const handleCreateLink = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const link = await sharingApi.createSharedLink({
        file_id: file.id,
        permission: linkPermission,
        password: linkPassword || undefined,
        expires_in_hours: linkExpiresHours ? Number(linkExpiresHours) : null,
        max_downloads: linkMaxDownloads ? Number(linkMaxDownloads) : null,
      });
      setSharedLinks((prev) => [link, ...prev]);
      setSuccess('Shared link created');
      setLinkPassword('');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to create link');
    }
  };

  const handleCopyLink = useCallback((url: string) => {
    navigator.clipboard.writeText(url).then(() => {
      setSuccess('Link copied to clipboard');
      setTimeout(() => setSuccess(null), 2000);
    });
  }, []);

  const handleDeactivateLink = async (linkId: string) => {
    try {
      await sharingApi.deactivateSharedLink(linkId);
      setSharedLinks((prev) =>
        prev.map((l) => (l.id === linkId ? { ...l, is_active: false } : l))
      );
    } catch (err) {
      setError('Failed to deactivate link');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Share "{file.name}"</h2>
            <p className="text-sm text-gray-500 mt-0.5">{file.size_display}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b">
          <button
            onClick={() => setActiveTab('people')}
            className={`flex-1 py-3 text-sm font-medium text-center transition-colors ${
              activeTab === 'people'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Share with People
          </button>
          <button
            onClick={() => setActiveTab('link')}
            className={`flex-1 py-3 text-sm font-medium text-center transition-colors ${
              activeTab === 'link'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Get Link
          </button>
        </div>

        {/* Alerts */}
        {error && (
          <div className="mx-6 mt-3 px-3 py-2 bg-red-50 text-red-700 text-sm rounded-lg">
            {error}
          </div>
        )}
        {success && (
          <div className="mx-6 mt-3 px-3 py-2 bg-green-50 text-green-700 text-sm rounded-lg">
            {success}
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'people' && (
            <div className="space-y-4">
              <form onSubmit={handleShareWithUser} className="flex space-x-2">
                <input
                  type="email"
                  value={shareEmail}
                  onChange={(e) => setShareEmail(e.target.value)}
                  placeholder="Enter email address"
                  className="flex-1 border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
                <select
                  value={sharePermission}
                  onChange={(e) => setSharePermission(e.target.value)}
                  className="border rounded-lg px-3 py-2 text-sm"
                >
                  <option value="view">View</option>
                  <option value="edit">Edit</option>
                  <option value="download">Download</option>
                </select>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
                >
                  Share
                </button>
              </form>

              <div className="space-y-2">
                <h3 className="text-sm font-medium text-gray-700">Shared with</h3>
                {isLoading ? (
                  <p className="text-sm text-gray-500">Loading...</p>
                ) : shares.length === 0 ? (
                  <p className="text-sm text-gray-500">Not shared with anyone yet</p>
                ) : (
                  shares.map((share) => (
                    <div
                      key={share.id}
                      className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg"
                    >
                      <div>
                        <p className="text-sm font-medium text-gray-800">
                          {share.shared_with?.email || 'Unknown'}
                        </p>
                        <p className="text-xs text-gray-500 capitalize">
                          {share.permission} access
                        </p>
                      </div>
                      <button
                        onClick={() => handleRevokeShare(share.id)}
                        className="text-red-500 hover:text-red-700 text-sm"
                      >
                        Remove
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {activeTab === 'link' && (
            <div className="space-y-4">
              <form onSubmit={handleCreateLink} className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Permission</label>
                    <select
                      value={linkPermission}
                      onChange={(e) => setLinkPermission(e.target.value)}
                      className="w-full border rounded-lg px-3 py-2 text-sm"
                    >
                      <option value="view">View Only</option>
                      <option value="download">Can Download</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Expires (hours)</label>
                    <input
                      type="number"
                      value={linkExpiresHours}
                      onChange={(e) => setLinkExpiresHours(e.target.value ? Number(e.target.value) : '')}
                      placeholder="Never"
                      min={1}
                      max={8760}
                      className="w-full border rounded-lg px-3 py-2 text-sm"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Password (optional)</label>
                    <input
                      type="password"
                      value={linkPassword}
                      onChange={(e) => setLinkPassword(e.target.value)}
                      placeholder="No password"
                      className="w-full border rounded-lg px-3 py-2 text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Max downloads</label>
                    <input
                      type="number"
                      value={linkMaxDownloads}
                      onChange={(e) => setLinkMaxDownloads(e.target.value ? Number(e.target.value) : '')}
                      placeholder="Unlimited"
                      min={1}
                      className="w-full border rounded-lg px-3 py-2 text-sm"
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  className="w-full py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
                >
                  Create Shared Link
                </button>
              </form>

              {sharedLinks.length > 0 && (
                <div className="space-y-2 mt-4">
                  <h3 className="text-sm font-medium text-gray-700">Active Links</h3>
                  {sharedLinks.map((link) => (
                    <div key={link.id} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-800 truncate">{link.url}</p>
                        <p className="text-xs text-gray-500">
                          {link.download_count} downloads
                          {link.expires_at && ` | Expires: ${new Date(link.expires_at).toLocaleDateString()}`}
                        </p>
                      </div>
                      <div className="flex space-x-2 ml-2">
                        <button
                          onClick={() => handleCopyLink(link.url)}
                          className="text-blue-600 hover:text-blue-800 text-sm"
                        >
                          Copy
                        </button>
                        {link.is_active && (
                          <button
                            onClick={() => handleDeactivateLink(link.id)}
                            className="text-red-500 hover:text-red-700 text-sm"
                          >
                            Disable
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SharingModal;
