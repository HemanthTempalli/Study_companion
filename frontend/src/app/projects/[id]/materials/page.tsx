'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import api from '@/lib/api';
import Link from 'next/link';

const NAV = [
  { key: 'overview', label: 'Overview' },
  { key: 'materials', label: 'Materials' },
  { key: 'tutor', label: 'AI Tutor' },
  { key: 'quiz', label: 'Quiz' },
  { key: 'mastery', label: 'Mastery' },
  { key: 'growth', label: 'Growth' },
  { key: 'analytics', label: 'Analytics' },
];

export default function MaterialsPage() {
  const { id } = useParams<{ id: string }>();
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [materials, setMaterials] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [toast, setToast] = useState<{ msg: string; type: string } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => { if (!authLoading && !user) router.push('/login'); }, [user, authLoading, router]);
  useEffect(() => { if (user && id) loadMaterials(); }, [user, id]);

  useEffect(() => {
    const hasProcessing = materials.some(m => m.status === 'QUEUED' || m.status === 'PROCESSING');
    if (!hasProcessing) return;
    const interval = setInterval(loadMaterials, 5000);
    return () => clearInterval(interval);
  }, [materials]);

  const loadMaterials = async () => {
    try { setMaterials(await api.materials.list(id)); } catch { }
    setLoading(false);
  };

  const showToast = (msg: string, type: string) => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.pdf')) { showToast('Only PDF files are allowed', 'error'); return; }
    setUploading(true);
    try {
      await api.materials.upload(id, file);
      loadMaterials();
      showToast('PDF uploaded! Processing will begin shortly.', 'success');
    } catch (err: any) { showToast(err.message, 'error'); }
    setUploading(false);
    if (fileRef.current) fileRef.current.value = '';
  };

  const handleDelete = async (materialId: string) => {
    if (!confirm('Delete this material? This cannot be undone.')) return;
    try {
      await api.materials.delete(id, materialId);
      loadMaterials();
      showToast('Material deleted', 'success');
    } catch (err: any) { showToast(err.message, 'error'); }
  };

  const handleRetry = async (materialId: string) => {
    try {
      await api.materials.retry(id, materialId);
      loadMaterials();
      showToast('Retrying processing...', 'success');
    } catch (err: any) { showToast(err.message, 'error'); }
  };

  const statusBadge = (s: string) => {
    switch (s) {
      case 'READY': return 'badge-emerald';
      case 'PROCESSING': return 'badge-amber';
      case 'QUEUED': return 'badge-cyan';
      case 'FAILED': return 'badge-rose';
      default: return 'badge-cyan';
    }
  };

  if (authLoading || !user) return <div style={{ minHeight: '100vh' }} />;

  return (
    <div style={{ minHeight: '100vh' }}>
      <header className="topnav">
        <div className="breadcrumb">
          <Link href="/dashboard">Dashboard</Link>
          <span className="breadcrumb-sep">/</span>
          <Link href={`/projects/${id}`}>Project</Link>
          <span className="breadcrumb-sep">/</span>
          <span className="breadcrumb-current">Materials</span>
        </div>
        <div>
          <input ref={fileRef} type="file" accept=".pdf" onChange={handleUpload} style={{ display: 'none' }} />
          <button onClick={() => fileRef.current?.click()} className="btn-primary" disabled={uploading}>
            {uploading ? 'Uploading...' : '↑ Upload PDF'}
          </button>
        </div>
      </header>

      <div className="tab-bar" style={{ padding: '0 24px' }}>
        {NAV.map(item => (
          <Link key={item.key} href={item.key === 'overview' ? `/projects/${id}` : `/projects/${id}/${item.key}`}
            className={`tab-item${item.key === 'materials' ? ' active' : ''}`}>
            {item.label}
          </Link>
        ))}
      </div>

      <main style={{ maxWidth: 900, margin: '0 auto', padding: '36px 24px' }}>
        <div style={{ marginBottom: 28 }}>
          <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>Learning Materials</h1>
          <p style={{ fontSize: 13.5, color: 'var(--color-text-3)' }}>Upload PDFs to build your AI-searchable knowledge base</p>
        </div>

        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {[1,2,3].map(i => <div key={i} className="skeleton" style={{ height: 76 }} />)}
          </div>
        ) : materials.length === 0 ? (
          <div className="card empty-state">
            <div className="empty-icon">📄</div>
            <p className="empty-title">No materials yet</p>
            <p className="empty-desc">Upload a PDF to start building your knowledge base. The AI will extract concepts and create a searchable index.</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {materials.map(m => (
              <div key={m.id} className="card" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16 }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                    <span style={{ fontSize: 14, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{m.filename}</span>
                    <span className={`badge ${statusBadge(m.status)}`} style={{ flexShrink: 0 }}>{m.status}</span>
                  </div>
                  <div style={{ display: 'flex', gap: 16, fontSize: 12, color: 'var(--color-text-3)' }}>
                    <span>{(m.file_size / 1024 / 1024).toFixed(1)} MB</span>
                    {m.page_count > 0 && <span>{m.page_count} pages</span>}
                    <span>{new Date(m.created_at).toLocaleDateString()}</span>
                  </div>
                  {m.error_message && (
                    <p style={{ fontSize: 12, color: 'var(--color-danger)', marginTop: 5 }}>{m.error_message}</p>
                  )}
                </div>
                <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                  {m.status === 'FAILED' && (
                    <button onClick={() => handleRetry(m.id)} className="btn-secondary" style={{ padding: '6px 12px', fontSize: 12 }}>Retry</button>
                  )}
                  <button onClick={() => handleDelete(m.id)} className="btn-danger" style={{ padding: '6px 12px', fontSize: 12 }}>Delete</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}
    </div>
  );
}