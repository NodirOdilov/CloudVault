import React from 'react';
import TeamManager from '../components/teams/TeamManager';

const TeamPage: React.FC = () => {
  return (
    <div className="h-[calc(100vh-64px)]">
      <TeamManager />
    </div>
  );
};

export default TeamPage;
