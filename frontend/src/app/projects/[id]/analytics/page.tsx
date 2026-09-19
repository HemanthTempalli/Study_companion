'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import api from '@/lib/api';
import Link from 'next/link';
import dynamic from 'next/dynamic';

const BarChart = dynamic(() => import('recharts').then(m => m.BarChart), { ssr: false });
const Bar = dynamic(() => import('recharts').then(m => m.Bar), { ssr: false });
const LineChart = dynamic(() => import('recharts').then(m => m.LineChart), { ssr: false });
const Line = dynamic(() => import('recharts').then(m => m.Line), { ssr: false });
const XAxis = dynamic(() => import('recharts').then(m => m.XAxis), { ssr: false });
const YAxis = dynamic(() => import('recharts').then(m => m.YAxis), { ssr: false });
const Tooltip = dynamic(() => import('recharts').then(m => m.Tooltip), { ssr: false });
const ResponsiveContainer = dynamic(() => import('recharts').then(m => m.ResponsiveContainer), { ssr: false });

export default function AnalyticsPage() {
  const { id } = useParams<{ id: string }>();
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { if (!authLoading && !user) router.push('/login'); }, [user, authLoading, router]);
  useEffect(() => {
    if (user && id) {
      api.analytics.project(id).then(setAnalytics).catch(() => {}).finally(() => setLoading(false));
    }
  }, [user, id]);

  if (authLoading || !user) return <div className="mesh-bg" style={{ minHeight: '100vh' }} />;

  return (
    <div style={{ minHeight: '100vh', position: 'relative' }}>
      <div className="mesh-bg" />
      <nav style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '16px 32px', borderBottom: '1px solid var(--glass-border)' }}>
        <Link href={`/projects/${id}`} style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontSize: 14 }}>← Project</Link>
        <span style={{ color: 'var(--text-muted)' }}>/</span>
        <span style={{ fontWeight: 600, fontSize: 14 }}>⚡ Analytics</span>
      </nav>

      <div style={{ maxWidth: 1000, margin: '0 auto', padding: '32px 24px' }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 32 }}>Project Analytics</h1>

        {loading ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16 }}>
            {[1,2,3,4].map(i => <div key={i} className="skeleton" style={{ height: 200 }} />)}
          </div>
        ) : (
          <>
            {/* Stats */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 32 }}>
              {[
                { label: 'Materials', value: analytics?.total_materials || 0, color: 'var(--accent-cyan)' },
                { label: 'Conversations', value: analytics?.total_conversations || 0, color: 'var(--accent-violet)' },
                { label: 'Quizzes', value: analytics?.total_quizzes || 0, color: 'var(--accent-emerald)' },
                { label: 'Questions Answered', value: analytics?.total_questions_answered || 0, color: 'var(--accent-amber)' },
              ].map((s, i) => (
                <div key={i} className="glass-card" style={{ padding: 20, textAlign: 'center' }}>
                  <div style={{ fontSize: 28, fontWeight: 800, color: s.color }}>{s.value}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>{s.label}</div>
                </div>
              ))}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
              {/* Mastery Distribution */}
              <div className="glass-card" style={{ padding: 24 }}>
                <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Mastery by Concept</h3>
                {analytics?.mastery_distribution?.length > 0 ? (
                  <div style={{ width: '100%', height: 250 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={analytics.mastery_distribution}>
                        <XAxis dataKey="concept" tick={{ fill: '#8b8b9e', fontSize: 10 }} angle={-30} textAnchor="end" height={60} />
                        <YAxis tick={{ fill: '#8b8b9e', fontSize: 11 }} domain={[0, 100]} />
                        <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#e8e8ed' }} />
                        <Bar dataKey="mastery" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                ) : <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>No mastery data available</p>}
              </div>

              {/* Quiz Performance */}
              <div className="glass-card" style={{ padding: 24 }}>
                <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Quiz Performance Over Time</h3>
                {analytics?.assessment_performance?.length > 0 ? (
                  <div style={{ width: '100%', height: 250 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={analytics.assessment_performance.map((d: any) => ({ ...d, date: new Date(d.date).toLocaleDateString() }))}>
                        <XAxis dataKey="date" tick={{ fill: '#8b8b9e', fontSize: 10 }} />
                        <YAxis tick={{ fill: '#8b8b9e', fontSize: 11 }} domain={[0, 100]} />
                        <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#e8e8ed' }} />
                        <Line type="monotone" dataKey="score" stroke="#10b981" strokeWidth={2} dot={{ fill: '#10b981', r: 4 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                ) : <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>No quiz data available</p>}
              </div>

              {/* Learning Activity */}
              <div className="glass-card" style={{ padding: 24 }}>
                <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Learning Activity (30 days)</h3>
                {analytics?.learning_activity?.length > 0 ? (
                  <div style={{ width: '100%', height: 250 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={analytics.learning_activity.map((d: any) => ({ ...d, date: new Date(d.date).toLocaleDateString() }))}>
                        <XAxis dataKey="date" tick={{ fill: '#8b8b9e', fontSize: 10 }} />
                        <YAxis tick={{ fill: '#8b8b9e', fontSize: 11 }} />
                        <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#e8e8ed' }} />
                        <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                ) : <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>No activity data available</p>}
              </div>

              {/* AI Usage */}
              <div className="glass-card" style={{ padding: 24 }}>
                <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>AI Usage</h3>
                {analytics?.ai_activity && Object.keys(analytics.ai_activity).length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {Object.entries(analytics.ai_activity).map(([feature, data]: any) => (
                      <div key={feature} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: 'rgba(255,255,255,0.02)', borderRadius: 8 }}>
                        <span style={{ fontSize: 13, fontWeight: 500 }}>{feature}</span>
                        <div style={{ display: 'flex', gap: 12 }}>
                          <span className="badge badge-cyan">{data.count} calls</span>
                          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{data.avg_latency_ms}ms avg</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>No AI usage data</p>}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
