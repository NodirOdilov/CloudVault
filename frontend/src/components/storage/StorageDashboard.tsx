import React, { useEffect, useState, useMemo } from 'react';
import { useAuthStore } from '../../store/authStore';
import apiClient from '../../api/client';

interface StorageBreakdown {
  category: string;
  size: number;
  count: number;
  color: string;
}

interface ActivityItem {
  action: string;
  count: number;
  action_display: string;
}

const StorageDashboard: React.FC = () => {
  const { user, fetchProfile } = useAuthStore();
  const [recentFiles, setRecentFiles] = useState<any[]>([]);
  const [activitySummary, setActivitySummary] = useState<{
    total_actions: number;
    action_breakdown: ActivityItem[];
    daily_activity: Array<{ date: string; count: number }>;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      await fetchProfile();

      const [recentResponse, activityResponse] = await Promise.all([
        apiClient.get('/files/recent/'),
        apiClient.get('/activity/summary/?days=30'),
      ]);

      setRecentFiles((recentResponse.data.results || recentResponse.data).slice(0, 10));
      setActivitySummary(activityResponse.data);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const storagePercentage = useMemo(() => {
    if (!user?.storage_quota) return 0;
    return user.storage_quota.usage_percentage;
  }, [user]);

  const storageColor = useMemo(() => {
    if (storagePercentage > 90) return 'text-red-600';
    if (storagePercentage > 70) return 'text-yellow-600';
    return 'text-blue-600';
  }, [storagePercentage]);

  const storageBarColor = useMemo(() => {
    if (storagePercentage > 90) return 'bg-red-500';
    if (storagePercentage > 70) return 'bg-yellow-500';
    return 'bg-blue-600';
  }, [storagePercentage]);

  const formatBytes = (bytes: number): string => {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Storage Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl border p-6 col-span-2">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Storage Usage</h3>
          <div className="flex items-end space-x-6">
            <div className="flex-1">
              <div className="flex items-baseline space-x-2 mb-2">
                <span className={`text-3xl font-bold ${storageColor}`}>
                  {storagePercentage.toFixed(1)}%
                </span>
                <span className="text-gray-500 text-sm">used</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3 mb-3">
                <div
                  className={`h-3 rounded-full transition-all duration-500 ${storageBarColor}`}
                  style={{ width: `${Math.min(100, storagePercentage)}%` }}
                />
              </div>
              <p className="text-sm text-gray-600">
                {user?.storage_used_display || '0 B'} of{' '}
                {user?.storage_quota_display || '5.0 GB'} used
              </p>
              {user?.storage_quota && (
                <p className="text-sm text-gray-500 mt-1">
                  {formatBytes(user.storage_quota.available_bytes)} available
                </p>
              )}
            </div>
            <div className="w-32 h-32 relative">
              <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
                <path
                  className="text-gray-200"
                  stroke="currentColor"
                  strokeWidth="3"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <path
                  className={storageBarColor.replace('bg-', 'text-')}
                  stroke="currentColor"
                  strokeWidth="3"
                  strokeDasharray={`${storagePercentage}, 100`}
                  strokeLinecap="round"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="space-y-4">
          <div className="bg-white rounded-xl border p-4">
            <p className="text-sm text-gray-500">Total Files</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {activitySummary?.action_breakdown.find((a) => a.action === 'upload')?.count || 0}
            </p>
          </div>
          <div className="bg-white rounded-xl border p-4">
            <p className="text-sm text-gray-500">Actions (30 days)</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {activitySummary?.total_actions || 0}
            </p>
          </div>
          <div className="bg-white rounded-xl border p-4">
            <p className="text-sm text-gray-500">Downloads</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {activitySummary?.action_breakdown.find((a) => a.action === 'download')?.count || 0}
            </p>
          </div>
        </div>
      </div>

      {/* Activity Chart + Recent Files */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Activity Timeline */}
        <div className="bg-white rounded-xl border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Activity (30 Days)</h3>
          {activitySummary?.daily_activity && activitySummary.daily_activity.length > 0 ? (
            <div className="space-y-2">
              {activitySummary.daily_activity.slice(-14).map((day) => {
                const maxCount = Math.max(
                  ...activitySummary.daily_activity.map((d) => d.count)
                );
                const barWidth = maxCount > 0 ? (day.count / maxCount) * 100 : 0;
                return (
                  <div key={day.date} className="flex items-center space-x-3">
                    <span className="text-xs text-gray-500 w-20 flex-shrink-0">
                      {new Date(day.date).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                      })}
                    </span>
                    <div className="flex-1 bg-gray-100 rounded-full h-2.5">
                      <div
                        className="bg-blue-500 h-2.5 rounded-full transition-all"
                        style={{ width: `${barWidth}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-600 w-8 text-right">
                      {day.count}
                    </span>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No activity data available</p>
          )}
        </div>

        {/* Recent Files */}
        <div className="bg-white rounded-xl border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Files</h3>
          {recentFiles.length > 0 ? (
            <div className="space-y-3">
              {recentFiles.map((file) => (
                <div
                  key={file.id}
                  className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0"
                >
                  <div className="flex items-center space-x-3 min-w-0">
                    <span className="text-lg flex-shrink-0">
                      {file.file_type_category === 'image'
                        ? '[ ]'
                        : file.file_type_category === 'document'
                        ? '[D]'
                        : '[F]'}
                    </span>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-800 truncate">
                        {file.name}
                      </p>
                      <p className="text-xs text-gray-500">{file.size_display}</p>
                    </div>
                  </div>
                  <span className="text-xs text-gray-400 flex-shrink-0 ml-2">
                    {new Date(file.updated_at).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No recent files</p>
          )}
        </div>
      </div>

      {/* Activity Breakdown */}
      {activitySummary?.action_breakdown && activitySummary.action_breakdown.length > 0 && (
        <div className="bg-white rounded-xl border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Action Breakdown</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {activitySummary.action_breakdown.slice(0, 8).map((item) => (
              <div key={item.action} className="text-center p-3 bg-gray-50 rounded-lg">
                <p className="text-2xl font-bold text-gray-800">{item.count}</p>
                <p className="text-xs text-gray-500 mt-1 capitalize">{item.action_display}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default StorageDashboard;
