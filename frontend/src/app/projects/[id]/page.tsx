'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import api from '@/lib/api';
import Link from 'next/link';

const NAV = [
  { key: 'overview', label: 'Overview', icon: '□' },
  { key: 'materials', label: 'Materials', icon: '📄' },
  { key: 'tutor', label: 'AI Tutor', icon: '🤖' },
  { key: 'quiz', label: 'Quiz', icon: '🧪' },
  { key: 'mastery', label: 'Mastery', icon: '📊' },
  { key: 'growth', label: 'Growth', icon: '📈' },
  { key: 'analytics', label: 'Analytics', icon: '⚡' },
];

export default function ProjectPage() {
  const { id } = useParams<{ id: string }>();
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [dashboard, setDashboard] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { if (!authLoading && !user) router.push('/login'); }, [user, authLoading, router]);
  useEffect(() => {
    if (user && id) {
      api.projects.dashboard(id)
        .then(setDashboard)
        .catch(() => router.push('/dashboard'))
        .finally(() => setLoading(false));
    }
  }, [user, id, router]);

  if (authLoading || !user || loading) {
    return (
      <div style={{ minHeight: '100vh' }}>
        <div className="topnav" />
        <div style={{ maxWidth: 1100, margin: '0 auto', padding: '40px 24px' }}>
          {[1,2,3].map(i => <div key={i} className="skeleton" style={{ height: 100, marginBottom: 12 }} />)}
        </div>
      </div>
    );
  }

  const project = dashboard?.project;
  const mastery = dashboard?.mastery_summary || {};
  const quizStats = dashboard?.quiz_stats || {};

  return (
    <div style={{ minHeight: '100vh' }}>
      <header className="topnav">
        <div className="breadcrumb">
          <Link href="/dashboard">Dashboard</Link>
          <span className="breadcrumb-sep">/</span>
          <span className="breadcrumb-current">{project?.name}</span>
        </div>
      </header>

      {/* Tab nav */}
      <div className="tab-bar" style={{ padding: '0 24px' }}>
        {NAV.map(item => (
          <Link
            key={item.key}
            href={item.key === 'overview' ? `/projects/${id}` : `/projects/${id}/${item.key}`}
            className={`tab-item${item.key === 'overview' ? ' active' : ''}`}
          >
            <span style={{ fontSize: 12 }}>{item.icon}</span> {item.label}
          </Link>
        ))}
      </div>

      <main style={{ maxWidth: 1100, margin: '0 auto', padding: '36px 24px' }}>
        <div style={{ marginBottom: 36 }}>
          <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 6 }}>{project?.name}</h1>
          {project?.learning_goal && (
            <p style={{ fontSize: 14, color: 'var(--color-text-3)' }}>Goal: {project.learning_goal}</p>
          )}
        </div>

        {/* Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 28 }}>
          {[
            { label: 'Materials', value: project?.material_count || 0 },
            { label: 'Concepts', value: project?.concept_count || 0 },
            { label: 'Avg Mastery', value: `${mastery?.average || 0}%` },
            { label: 'Quizzes Taken', value: quizStats?.total_quizzes || 0 },
          ].map((s, i) => (
            <div key={i} className="stat-card">
              <div className="stat-value">{s.value}</div>
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {/* Recommendation */}
          <div className="card" style={{ padding: 24 }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 14, color: 'var(--color-text-2)', display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>🎯</span> Recommendation
            </h3>
            {dashboard?.recommendation ? (
              <p style={{ fontSize: 13.5, color: 'var(--color-text-2)', lineHeight: 1.7 }}>{dashboard.recommendation}</p>
            ) : (
              <p style={{ fontSize: 13, color: 'var(--color-text-4)', lineHeight: 1.65 }}>
                Upload materials and take quizzes to get personalized study recommendations.
              </p>
            )}
          </div>

          {/* Mastery */}
          <div className="card" style={{ padding: 24 }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 14, color: 'var(--color-text-2)', display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>📊</span> Mastery Overview
            </h3>
            {mastery?.weak_concepts?.length > 0 ? (
              <div>
                <p style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--color-danger)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Needs attention</p>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 12 }}>
                  {mastery.weak_concepts.map((c: string, i: number) => (
                    <span key={i} className="badge badge-rose">{c}</span>
                  ))}
                </div>
                {mastery?.strong_concepts?.length > 0 && (
                  <>
                    <p style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--color-success)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Strong</p>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      {mastery.strong_concepts.map((c: string, i: number) => (
                        <span key={i} className="badge badge-emerald">{c}</span>
                      ))}
                    </div>
                  </>
                )}
              </div>
            ) : (
              <p style={{ fontSize: 13, color: 'var(--color-text-4)', lineHeight: 1.65 }}>
                No mastery data yet. Take a quiz to start tracking concepts.
              </p>
            )}
          </div>
        </div>

        {/* Recent Activity */}
        {dashboard?.recent_activity?.length > 0 && (
          <div className="card" style={{ padding: 24, marginTop: 16 }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16, color: 'var(--color-text-2)' }}>Recent Activity</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {dashboard.recent_activity.slice(0, 5).map((ev: any, i: number) => (
                <div key={i} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '9px 12px', borderRadius: 'var(--radius)',
                  background: i % 2 === 0 ? 'var(--color-surface-2)' : 'transparent',
                }}>
                  <span style={{ fontSize: 13, color: 'var(--color-text-2)', textTransform: 'capitalize' }}>
                    {ev.type.replace(/_/g, ' ').toLowerCase()}
                  </span>
                  <span style={{ fontSize: 12, color: 'var(--color-text-4)' }}>
                    {new Date(ev.created_at).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Quick nav cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginTop: 24 }}>
          {NAV.slice(1).map(item => (
            <Link key={item.key} href={`/projects/${id}/${item.key}`} style={{ textDecoration: 'none', color: 'inherit' }}>
              <div className="card card-interactive" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ fontSize: 20 }}>{item.icon}</span>
                <div>
                  <p style={{ fontSize: 13.5, fontWeight: 600 }}>{item.label}</p>
                  <p style={{ fontSize: 12, color: 'var(--color-text-3)', marginTop: 1 }}>Open →</p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}