'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import api from '@/lib/api';
import Link from 'next/link';

export default function MasteryPage() {
  const { id } = useParams<{ id: string }>();
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [mastery, setMastery] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { if (!authLoading && !user) router.push('/login'); }, [user, authLoading, router]);
  useEffect(() => {
    if (user && id) {
      api.mastery.get(id).then(setMastery).catch(() => {}).finally(() => setLoading(false));
    }
  }, [user, id]);

  const masteryColor = (level: number) => {
    if (level >= 80) return 'var(--accent-emerald)';
    if (level >= 60) return 'var(--accent-cyan)';
    if (level >= 40) return 'var(--accent-amber)';
    return 'var(--accent-rose)';
  };

  const trendIcon = (t: string) => {
    if (t === 'improving') return '📈';
    if (t === 'declining') return '📉';
    return '➡️';
  };

  if (authLoading || !user) return <div className="mesh-bg" style={{ minHeight: '100vh' }} />;

  return (
    <div style={{ minHeight: '100vh', position: 'relative' }}>
      <div className="mesh-bg" />
      <nav style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '16px 32px', borderBottom: '1px solid var(--glass-border)' }}>
        <Link href={`/projects/${id}`} style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontSize: 14 }}>← Project</Link>
        <span style={{ color: 'var(--text-muted)' }}>/</span>
        <span style={{ fontWeight: 600, fontSize: 14 }}>📊 Mastery</span>
      </nav>

      <div style={{ maxWidth: 800, margin: '0 auto', padding: '32px 24px' }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Concept Mastery</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 32 }}>
          Evidence-based estimates of your understanding. Updated with every quiz and interaction.
        </p>

        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {[1,2,3,4,5].map(i => <div key={i} className="skeleton" style={{ height: 80 }} />)}
          </div>
        ) : mastery.length === 0 ? (
          <div className="glass-card" style={{ padding: 48, textAlign: 'center' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>📊</div>
            <h2 style={{ fontSize: 18, fontWeight: 600 }}>No mastery data yet</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 8, marginBottom: 20 }}>
              Take a quiz or interact with the AI Tutor to start building mastery records.
            </p>
            <Link href={`/projects/${id}/quiz`} className="btn-primary" style={{ textDecoration: 'none' }}>Take a Quiz →</Link>
          </div>
        ) : (
          <>
            {/* Summary stats */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 32 }}>
              <div className="glass-card" style={{ padding: 20, textAlign: 'center' }}>
                <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--accent-cyan)' }}>
                  {(mastery.reduce((s, m) => s + m.mastery_level, 0) / mastery.length).toFixed(0)}%
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>Average Mastery</div>
              </div>
              <div className="glass-card" style={{ padding: 20, textAlign: 'center' }}>
                <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--accent-emerald)' }}>
                  {mastery.filter(m => m.mastery_level >= 80).length}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>Mastered</div>
              </div>
              <div className="glass-card" style={{ padding: 20, textAlign: 'center' }}>
                <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--accent-rose)' }}>
                  {mastery.filter(m => m.mastery_level < 50).length}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>Needs Work</div>
              </div>
            </div>

            {/* Concept list */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {mastery.sort((a, b) => a.mastery_level - b.mastery_level).map((m, i) => (
                <div key={i} className="glass-card" style={{ padding: 20 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: 14, fontWeight: 600 }}>{m.concept_name}</span>
                      <span style={{ fontSize: 12 }}>{trendIcon(m.trend)}</span>
                    </div>
                    <span style={{ fontSize: 18, fontWeight: 800, color: masteryColor(m.mastery_level) }}>
                      {m.mastery_level.toFixed(0)}%
                    </span>
                  </div>
                  <div className="mastery-bar">
                    <div className="mastery-bar-fill" style={{ width: `${m.mastery_level}%`, background: masteryColor(m.mastery_level) }} />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8, fontSize: 11, color: 'var(--text-muted)' }}>
                    <span>{m.evidence_count} evidence points</span>
                    <span>{m.trend}</span>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
