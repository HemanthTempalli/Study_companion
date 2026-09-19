'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import api from '@/lib/api';
import Link from 'next/link';

export default function QuizPage() {
  const { id } = useParams<{ id: string }>();
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [quiz, setQuiz] = useState<any>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<any>(null);
  const [generating, setGenerating] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [currentQ, setCurrentQ] = useState(0);
  const [numQuestions, setNumQuestions] = useState(5);
  const [toast, setToast] = useState<{ msg: string; type: string } | null>(null);
  const [history, setHistory] = useState<any[]>([]);

  useEffect(() => { if (!authLoading && !user) router.push('/login'); }, [user, authLoading, router]);
  useEffect(() => { if (user && id) api.quiz.history(id).then(setHistory).catch(() => {}); }, [user, id]);

  const generateQuiz = async () => {
    setGenerating(true);
    setResult(null);
    setAnswers({});
    setCurrentQ(0);
    try {
      const q = await api.quiz.generate(id, { num_questions: numQuestions });
      setQuiz(q);
    } catch (err: any) {
      setToast({ msg: err.message, type: 'error' });
      setTimeout(() => setToast(null), 3000);
    }
    setGenerating(false);
  };

  const submitQuiz = async () => {
    if (!quiz) return;
    const answerList = quiz.questions.map((q: any) => ({
      question_id: q.id,
      user_answer: answers[q.id] || '',
    })).filter((a: any) => a.user_answer);

    if (answerList.length === 0) {
      setToast({ msg: 'Please answer at least one question', type: 'error' });
      setTimeout(() => setToast(null), 3000);
      return;
    }

    setSubmitting(true);
    try {
      const res = await api.quiz.submit(id, quiz.id, answerList);
      setResult(res);
    } catch (err: any) {
      setToast({ msg: err.message, type: 'error' });
      setTimeout(() => setToast(null), 3000);
    }
    setSubmitting(false);
  };

  if (authLoading || !user) return <div style={{ minHeight: '100vh' }} />;

  const question = quiz?.questions?.[currentQ];
  const NAV_ITEMS = [
    { key: 'overview', label: 'Overview' }, { key: 'materials', label: 'Materials' },
    { key: 'tutor', label: 'AI Tutor' }, { key: 'quiz', label: 'Quiz' },
    { key: 'mastery', label: 'Mastery' }, { key: 'growth', label: 'Growth' }, { key: 'analytics', label: 'Analytics' },
  ];

  return (
    <div style={{ minHeight: '100vh' }}>
      <header className="topnav">
        <div className="breadcrumb">
          <Link href="/dashboard">Dashboard</Link>
          <span className="breadcrumb-sep">/</span>
          <Link href={`/projects/${id}`}>Project</Link>
          <span className="breadcrumb-sep">/</span>
          <span className="breadcrumb-current">Quiz</span>
        </div>
      </header>
      <div className="tab-bar" style={{ padding: '0 24px' }}>
        {NAV_ITEMS.map(item => (
          <Link key={item.key} href={item.key === 'overview' ? `/projects/${id}` : `/projects/${id}/${item.key}`}
            className={`tab-item${item.key === 'quiz' ? ' active' : ''}`}>{item.label}</Link>
        ))}
      </div>

      <div style={{ maxWidth: 800, margin: '0 auto', padding: '32px 24px' }}>
        {/* No quiz yet — start screen */}
        {!quiz && !result && (
          <div className="animate-in">
            <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>Adaptive Quiz</h1>

            <div className="card" style={{ padding: 36, textAlign: 'center', marginBottom: 24 }}>
              <div className="empty-icon" style={{ margin: '0 auto 20px', fontSize: 26 }}>🧪</div>
              <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Test Your Knowledge</h2>
              <p style={{ color: 'var(--color-text-3)', fontSize: 13.5, marginBottom: 28, maxWidth: 400, margin: '0 auto 24px', lineHeight: 1.65 }}>
                Questions are generated from your materials, adapted to your mastery level.
              </p>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, marginBottom: 24 }}>
                <label style={{ fontSize: 13, color: 'var(--color-text-3)', fontWeight: 500 }}>Number of questions:</label>
                <select className="input-field" value={numQuestions} onChange={e => setNumQuestions(parseInt(e.target.value))}
                  style={{ width: 76 }}>
                  {[3, 5, 7, 10].map(n => <option key={n} value={n}>{n}</option>)}
                </select>
              </div>
              <button onClick={generateQuiz} className="btn-primary" disabled={generating} style={{ padding: '10px 28px', fontSize: 14 }}>
                {generating ? 'Generating...' : 'Start Quiz'}
              </button>
            </div>

            {history.length > 0 && (
              <div>
                <p className="section-heading">Past Quizzes</p>
                {history.map(h => (
                  <div key={h.id} className="card" style={{ padding: '14px 18px', marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span style={{ fontSize: 13.5 }}>{h.total_questions} questions</span>
                      <span style={{ fontSize: 12, color: 'var(--color-text-3)', marginLeft: 10 }}>{new Date(h.created_at).toLocaleDateString()}</span>
                    </div>
                    <div style={{ fontSize: 16, fontWeight: 700, color: h.score >= 70 ? 'var(--color-success)' : h.score >= 40 ? 'var(--color-warning)' : 'var(--color-danger)' }}>
                      {h.score.toFixed(0)}%
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Active quiz */}
        {quiz && !result && question && (
          <div className="animate-in">
            {/* Progress */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
              <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>Question {currentQ + 1} of {quiz.questions.length}</span>
              <span className={`badge ${question.question_type === 'MCQ' ? 'badge-cyan' : 'badge-violet'}`}>{question.question_type}</span>
            </div>
            <div className="mastery-bar" style={{ marginBottom: 24 }}>
              <div className="mastery-bar-fill" style={{ width: `${((currentQ + 1) / quiz.questions.length) * 100}%`, background: 'var(--color-accent)' }} />
            </div>

            <div className="card" style={{ padding: 28, marginBottom: 24 }}>
              {question.concept_name && <span className="badge badge-violet" style={{ marginBottom: 14, display: 'inline-block' }}>{question.concept_name}</span>}
              <h2 style={{ fontSize: 17, fontWeight: 600, marginBottom: 20, lineHeight: 1.65 }}>{question.question_text}</h2>

              {question.question_type === 'MCQ' && question.options ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {question.options.map((opt: string, i: number) => (
                    <button key={i} onClick={() => setAnswers({ ...answers, [question.id]: opt })}
                      style={{
                        padding: '12px 16px', borderRadius: 'var(--radius)', textAlign: 'left', fontSize: 13.5,
                        background: answers[question.id] === opt ? 'var(--color-accent-dim)' : 'var(--color-surface-2)',
                        border: answers[question.id] === opt ? '1px solid var(--color-accent-border)' : '1px solid var(--color-border)',
                        color: answers[question.id] === opt ? 'var(--color-accent)' : 'var(--color-text)', cursor: 'pointer', transition: 'all 0.15s',
                      }}>
                      {opt}
                    </button>
                  ))}
                </div>
              ) : (
                <textarea className="input-field" rows={4} value={answers[question.id] || ''} onChange={e => setAnswers({ ...answers, [question.id]: e.target.value })}
                  placeholder="Type your answer..." style={{ resize: 'vertical' }} />
              )}
              {question.source_page && <p style={{ fontSize: 12, color: 'var(--color-text-3)', marginTop: 12 }}>📄 {question.source_page}</p>}
            </div>

            {/* Navigation */}
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <button onClick={() => setCurrentQ(Math.max(0, currentQ - 1))} className="btn-secondary" disabled={currentQ === 0}>← Previous</button>
              {currentQ < quiz.questions.length - 1 ? (
                <button onClick={() => setCurrentQ(currentQ + 1)} className="btn-primary">Next →</button>
              ) : (
                <button onClick={submitQuiz} className="btn-primary" disabled={submitting}>
                  {submitting ? 'Evaluating...' : 'Submit Quiz'}
                </button>
              )}
            </div>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="animate-in">
            <div className="card" style={{ padding: 32, textAlign: 'center', marginBottom: 20 }}>
              <div style={{ fontSize: 36, marginBottom: 12 }}>{result.score >= 70 ? '🎉' : result.score >= 40 ? '💪' : '📚'}</div>
              <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 6 }}>
                {result.score >= 70 ? 'Great job!' : result.score >= 40 ? 'Good effort!' : 'Keep studying!'}
              </h2>
              <div style={{ fontSize: 44, fontWeight: 800, color: result.score >= 70 ? 'var(--color-success)' : result.score >= 40 ? 'var(--color-warning)' : 'var(--color-danger)', marginBottom: 6, letterSpacing: '-0.03em' }}>
                {result.score.toFixed(0)}%
              </div>
              <p style={{ color: 'var(--color-text-3)', fontSize: 13.5 }}>{result.correct_answers}/{result.total_questions} correct</p>
            </div>

            {result.question_results?.map((qr: any, i: number) => {
              const q = quiz?.questions?.[i];
              return (
                <div key={i} className="card" style={{ padding: 18, marginBottom: 10 }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 8 }}>
                    <span style={{ fontSize: 16, flexShrink: 0 }}>{qr.is_correct ? '✅' : '❌'}</span>
                    <span style={{ fontSize: 13.5, fontWeight: 600, flex: 1, lineHeight: 1.5 }}>{q?.question_text}</span>
                    <span style={{ fontSize: 13, fontWeight: 700, color: qr.is_correct ? 'var(--color-success)' : 'var(--color-danger)', flexShrink: 0 }}>
                      {qr.score.toFixed(0)}%
                    </span>
                  </div>
                  <p style={{ fontSize: 12.5, color: 'var(--color-success)', marginBottom: 4 }}>✓ {qr.correct_answer}</p>
                  {qr.explanation && <p style={{ fontSize: 12.5, color: 'var(--color-text-3)', lineHeight: 1.6 }}>{qr.explanation}</p>}
                  {qr.feedback?.explanation && <p style={{ fontSize: 12.5, color: 'var(--color-text-3)', marginTop: 4, lineHeight: 1.6 }}>{qr.feedback.explanation}</p>}
                </div>
              );
            })}

            {result.mastery_updates?.length > 0 && (
              <div className="card" style={{ padding: 20, marginTop: 12 }}>
                <p className="section-heading">Mastery Updates</p>
                {result.mastery_updates.map((mu: any, i: number) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                    <span style={{ fontSize: 13, flex: 1 }}>{mu.concept}</span>
                    <span style={{ fontSize: 12, color: 'var(--color-text-3)' }}>{mu.old_mastery.toFixed(0)}%</span>
                    <span style={{ color: mu.direction === 'up' ? 'var(--color-success)' : mu.direction === 'down' ? 'var(--color-danger)' : 'var(--color-text-4)', fontWeight: 600 }}>
                      {mu.direction === 'up' ? '↑' : mu.direction === 'down' ? '↓' : '→'}
                    </span>
                    <span style={{ fontSize: 12.5, fontWeight: 700 }}>{mu.new_mastery.toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            )}

            <div style={{ display: 'flex', gap: 10, marginTop: 20 }}>
              <button onClick={() => { setQuiz(null); setResult(null); }} className="btn-primary">Take Another Quiz</button>
              <Link href={`/projects/${id}/mastery`} className="btn-secondary" style={{ textDecoration: 'none' }}>View Mastery</Link>
            </div>
          </div>
        )}
      </div>
      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}
    </div>
  );
}
