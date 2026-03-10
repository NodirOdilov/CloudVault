import React from 'react';
import StorageDashboard from '../components/storage/StorageDashboard';

const DashboardPage: React.FC = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Overview of your storage usage and recent activity
        </p>
      </div>
      <StorageDashboard />
    </div>
  );
};

export default DashboardPage;
