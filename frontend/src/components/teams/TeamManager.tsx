import React, { useState, useEffect } from 'react';
import apiClient from '../../api/client';

interface Team {
  id: string;
  name: string;
  description: string;
  avatar: string;
  member_count: number;
  storage_quota: number;
  storage_used: number;
  storage_percentage: number;
  my_role: string | null;
  created_at: string;
}

interface TeamMember {
  id: string;
  user: { id: string; email: string; full_name: string; avatar: string };
  role: string;
  can_upload: boolean;
  can_delete: boolean;
  can_manage_members: boolean;
  joined_at: string;
}

const TeamManager: React.FC = () => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Create team form
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newTeamName, setNewTeamName] = useState('');
  const [newTeamDescription, setNewTeamDescription] = useState('');

  // Invite form
  const [showInviteForm, setShowInviteForm] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('viewer');

  useEffect(() => {
    loadTeams();
  }, []);

  const loadTeams = async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.get('/teams/');
      setTeams(response.data.results || response.data);
    } catch (err: any) {
      setError('Failed to load teams');
    } finally {
      setIsLoading(false);
    }
  };

  const loadMembers = async (teamId: string) => {
    try {
      const response = await apiClient.get(`/teams/${teamId}/members/`);
      setMembers(response.data.results || response.data);
    } catch (err) {
      setError('Failed to load team members');
    }
  };

  const handleSelectTeam = (team: Team) => {
    setSelectedTeam(team);
    loadMembers(team.id);
  };

  const handleCreateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await apiClient.post('/teams/', {
        name: newTeamName,
        description: newTeamDescription,
      });
      setTeams((prev) => [...prev, response.data]);
      setShowCreateForm(false);
      setNewTeamName('');
      setNewTeamDescription('');
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to create team');
    }
  };

  const handleInviteMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTeam) return;

    try {
      await apiClient.post(`/teams/${selectedTeam.id}/invite/`, {
        email: inviteEmail,
        role: inviteRole,
      });
      setShowInviteForm(false);
      setInviteEmail('');
      setInviteRole('viewer');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to invite member');
    }
  };

  const handleRemoveMember = async (membershipId: string) => {
    if (!selectedTeam) return;
    try {
      await apiClient.delete(
        `/teams/${selectedTeam.id}/members/${membershipId}/`
      );
      setMembers((prev) => prev.filter((m) => m.id !== membershipId));
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to remove member');
    }
  };

  const handleUpdateRole = async (membershipId: string, newRole: string) => {
    if (!selectedTeam) return;
    try {
      const response = await apiClient.patch(
        `/teams/${selectedTeam.id}/members/${membershipId}/`,
        { role: newRole }
      );
      setMembers((prev) =>
        prev.map((m) => (m.id === membershipId ? response.data : m))
      );
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to update role');
    }
  };

  const handleLeaveTeam = async (teamId: string) => {
    try {
      await apiClient.post(`/teams/${teamId}/leave/`);
      setTeams((prev) => prev.filter((t) => t.id !== teamId));
      if (selectedTeam?.id === teamId) {
        setSelectedTeam(null);
        setMembers([]);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to leave team');
    }
  };

  const formatStorageSize = (bytes: number): string => {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  const roleColors: Record<string, string> = {
    owner: 'bg-purple-100 text-purple-800',
    admin: 'bg-blue-100 text-blue-800',
    editor: 'bg-green-100 text-green-800',
    viewer: 'bg-gray-100 text-gray-700',
  };

  return (
    <div className="flex h-full">
      {/* Team List Sidebar */}
      <div className="w-72 border-r bg-gray-50 flex flex-col">
        <div className="p-4 border-b">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-gray-900">Teams</h2>
            <button
              onClick={() => setShowCreateForm(true)}
              className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
            >
              + New
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {teams.map((team) => (
            <button
              key={team.id}
              onClick={() => handleSelectTeam(team)}
              className={`w-full text-left px-3 py-3 rounded-lg transition-colors ${
                selectedTeam?.id === team.id
                  ? 'bg-blue-100 text-blue-900'
                  : 'hover:bg-gray-100 text-gray-700'
              }`}
            >
              <p className="font-medium text-sm">{team.name}</p>
              <p className="text-xs text-gray-500 mt-0.5">
                {team.member_count} members
              </p>
            </button>
          ))}
          {teams.length === 0 && !isLoading && (
            <p className="text-sm text-gray-500 text-center py-8">No teams yet</p>
          )}
        </div>
      </div>

      {/* Team Detail */}
      <div className="flex-1 overflow-y-auto">
        {selectedTeam ? (
          <div className="p-6 space-y-6">
            {/* Team Header */}
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">
                  {selectedTeam.name}
                </h2>
                <p className="text-gray-600 mt-1">{selectedTeam.description || 'No description'}</p>
              </div>
              {selectedTeam.my_role !== 'owner' && (
                <button
                  onClick={() => handleLeaveTeam(selectedTeam.id)}
                  className="px-4 py-2 text-red-600 border border-red-300 rounded-lg hover:bg-red-50 text-sm"
                >
                  Leave Team
                </button>
              )}
            </div>

            {/* Storage Usage */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Team Storage</span>
                <span className="text-sm text-gray-600">
                  {formatStorageSize(selectedTeam.storage_used)} /{' '}
                  {formatStorageSize(selectedTeam.storage_quota)}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${
                    selectedTeam.storage_percentage > 90
                      ? 'bg-red-500'
                      : selectedTeam.storage_percentage > 70
                      ? 'bg-yellow-500'
                      : 'bg-blue-600'
                  }`}
                  style={{ width: `${Math.min(100, selectedTeam.storage_percentage)}%` }}
                />
              </div>
            </div>

            {/* Members */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  Members ({members.length})
                </h3>
                {selectedTeam.my_role && ['owner', 'admin'].includes(selectedTeam.my_role) && (
                  <button
                    onClick={() => setShowInviteForm(true)}
                    className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700"
                  >
                    Invite Member
                  </button>
                )}
              </div>

              <div className="space-y-2">
                {members.map((member) => (
                  <div
                    key={member.id}
                    className="flex items-center justify-between p-3 bg-white border rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center text-sm font-medium text-gray-600">
                        {(member.user.full_name || member.user.email)[0].toUpperCase()}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-800">
                          {member.user.full_name || member.user.email}
                        </p>
                        <p className="text-xs text-gray-500">{member.user.email}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-medium capitalize ${roleColors[member.role] || roleColors.viewer}`}>
                        {member.role}
                      </span>
                      {selectedTeam.my_role &&
                        ['owner', 'admin'].includes(selectedTeam.my_role) &&
                        member.role !== 'owner' && (
                          <div className="flex space-x-1">
                            <select
                              value={member.role}
                              onChange={(e) => handleUpdateRole(member.id, e.target.value)}
                              className="text-xs border rounded px-2 py-1"
                            >
                              <option value="admin">Admin</option>
                              <option value="editor">Editor</option>
                              <option value="viewer">Viewer</option>
                            </select>
                            <button
                              onClick={() => handleRemoveMember(member.id)}
                              className="text-red-500 hover:text-red-700 text-xs px-2"
                            >
                              Remove
                            </button>
                          </div>
                        )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            <div className="text-center">
              <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              <p className="text-lg font-medium">Select a team</p>
              <p className="text-sm">Choose a team from the sidebar or create a new one</p>
            </div>
          </div>
        )}
      </div>

      {/* Create Team Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 p-6">
            <h3 className="text-lg font-semibold mb-4">Create New Team</h3>
            <form onSubmit={handleCreateTeam} className="space-y-3">
              <input
                type="text"
                value={newTeamName}
                onChange={(e) => setNewTeamName(e.target.value)}
                placeholder="Team name"
                className="w-full border rounded-lg px-3 py-2 text-sm"
                required
              />
              <textarea
                value={newTeamDescription}
                onChange={(e) => setNewTeamDescription(e.target.value)}
                placeholder="Description (optional)"
                className="w-full border rounded-lg px-3 py-2 text-sm"
                rows={3}
              />
              <div className="flex space-x-2 justify-end">
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="px-4 py-2 border rounded-lg text-sm hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
                >
                  Create Team
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Invite Member Modal */}
      {showInviteForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 p-6">
            <h3 className="text-lg font-semibold mb-4">Invite Team Member</h3>
            <form onSubmit={handleInviteMember} className="space-y-3">
              <input
                type="email"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="Email address"
                className="w-full border rounded-lg px-3 py-2 text-sm"
                required
              />
              <select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value)}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              >
                <option value="admin">Admin</option>
                <option value="editor">Editor</option>
                <option value="viewer">Viewer</option>
              </select>
              <div className="flex space-x-2 justify-end">
                <button
                  type="button"
                  onClick={() => setShowInviteForm(false)}
                  className="px-4 py-2 border rounded-lg text-sm hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
                >
                  Send Invite
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="fixed bottom-4 right-4 bg-red-50 border border-red-200 px-4 py-3 rounded-lg shadow-lg">
          <div className="flex items-center justify-between">
            <p className="text-sm text-red-700">{error}</p>
            <button onClick={() => setError(null)} className="ml-4 text-red-500 hover:text-red-700">
              x
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default TeamManager;
