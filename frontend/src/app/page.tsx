'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import Link from 'next/link';

const features = [
  { icon: '📄', title: 'Smart Materials', desc: 'Upload PDFs and let AI extract knowledge, build semantic chunks, and create a searchable knowledge base.' },
  { icon: '🤖', title: 'AI Tutor', desc: 'Ask any question and get grounded answers with real citations pulled directly from your uploaded materials.' },
  { icon: '🧪', title: 'Adaptive Quizzes', desc: 'MCQ and open-ended questions that adapt to your mastery level, targeting your weakest concepts first.' },
  { icon: '📊', title: 'Mastery Tracking', desc: 'Evidence-based concept mastery that evolves in real-time with every quiz attempt and interaction.' },
  { icon: '📈', title: 'Growth Analysis', desc: 'Visual trend lines showing improving, stable, and attention-needed concepts across study sessions.' },
  { icon: '🎯', title: 'Smart Recommendations', desc: 'AI-generated study plans based on your unique performance patterns and learning history.' },
];

export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) router.push('/dashboard');
  }, [user, loading, router]);

  if (loading) return <div style={{ minHeight: '100vh' }} />;

  return (
    <div style={{ minHeight: '100vh' }}>
      <nav style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '0 40px', height: 60,
        borderBottom: '1px solid var(--color-border-soft)',
        position: 'sticky', top: 0, zIndex: 50,
        background: 'rgba(9,9,11,0.9)', backdropFilter: 'blur(12px)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div className="logo-mark">🧠</div>
          <span className="logo-text">StudyCompanion</span>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <Link href="/login" className="btn-secondary" style={{ textDecoration: 'none' }}>Sign in</Link>
          <Link href="/register" className="btn-primary" style={{ textDecoration: 'none' }}>Get started</Link>
        </div>
      </nav>

      <div style={{ maxWidth: 860, margin: '0 auto', padding: '96px 24px 80px', textAlign: 'center' }} className="animate-in">
        <div className="badge badge-cyan" style={{ marginBottom: 20, display: 'inline-flex' }}>AI-Powered Learning</div>

        <h1 style={{ fontSize: 'clamp(36px, 6vw, 58px)', fontWeight: 800, lineHeight: 1.08, marginBottom: 24, letterSpacing: '-0.04em' }}>
          Your intelligent{' '}
          <span className="gradient-text">study companion</span>
        </h1>

        <p style={{ fontSize: 17, color: 'var(--color-text-2)', maxWidth: 540, margin: '0 auto 40px', lineHeight: 1.75 }}>
          Upload your materials, get AI tutoring with real citations, take adaptive quizzes, and track mastery growth — all in one focused workspace.
        </p>

        <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
          <Link href="/register" className="btn-primary" style={{ textDecoration: 'none', padding: '11px 26px', fontSize: 14.5 }}>
            Start learning free →
          </Link>
          <Link href="/login" className="btn-secondary" style={{ textDecoration: 'none', padding: '11px 26px', fontSize: 14.5 }}>
            Sign in
          </Link>
        </div>

        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 0, marginTop: 80,
          border: '1px solid var(--color-border)', borderRadius: 'var(--radius-xl)', overflow: 'hidden',
        }}>
          {features.map((f, i) => (
            <div key={i} style={{
              padding: '28px 24px', background: 'var(--color-surface)', textAlign: 'left',
              borderRight: i % 3 !== 2 ? '1px solid var(--color-border)' : 'none',
              borderBottom: i < 3 ? '1px solid var(--color-border)' : 'none',
              transition: 'background 0.15s',
            }}>
              <div style={{ fontSize: 22, marginBottom: 12 }}>{f.icon}</div>
              <h3 style={{ fontSize: 14.5, fontWeight: 600, marginBottom: 8 }}>{f.title}</h3>
              <p style={{ fontSize: 13, color: 'var(--color-text-3)', lineHeight: 1.65 }}>{f.desc}</p>
            </div>
          ))}
        </div>

        <p style={{ marginTop: 40, fontSize: 12.5, color: 'var(--color-text-4)' }}>Free to start · No credit card required</p>
      </div>
    </div>
  );
}
