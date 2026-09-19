'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import Link from 'next/link';

export default function RegisterPage() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (password.length < 8) { setError('Password must be at least 8 characters'); return; }
    setLoading(true);
    try {
      await register(email, password, fullName);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Registration failed');
    }
    setLoading(false);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
      <div style={{ width: '100%', maxWidth: 400 }} className="animate-in">
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ width: 44, height: 44, borderRadius: 12, background: 'var(--color-accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, margin: '0 auto 16px' }}>🧠</div>
          <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 6 }}>Create your account</h1>
          <p style={{ fontSize: 13.5, color: 'var(--color-text-3)' }}>Start your learning journey today</p>
        </div>

        <div className="card" style={{ padding: 28 }}>
          {error && (
            <div style={{ padding: '10px 14px', borderRadius: 'var(--radius)', background: 'var(--color-danger-dim)', border: '1px solid rgba(239,68,68,0.25)', color: 'var(--color-danger)', fontSize: 13, marginBottom: 20 }}>
              {error}
            </div>
          )}
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--color-text-2)', marginBottom: 6 }}>Full name</label>
              <input className="input-field" value={fullName} onChange={e => setFullName(e.target.value)} placeholder="Your name" required />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--color-text-2)', marginBottom: 6 }}>Email</label>
              <input className="input-field" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" required />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 500, color: 'var(--color-text-2)', marginBottom: 6 }}>Password</label>
              <input className="input-field" type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Minimum 8 characters" required />
            </div>
            <button type="submit" className="btn-primary" disabled={loading} style={{ marginTop: 4, width: '100%', padding: '10px 16px', fontSize: 14 }}>
              {loading ? 'Creating account...' : 'Create account'}
            </button>
          </form>
        </div>

        <p style={{ textAlign: 'center', fontSize: 13, color: 'var(--color-text-3)', marginTop: 20 }}>
          Already have an account?{' '}
          <Link href="/login" style={{ color: 'var(--color-accent)', textDecoration: 'none', fontWeight: 500 }}>Sign in</Link>
        </p>
      </div>
    </div>
  );
}
