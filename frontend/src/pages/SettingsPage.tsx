import React, { useState, useEffect } from 'react';
import { useAuthStore } from '../store/authStore';
import apiClient from '../api/client';

interface NotificationPrefs {
  email_file_shared: boolean;
  email_team_events: boolean;
  email_storage_warnings: boolean;
  email_weekly_digest: boolean;
  push_file_shared: boolean;
  push_team_events: boolean;
  push_storage_warnings: boolean;
}

type SettingsTab = 'profile' | 'security' | 'notifications' | 'storage';

const SettingsPage: React.FC = () => {
  const { user, updateProfile, changePassword, fetchProfile, error, clearError } =
    useAuthStore();

  const [activeTab, setActiveTab] = useState<SettingsTab>('profile');
  const [success, setSuccess] = useState<string | null>(null);

  // Profile form
  const [firstName, setFirstName] = useState(user?.first_name || '');
  const [lastName, setLastName] = useState(user?.last_name || '');
  const [avatar, setAvatar] = useState(user?.avatar || '');

  // Password form
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Notification preferences
  const [notifPrefs, setNotifPrefs] = useState<NotificationPrefs | null>(null);

  useEffect(() => {
    if (user) {
      setFirstName(user.first_name);
      setLastName(user.last_name);
      setAvatar(user.avatar);
    }
  }, [user]);

  useEffect(() => {
    if (activeTab === 'notifications') {
      loadNotificationPrefs();
    }
  }, [activeTab]);

  const loadNotificationPrefs = async () => {
    try {
      const response = await apiClient.get('/notifications/preferences/');
      setNotifPrefs(response.data);
    } catch {
      // Preferences may not exist yet
      setNotifPrefs({
        email_file_shared: true,
        email_team_events: true,
        email_storage_warnings: true,
        email_weekly_digest: true,
        push_file_shared: true,
        push_team_events: true,
        push_storage_warnings: true,
      });
    }
  };

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setSuccess(null);
    try {
      await updateProfile({
        first_name: firstName,
        last_name: lastName,
        avatar,
      });
      setSuccess('Profile updated successfully');
    } catch {
      // Error handled in store
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setSuccess(null);

    if (newPassword !== confirmPassword) {
      return;
    }

    try {
      await changePassword(oldPassword, newPassword, confirmPassword);
      setSuccess('Password changed successfully');
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch {
      // Error handled in store
    }
  };

  const handleUpdateNotifPref = async (key: keyof NotificationPrefs, value: boolean) => {
    if (!notifPrefs) return;
    const updated = { ...notifPrefs, [key]: value };
    setNotifPrefs(updated);

    try {
      await apiClient.patch('/notifications/preferences/', { [key]: value });
    } catch {
      setNotifPrefs(notifPrefs); // Revert on failure
    }
  };

  const tabs: Array<{ key: SettingsTab; label: string }> = [
    { key: 'profile', label: 'Profile' },
    { key: 'security', label: 'Security' },
    { key: 'notifications', label: 'Notifications' },
    { key: 'storage', label: 'Storage' },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>

      <div className="flex space-x-8">
        {/* Sidebar Navigation */}
        <nav className="w-48 flex-shrink-0">
          <ul className="space-y-1">
            {tabs.map((tab) => (
              <li key={tab.key}>
                <button
                  onClick={() => { setActiveTab(tab.key); setSuccess(null); clearError(); }}
                  className={`w-full text-left px-4 py-2 rounded-lg text-sm transition-colors ${
                    activeTab === tab.key
                      ? 'bg-blue-50 text-blue-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {tab.label}
                </button>
              </li>
            ))}
          </ul>
        </nav>

        {/* Content */}
        <div className="flex-1">
          {error && (
            <div className="mb-4 px-4 py-3 bg-red-50 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}
          {success && (
            <div className="mb-4 px-4 py-3 bg-green-50 text-green-700 rounded-lg text-sm">
              {success}
            </div>
          )}

          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <form onSubmit={handleUpdateProfile} className="space-y-4">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Profile Information
              </h2>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
                  <input
                    type="text"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
                  <input
                    type="text"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  value={user?.email || ''}
                  disabled
                  className="w-full border rounded-lg px-3 py-2 text-sm bg-gray-50 text-gray-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Avatar URL</label>
                <input
                  type="url"
                  value={avatar}
                  onChange={(e) => setAvatar(e.target.value)}
                  placeholder="https://example.com/avatar.png"
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <button
                type="submit"
                className="px-6 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
              >
                Save Changes
              </button>
            </form>
          )}

          {/* Security Tab */}
          {activeTab === 'security' && (
            <form onSubmit={handleChangePassword} className="space-y-4">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Change Password
              </h2>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Current Password</label>
                <input
                  type="password"
                  value={oldPassword}
                  onChange={(e) => setOldPassword(e.target.value)}
                  required
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  minLength={8}
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Confirm New Password</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                />
                {confirmPassword && newPassword !== confirmPassword && (
                  <p className="text-xs text-red-500 mt-1">Passwords do not match</p>
                )}
              </div>
              <button
                type="submit"
                disabled={!oldPassword || !newPassword || newPassword !== confirmPassword}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Update Password
              </button>
            </form>
          )}

          {/* Notifications Tab */}
          {activeTab === 'notifications' && notifPrefs && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Notification Preferences
              </h2>
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-3">Email Notifications</h3>
                <div className="space-y-3">
                  {([
                    ['email_file_shared', 'File shared with you'],
                    ['email_team_events', 'Team events'],
                    ['email_storage_warnings', 'Storage warnings'],
                    ['email_weekly_digest', 'Weekly activity digest'],
                  ] as const).map(([key, label]) => (
                    <label key={key} className="flex items-center justify-between py-2">
                      <span className="text-sm text-gray-700">{label}</span>
                      <input
                        type="checkbox"
                        checked={notifPrefs[key]}
                        onChange={(e) => handleUpdateNotifPref(key, e.target.checked)}
                        className="rounded text-blue-600 focus:ring-blue-500"
                      />
                    </label>
                  ))}
                </div>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-3">Push Notifications</h3>
                <div className="space-y-3">
                  {([
                    ['push_file_shared', 'File shared with you'],
                    ['push_team_events', 'Team events'],
                    ['push_storage_warnings', 'Storage warnings'],
                  ] as const).map(([key, label]) => (
                    <label key={key} className="flex items-center justify-between py-2">
                      <span className="text-sm text-gray-700">{label}</span>
                      <input
                        type="checkbox"
                        checked={notifPrefs[key]}
                        onChange={(e) => handleUpdateNotifPref(key, e.target.checked)}
                        className="rounded text-blue-600 focus:ring-blue-500"
                      />
                    </label>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Storage Tab */}
          {activeTab === 'storage' && user && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Storage Management
              </h2>
              <div className="bg-gray-50 rounded-xl p-6">
                <div className="flex items-baseline justify-between mb-3">
                  <span className="text-sm font-medium text-gray-700">Storage Used</span>
                  <span className="text-sm text-gray-600">
                    {user.storage_used_display} / {user.storage_quota_display}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
                  <div
                    className={`h-3 rounded-full ${
                      (user.storage_quota?.usage_percentage || 0) > 90
                        ? 'bg-red-500'
                        : (user.storage_quota?.usage_percentage || 0) > 70
                        ? 'bg-yellow-500'
                        : 'bg-blue-600'
                    }`}
                    style={{
                      width: `${Math.min(100, user.storage_quota?.usage_percentage || 0)}%`,
                    }}
                  />
                </div>
                {user.storage_quota && (
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div className="bg-white rounded-lg p-3">
                      <p className="text-xs text-gray-500">Used</p>
                      <p className="text-sm font-semibold text-gray-800">
                        {user.storage_used_display}
                      </p>
                    </div>
                    <div className="bg-white rounded-lg p-3">
                      <p className="text-xs text-gray-500">Available</p>
                      <p className="text-sm font-semibold text-gray-800">
                        {formatBytes(user.storage_quota.available_bytes)}
                      </p>
                    </div>
                    <div className="bg-white rounded-lg p-3">
                      <p className="text-xs text-gray-500">Quota</p>
                      <p className="text-sm font-semibold text-gray-800">
                        {user.storage_quota_display}
                      </p>
                    </div>
                  </div>
                )}
              </div>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-800 font-medium">Need more space?</p>
                <p className="text-sm text-blue-700 mt-1">
                  Empty your trash to free up storage, or contact your administrator
                  to increase your quota.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

function formatBytes(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let size = bytes;
  let i = 0;
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024;
    i++;
  }
  return `${size.toFixed(1)} ${units[i]}`;
}

export default SettingsPage;
