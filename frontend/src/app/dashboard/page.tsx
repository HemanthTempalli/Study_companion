'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import api from '@/lib/api';
import Link from 'next/link';

export default function DashboardPage() {
  const { user, loading: authLoading, logout, isAdmin } = useAuth();
  const router = useRouter();
  const [spaces, setSpaces] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNewSpace, setShowNewSpace] = useState(false);
  const [newSpaceName, setNewSpaceName] = useState('');
  const [newSpaceDesc, setNewSpaceDesc] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [toast, setToast] = useState<{ msg: string; type: string } | null>(null);

  useEffect(() => { if (!authLoading && !user) router.push('/login'); }, [user, authLoading, router]);
  useEffect(() => { if (user) loadData(); }, [user]);

  const loadData = async () => {
    try {
      const [s, p] = await Promise.all([api.spaces.list(), api.projects.list()]);
      setSpaces(s);
      setProjects(p);
    } catch { }
    setLoading(false);
  };

  const showToast = (msg: string, type: string) => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const createSpace = async () => {
    if (!newSpaceName.trim() || isCreating) return;
    setIsCreating(true);
    try {
      await api.spaces.create({ name: newSpaceName, description: newSpaceDesc });
      setNewSpaceName(''); setNewSpaceDesc(''); setShowNewSpace(false);
      loadData();
      showToast('Space created!', 'success');
    } catch (err: any) { showToast(err.message, 'error'); }
    setIsCreating(false);
  };

  const deleteSpace = async (e: React.MouseEvent, id: string) => {
    e.preventDefault(); e.stopPropagation();
    if (!confirm('Delete this space? All projects inside will also be deleted.')) return;
    try {
      await api.spaces.delete(id);
      setSpaces(spaces.filter(s => s.id !== id));
      showToast('Space deleted', 'success');
    } catch (err: any) { showToast(err.message, 'error'); }
  };

  if (authLoading || !user) return <div style={{ minHeight: '100vh' }} />;

  const totalMaterials = projects.reduce((s, p) => s + (p.material_count || 0), 0);

  return (
    <div style={{ minHeight: '100vh' }}>
      {/* Topnav */}
      <header className="topnav">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div className="logo-mark">🧠</div>
          <span className="logo-text">StudyCompanion</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {isAdmin && <Link href="/admin" className="btn-ghost" style={{ textDecoration: 'none' }}>Admin</Link>}
          <span style={{ fontSize: 13, color: 'var(--color-text-3)', padding: '0 8px' }}>{user.full_name}</span>
          <button onClick={logout} className="btn-ghost">Sign out</button>
        </div>
      </header>

      <main style={{ maxWidth: 1100, margin: '0 auto', padding: '40px 24px' }}>
        {/* Page header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 40 }}>
          <div>
            <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>
              Good to see you, {user.full_name.split(' ')[0]}
            </h1>
            <p style={{ fontSize: 14, color: 'var(--color-text-3)' }}>Your learning spaces and recent projects</p>
          </div>
          <button onClick={() => setShowNewSpace(true)} className="btn-primary" style={{ flexShrink: 0 }}>
            + New Space
          </button>
        </div>

        {/* Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 40 }}>
          {[
            { label: 'Spaces', value: spaces.length },
            { label: 'Projects', value: projects.length },
            { label: 'Materials', value: totalMaterials },
          ].map((s, i) => (
            <div key={i} className="stat-card">
              <div className="stat-value">{s.value}</div>
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
        </div>

        {/* New Space Modal */}
        {showNewSpace && (
          <div className="modal-overlay" onClick={() => setShowNewSpace(false)}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <h3 style={{ fontSize: 17, fontWeight: 600, marginBottom: 4 }}>New Space</h3>
              <p style={{ fontSize: 13, color: 'var(--color-text-3)', marginBottom: 20 }}>Group related projects together</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--color-text-2)', marginBottom: 6 }}>Name</label>
                  <input className="input-field" value={newSpaceName} onChange={e => setNewSpaceName(e.target.value)} placeholder="e.g. Computer Science" autoFocus />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--color-text-2)', marginBottom: 6 }}>Description <span style={{ color: 'var(--color-text-4)' }}>(optional)</span></label>
                  <input className="input-field" value={newSpaceDesc} onChange={e => setNewSpaceDesc(e.target.value)} placeholder="What will you learn here?" />
                </div>
                <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                  <button onClick={createSpace} disabled={isCreating || !newSpaceName.trim()} className="btn-primary" style={{ flex: 1 }}>
                    {isCreating ? 'Creating...' : 'Create Space'}
                  </button>
                  <button onClick={() => setShowNewSpace(false)} disabled={isCreating} className="btn-secondary">
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Spaces */}
        <section>
          <p className="section-heading">Spaces</p>
          {loading ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 12 }}>
              {[1,2,3].map(i => <div key={i} className="skeleton" style={{ height: 130 }} />)}
            </div>
          ) : spaces.length === 0 ? (
            <div className="card empty-state">
              <div className="empty-icon">📚</div>
              <p className="empty-title">No spaces yet</p>
              <p className="empty-desc">Create your first space to start organizing your learning projects</p>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 12 }}>
              {spaces.map(space => (
                <Link key={space.id} href={`/spaces/${space.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                  <div className="card card-interactive" style={{ padding: 22, position: 'relative' }}>
                    <button
                      onClick={e => deleteSpace(e, space.id)}
                      title="Delete Space"
                      style={{
                        position: 'absolute', top: 14, right: 14, width: 28, height: 28,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        background: 'none', border: 'none', cursor: 'pointer', borderRadius: 'var(--radius-sm)',
                        color: 'var(--color-text-4)', fontSize: 14, transition: 'color 0.15s, background 0.15s',
                      }}
                      onMouseEnter={e => { e.currentTarget.style.color = 'var(--color-danger)'; e.currentTarget.style.background = 'var(--color-danger-dim)'; }}
                      onMouseLeave={e => { e.currentTarget.style.color = 'var(--color-text-4)'; e.currentTarget.style.background = 'none'; }}
                    >
                      🗑
                    </button>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                      <div style={{ width: 36, height: 36, borderRadius: 'var(--radius)', background: 'var(--color-surface-3)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, flexShrink: 0 }}>
                        📁
                      </div>
                      <div>
                        <h3 style={{ fontSize: 15, fontWeight: 600, paddingRight: 28 }}>{space.name}</h3>
                        <p style={{ fontSize: 12, color: 'var(--color-text-3)', marginTop: 1 }}>
                          {space.project_count || 0} {space.project_count === 1 ? 'project' : 'projects'}
                        </p>
                      </div>
                    </div>
                    {space.description && (
                      <p style={{ fontSize: 13, color: 'var(--color-text-3)', lineHeight: 1.55 }}>{space.description}</p>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>

        {/* Recent Projects */}
        {projects.length > 0 && (
          <section style={{ marginTop: 48 }}>
            <p className="section-heading">Recent Projects</p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
              {projects.slice(0, 6).map(p => (
                <Link key={p.id} href={`/projects/${p.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                  <div className="card card-interactive" style={{ padding: 20 }}>
                    <h3 style={{ fontSize: 14.5, fontWeight: 600, marginBottom: 8 }}>{p.name}</h3>
                    <p style={{ fontSize: 12.5, color: 'var(--color-text-3)', marginBottom: 14, lineHeight: 1.55 }}>
                      {p.description || p.learning_goal || 'No description'}
                    </p>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <span className="badge badge-cyan">{p.material_count} materials</span>
                      <span className="badge badge-violet">{p.concept_count} concepts</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </section>
        )}
      </main>

      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}
    </div>
  );
}
