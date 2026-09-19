'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import api from '@/lib/api';
import Link from 'next/link';

export default function SpaceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [space, setSpace] = useState<any>(null);
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNew, setShowNew] = useState(false);
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');
  const [goal, setGoal] = useState('');
  const [toast, setToast] = useState<{ msg: string; type: string } | null>(null);

  useEffect(() => { if (!authLoading && !user) router.push('/login'); }, [user, authLoading, router]);
  useEffect(() => { if (user && id) loadData(); }, [user, id]);

  const loadData = async () => {
    try {
      const [s, p] = await Promise.all([api.spaces.get(id), api.projects.list(id)]);
      setSpace(s); setProjects(p);
    } catch { router.push('/dashboard'); }
    setLoading(false);
  };

  const showToast = (msg: string, type: string) => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const createProject = async () => {
    if (!name.trim()) return;
    try {
      const p = await api.projects.create({ name, description: desc, learning_goal: goal, space_id: id });
      setName(''); setDesc(''); setGoal(''); setShowNew(false);
      router.push(`/projects/${p.id}`);
    } catch (err: any) { showToast(err.message, 'error'); }
  };

  const deleteProject = async (e: React.MouseEvent, projectId: string) => {
    e.preventDefault(); e.stopPropagation();
    if (!confirm('Delete this project? All materials, quizzes and chat history will be permanently removed.')) return;
    try {
      await api.projects.delete(projectId);
      setProjects(projects.filter(p => p.id !== projectId));
      showToast('Project deleted', 'success');
    } catch (err: any) { showToast(err.message, 'error'); }
  };

  if (authLoading || !user) return <div style={{ minHeight: '100vh' }} />;

  return (
    <div style={{ minHeight: '100vh' }}>
      <header className="topnav">
        <div className="breadcrumb">
          <Link href="/dashboard">Dashboard</Link>
          <span className="breadcrumb-sep">/</span>
          <span className="breadcrumb-current">{space?.name || '...'}</span>
        </div>
        <button onClick={() => setShowNew(true)} className="btn-primary">+ New Project</button>
      </header>

      <main style={{ maxWidth: 1100, margin: '0 auto', padding: '40px 24px' }}>
        <div style={{ marginBottom: 40 }}>
          <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 4 }}>{space?.name}</h1>
          {space?.description && <p style={{ fontSize: 14, color: 'var(--color-text-3)' }}>{space.description}</p>}
        </div>

        {showNew && (
          <div className="modal-overlay" onClick={() => setShowNew(false)}>
            <div className="modal" onClick={e => e.stopPropagation()}>
              <h3 style={{ fontSize: 17, fontWeight: 600, marginBottom: 4 }}>New Project</h3>
              <p style={{ fontSize: 13, color: 'var(--color-text-3)', marginBottom: 20 }}>Add a focused learning project to this space</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--color-text-2)', marginBottom: 6 }}>Project name</label>
                  <input className="input-field" value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Machine Learning Fundamentals" autoFocus />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--color-text-2)', marginBottom: 6 }}>Description</label>
                  <input className="input-field" value={desc} onChange={e => setDesc(e.target.value)} placeholder="Brief description (optional)" />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--color-text-2)', marginBottom: 6 }}>Learning goal</label>
                  <textarea className="input-field" value={goal} onChange={e => setGoal(e.target.value)} placeholder="What do you want to master? (optional)" rows={2} style={{ resize: 'vertical' }} />
                </div>
                <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                  <button onClick={createProject} className="btn-primary" disabled={!name.trim()} style={{ flex: 1 }}>Create Project</button>
                  <button onClick={() => setShowNew(false)} className="btn-secondary">Cancel</button>
                </div>
              </div>
            </div>
          </div>
        )}

        <p className="section-heading">Projects</p>
        {loading ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 12 }}>
            {[1,2,3,4].map(i => <div key={i} className="skeleton" style={{ height: 150 }} />)}
          </div>
        ) : projects.length === 0 ? (
          <div className="card empty-state">
            <div className="empty-icon">🚀</div>
            <p className="empty-title">No projects yet</p>
            <p className="empty-desc">Create your first project to start uploading materials and learning</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 12 }}>
            {projects.map(p => (
              <Link key={p.id} href={`/projects/${p.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                <div className="card card-interactive" style={{ padding: 22, position: 'relative' }}>
                  <button
                    onClick={e => deleteProject(e, p.id)}
                    title="Delete Project"
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
                  <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 8, paddingRight: 28 }}>{p.name}</h3>
                  <p style={{ fontSize: 13, color: 'var(--color-text-3)', marginBottom: 16, lineHeight: 1.55 }}>
                    {p.learning_goal || p.description || 'No description'}
                  </p>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <span className="badge badge-cyan">{p.material_count} materials</span>
                    <span className="badge badge-violet">{p.concept_count} concepts</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}
    </div>
  );
}