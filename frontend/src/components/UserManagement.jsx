import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Shield, UserPlus, Trash2, ShieldAlert, CheckCircle2, X } from 'lucide-react';
import { apiService } from '../services/api';

const ROLES = ['admin', 'manager', 'qa', 'guest'];

export default function UserManagement({ currentUser }) {
  const [users, setUsers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // New user state
  const [showNewUser, setShowNewUser] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState('qa');

  // Delete modal state
  const [userToDelete, setUserToDelete] = useState(null);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setIsLoading(true);
      const data = await apiService.getUsers();
      setUsers(data);
    } catch (err) {
      setError(err.message || 'Failed to load users');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      await apiService.createUser({
        username: newUsername,
        email: newEmail,
        password: newPassword,
        role: newRole
      });
      setSuccessMsg('User created successfully');
      setShowNewUser(false);
      setNewUsername('');
      setNewEmail('');
      setNewPassword('');
      fetchUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteUser = async (id) => {
    try {
      await apiService.deleteUser(id);
      setSuccessMsg('User deleted');
      setUserToDelete(null);
      fetchUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRoleChange = async (id, newRole) => {
    try {
      await apiService.updateUser(id, { role: newRole });
      setSuccessMsg(`Role updated to ${newRole}`);
      fetchUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  if (currentUser?.role?.toLowerCase() !== 'admin') {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh]">
        <ShieldAlert className="w-16 h-16 text-red-500 mb-4" />
        <h2 className="text-2xl font-black text-[var(--text-primary)]">Access Denied</h2>
        <p className="text-[var(--text-secondary)] mt-2">You must be an administrator to view this page.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-black text-[var(--text-primary)] tracking-tight">User Management</h2>
          <p className="text-[var(--text-secondary)] text-sm mt-1">Manage platform access, roles, and security.</p>
        </div>
        <button 
          onClick={() => setShowNewUser(!showNewUser)}
          className="flex items-center gap-2 px-4 py-2 primary-gradient rounded-xl text-sm font-bold text-[var(--text-primary)] transition-all hover:opacity-90 active:scale-[0.98]"
        >
          {showNewUser ? <X className="w-4 h-4" /> : <UserPlus className="w-4 h-4" />}
          {showNewUser ? 'Cancel' : 'Add User'}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm font-bold flex items-center gap-3">
          <ShieldAlert className="w-4 h-4" /> {error}
          <button onClick={() => setError(null)} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}

      {successMsg && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-400 text-sm font-bold flex items-center gap-3">
          <CheckCircle2 className="w-4 h-4" /> {successMsg}
          <button onClick={() => setSuccessMsg(null)} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}

      {showNewUser && (
        <motion.form 
          initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
          onSubmit={handleCreateUser} 
          className="card p-6 border-l-4 border-l-red-500"
        >
          <h3 className="text-lg font-bold text-[var(--text-primary)] mb-4">Create New User</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs font-bold text-[var(--text-muted)] uppercase mb-1">Username</label>
              <input required type="text" value={newUsername} onChange={e => setNewUsername(e.target.value)} className="w-full px-3 py-2 bg-[var(--bg-input)] border border-[var(--border-color)] rounded-lg text-sm text-[var(--text-primary)] focus:border-red-500 outline-none" />
            </div>
            <div>
              <label className="block text-xs font-bold text-[var(--text-muted)] uppercase mb-1">Email</label>
              <input required type="email" value={newEmail} onChange={e => setNewEmail(e.target.value)} className="w-full px-3 py-2 bg-[var(--bg-input)] border border-[var(--border-color)] rounded-lg text-sm text-[var(--text-primary)] focus:border-red-500 outline-none" />
            </div>
            <div>
              <label className="block text-xs font-bold text-[var(--text-muted)] uppercase mb-1">Password</label>
              <input required type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} className="w-full px-3 py-2 bg-[var(--bg-input)] border border-[var(--border-color)] rounded-lg text-sm text-[var(--text-primary)] focus:border-red-500 outline-none" />
            </div>
            <div>
              <label className="block text-xs font-bold text-[var(--text-muted)] uppercase mb-1">Role</label>
              <select value={newRole} onChange={e => setNewRole(e.target.value)} className="w-full px-3 py-2 bg-[var(--bg-input)] border border-[var(--border-color)] rounded-lg text-sm text-[var(--text-primary)] focus:border-red-500 outline-none">
                {ROLES.map(r => <option key={r} value={r}>{r.toUpperCase()}</option>)}
              </select>
            </div>
          </div>
          <div className="mt-4 flex justify-end">
            <button type="submit" className="px-4 py-2 bg-white/10 hover:bg-white/20 text-[var(--text-primary)] rounded-lg text-sm font-bold transition-all">Save User</button>
          </div>
        </motion.form>
      )}

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[var(--border-color)] bg-[var(--bg-hover)]">
                <th className="px-6 py-4 text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest">User</th>
                <th className="px-6 py-4 text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest">Email</th>
                <th className="px-6 py-4 text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest">Role</th>
                <th className="px-6 py-4 text-xs font-bold text-[var(--text-muted)] uppercase tracking-widest text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.06]">
              {isLoading ? (
                <tr>
                  <td colSpan="4" className="px-6 py-8 text-center text-[var(--text-muted)]">Loading users...</td>
                </tr>
              ) : users.map(user => (
                <tr key={user.id} className="hover:bg-[var(--bg-hover)] transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center text-xs font-bold text-[var(--text-primary)] uppercase">
                        {user.username.charAt(0)}
                      </div>
                      <span className="font-bold text-[var(--text-secondary)]">{user.username}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-[var(--text-secondary)]">{user.email}</td>
                  <td className="px-6 py-4">
                    <select 
                      value={user.role} 
                      onChange={e => handleRoleChange(user.id, e.target.value)}
                      disabled={user.username === currentUser?.username}
                      className="px-2 py-1 bg-[var(--bg-input)] border border-[var(--border-color)] rounded text-xs font-bold uppercase text-[var(--text-secondary)] outline-none cursor-pointer focus:border-red-500"
                    >
                      {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                    </select>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button 
                      onClick={() => setUserToDelete(user)}
                      disabled={user.username === currentUser?.username}
                      className="p-2 rounded-lg text-[var(--text-muted)] hover:text-red-400 hover:bg-red-500/10 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                      title="Delete User"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {userToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setUserToDelete(null)}>
          <div className="card p-8 max-w-sm w-full mx-4" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-[var(--text-primary)] mb-2">Delete User?</h3>
            <p className="text-sm text-[var(--text-secondary)] mb-6">Are you sure you want to delete <strong>{userToDelete.username}</strong>? This action cannot be undone.</p>
            <div className="flex gap-3">
              <button onClick={() => setUserToDelete(null)} className="flex-1 py-2.5 rounded-xl text-sm font-bold text-[var(--text-secondary)] bg-[var(--bg-hover)] border border-[var(--border-color)] hover:bg-[var(--bg-hover-strong)] transition-all">Cancel</button>
              <button onClick={() => handleDeleteUser(userToDelete.id)} className="flex-1 py-2.5 rounded-xl text-sm font-bold text-[var(--text-primary)] bg-red-600 hover:bg-red-700 transition-all">Delete</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
