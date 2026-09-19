'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import api from '@/lib/api';
import Link from 'next/link';

export default function GrowthPage() {
  const { id } = useParams<{ id: string }>();
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [growth, setGrowth] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [genLoading, setGenLoading] = useState(false);
  const [toast, setToast] = useState<{ msg: string; type: string } | null>(null);

  useEffect(() => { if (!authLoading && !user) router.push('/login'); }, [user, authLoading, router]);
  useEffect(() => {
    if (user && id) {
      Promise.all([
        api.mastery.growth(id).then(setGrowth),
        api.recommendations.list(id).then(setRecommendations),
      ]).catch(() => {}).finally(() => setLoading(false));
    }
  }, [user, id]);

  const generateRec = async () => {
    setGenLoading(true);
    try {
      const rec = await api.recommendations.generate(id);
      setRecommendations(prev => [rec, ...prev]);
      setToast({ msg: 'New recommendation generated!', type: 'success' });
    } catch (err: any) {
      setToast({ msg: err.message, type: 'error' });
    }
    setGenLoading(false);
    setTimeout(() => setToast(null), 3000);
  };

  if (authLoading || !user) return <div className="mesh-bg" style={{ minHeight: '100vh' }} />;

  return (
    <div style={{ minHeight: '100vh', position: 'relative' }}>
      <div className="mesh-bg" />
      <nav style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '16px 32px', borderBottom: '1px solid var(--glass-border)' }}>
        <Link href={`/projects/${id}`} style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontSize: 14 }}>← Project</Link>
        <span style={{ color: 'var(--text-muted)' }}>/</span>
        <span style={{ fontWeight: 600, fontSize: 14 }}>📈 Growth & Recommendations</span>
      </nav>

      <div style={{ maxWidth: 900, margin: '0 auto', padding: '32px 24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
          <div>
            <h1 style={{ fontSize: 24, fontWeight: 700 }}>Growth Analysis</h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 4 }}>
              {growth?.summary || 'Track your learning progress over time'}
            </p>
          </div>
          <button onClick={generateRec} className="btn-primary" disabled={genLoading}>
            {genLoading ? 'Generating...' : '🎯 Get Recommendation'}
          </button>
        </div>

        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {[1,2,3].map(i => <div key={i} className="skeleton" style={{ height: 160 }} />)}
          </div>
        ) : (
          <>
            {/* Growth categories */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 32 }}>
              {/* Improving */}
              <div className="glass-card" style={{ padding: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                  <span style={{ fontSize: 18 }}>📈</span>
                  <h3 style={{ fontSize: 15, fontWeight: 600, color: 'var(--accent-emerald)' }}>Improving ({growth?.improving?.length || 0})</h3>
                </div>
                {growth?.improving?.length > 0 ? (
                  growth.improving.map((c: any, i: number) => (
                    <div key={i} style={{ marginBottom: 10 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                        <span>{c.concept}</span>
                        <span style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>{c.mastery.toFixed(0)}%</span>
                      </div>
                      <div className="mastery-bar">
                        <div className="mastery-bar-fill" style={{ width: `${c.mastery}%`, background: 'var(--accent-emerald)' }} />
                      </div>
                    </div>
                  ))
                ) : <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>No improving concepts yet</p>}
              </div>

              {/* Stable */}
              <div className="glass-card" style={{ padding: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                  <span style={{ fontSize: 18 }}>➡️</span>
                  <h3 style={{ fontSize: 15, fontWeight: 600, color: 'var(--accent-cyan)' }}>Stable ({growth?.stable?.length || 0})</h3>
                </div>
                {growth?.stable?.length > 0 ? (
                  growth.stable.map((c: any, i: number) => (
                    <div key={i} style={{ marginBottom: 10 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                        <span>{c.concept}</span>
                        <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>{c.mastery.toFixed(0)}%</span>
                      </div>
                      <div className="mastery-bar">
                        <div className="mastery-bar-fill" style={{ width: `${c.mastery}%`, background: 'var(--accent-cyan)' }} />
                      </div>
                    </div>
                  ))
                ) : <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>No stable concepts yet</p>}
              </div>

              {/* Needs attention */}
              <div className="glass-card" style={{ padding: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                  <span style={{ fontSize: 18 }}>⚠️</span>
                  <h3 style={{ fontSize: 15, fontWeight: 600, color: 'var(--accent-rose)' }}>Needs Attention ({growth?.needs_attention?.length || 0})</h3>
                </div>
                {growth?.needs_attention?.length > 0 ? (
                  growth.needs_attention.map((c: any, i: number) => (
                    <div key={i} style={{ marginBottom: 10 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                        <span>{c.concept}</span>
                        <span style={{ color: 'var(--accent-rose)', fontWeight: 600 }}>{c.mastery.toFixed(0)}%</span>
                      </div>
                      <div className="mastery-bar">
                        <div className="mastery-bar-fill" style={{ width: `${c.mastery}%`, background: 'var(--accent-rose)' }} />
                      </div>
                    </div>
                  ))
                ) : <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>No concepts need attention</p>}
              </div>
            </div>

            {/* Recommendations */}
            <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>🎯 Recommendations</h2>
            {recommendations.length === 0 ? (
              <div className="glass-card" style={{ padding: 32, textAlign: 'center' }}>
                <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>No recommendations yet. Click &quot;Get Recommendation&quot; to generate one based on your progress.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {recommendations.map((r, i) => (
                  <div key={r.id || i} className="glass-card" style={{ padding: 20 }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                      <span style={{ fontSize: 20 }}>{r.action_type === 'quiz' ? '🧪' : r.action_type === 'explore' ? '🔍' : r.action_type === 'revisit' ? '🔄' : '📖'}</span>
                      <div style={{ flex: 1 }}>
                        <p style={{ fontSize: 14, lineHeight: 1.7, marginBottom: 8 }}>{r.recommendation_text}</p>
                        {r.reasoning && <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>💡 {r.reasoning}</p>}
                        {r.target_concepts?.length > 0 && (
                          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 8 }}>
                            {r.target_concepts.map((c: string, j: number) => (
                              <span key={j} className="badge badge-violet">{c}</span>
                            ))}
                          </div>
                        )}
                      </div>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>{new Date(r.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}
    </div>
  );
}
