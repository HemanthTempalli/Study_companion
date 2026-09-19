'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import api from '@/lib/api';
import Link from 'next/link';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const NAV = [
  { key: 'overview', label: 'Overview' },
  { key: 'materials', label: 'Materials' },
  { key: 'tutor', label: 'AI Tutor' },
  { key: 'quiz', label: 'Quiz' },
  { key: 'mastery', label: 'Mastery' },
  { key: 'growth', label: 'Growth' },
  { key: 'analytics', label: 'Analytics' },
];

const QUICK_PROMPTS = ['What are the key concepts?', 'Explain the main topic', 'Summarize chapter 1'];

// Typewriter component for progressive text reveal
function TypewriterMessage({ content, animate }: { content: string, animate: boolean }) {
  const [displayedContent, setDisplayedContent] = useState(animate ? '' : content);
  const [isTyping, setIsTyping] = useState(animate);

  useEffect(() => {
    if (!animate) {
      setDisplayedContent(content);
      return;
    }

    let currentIndex = 0;
    setDisplayedContent('');
    setIsTyping(true);

    const intervalId = setInterval(() => {
      // Reveal 2 characters at a time for faster, smoother typing
      currentIndex += 2;
      
      if (currentIndex >= content.length) {
        currentIndex = content.length;
        clearInterval(intervalId);
        setIsTyping(false);
      }
      setDisplayedContent(content.substring(0, currentIndex));
    }, 10);

    return () => clearInterval(intervalId);
  }, [content, animate]);

  return (
    <div className="relative">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {displayedContent}
      </ReactMarkdown>
      {isTyping && (
        <span style={{ 
          display: 'inline-block', width: 6, height: 14, 
          background: 'var(--color-text-2)', marginLeft: 4, 
          animation: 'blink 1s step-end infinite', verticalAlign: 'middle'
        }} />
      )}
    </div>
  );
}

export default function TutorPage() {
  const { id } = useParams<{ id: string }>();
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<any[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => { if (!authLoading && !user) router.push('/login'); }, [user, authLoading, router]);
  useEffect(() => {
    if (user && id) api.tutor.conversations(id).then(setConversations).catch(() => {});
  }, [user, id]);
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const loadConversation = async (convId: string) => {
    // When loading history, don't animate the typewriter effect
    const msgs = await api.tutor.messages(id, convId);
    setMessages(msgs.map((m: any) => ({ ...m, animate: false }))); 
    setConversationId(convId);
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg, created_at: new Date().toISOString() }]);
    setLoading(true);
    try {
      const res = await api.tutor.chat(id, { message: userMsg, conversation_id: conversationId || undefined });
      setConversationId(res.conversation_id);
      setMessages(prev => [...prev, {
        role: 'assistant', content: res.answer, citations: res.citations,
        has_sufficient_evidence: res.has_sufficient_evidence, created_at: new Date().toISOString(),
        animate: true // Only animate new messages
      }]);
    } catch (err: any) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${err.message || 'Failed to get response'}`, created_at: new Date().toISOString(), animate: true }]);
    }
    setLoading(false);
  };

  const newConversation = () => { setConversationId(null); setMessages([]); };

  if (authLoading || !user) return <div style={{ minHeight: '100vh' }} />;

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header className="topnav">
        <div className="breadcrumb">
          <Link href="/dashboard">Dashboard</Link>
          <span className="breadcrumb-sep">/</span>
          <Link href={`/projects/${id}`}>Project</Link>
          <span className="breadcrumb-sep">/</span>
          <span className="breadcrumb-current">AI Tutor</span>
        </div>
        <button onClick={newConversation} className="btn-secondary" style={{ fontSize: 13, padding: '6px 14px' }}>+ New Chat</button>
      </header>

      <div className="tab-bar" style={{ padding: '0 24px' }}>
        {NAV.map(item => (
          <Link key={item.key} href={item.key === 'overview' ? `/projects/${id}` : `/projects/${id}/${item.key}`}
            className={`tab-item${item.key === 'tutor' ? ' active' : ''}`}>
            {item.label}
          </Link>
        ))}
      </div>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Conversation sidebar */}
        <div style={{
          width: 220, borderRight: '1px solid var(--color-border-soft)',
          padding: '16px 12px', overflowY: 'auto', flexShrink: 0,
          background: 'var(--color-bg)',
        }}>
          <p className="section-heading" style={{ padding: '0 4px' }}>History</p>
          {conversations.length === 0 ? (
            <p style={{ fontSize: 12.5, color: 'var(--color-text-4)', padding: '4px 4px', lineHeight: 1.5 }}>No conversations yet</p>
          ) : (
            conversations.map(c => (
              <button key={c.id} onClick={() => loadConversation(c.id)} style={{
                display: 'block', width: '100%', textAlign: 'left', padding: '8px 10px',
                borderRadius: 'var(--radius)', fontSize: 13, cursor: 'pointer', marginBottom: 2,
                background: conversationId === c.id ? 'var(--color-accent-dim)' : 'transparent',
                color: conversationId === c.id ? 'var(--color-accent)' : 'var(--color-text-3)',
                border: '1px solid transparent',
                borderColor: conversationId === c.id ? 'var(--color-accent-border)' : 'transparent',
                transition: 'all 0.15s',
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}>
                {c.title}
              </button>
            ))
          )}
        </div>

        {/* Chat area */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ flex: 1, overflowY: 'auto', padding: '24px 32px', maxWidth: 800, width: '100%', margin: '0 auto', boxSizing: 'border-box' }}>
            {messages.length === 0 && (
              <div style={{ textAlign: 'center', paddingTop: 60 }}>
                <div style={{ width: 56, height: 56, background: 'var(--color-surface-2)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-xl)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 26, margin: '0 auto 20px' }}>🤖</div>
                <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Ask me anything</h2>
                <p style={{ fontSize: 13.5, color: 'var(--color-text-3)', maxWidth: 360, margin: '0 auto 28px', lineHeight: 1.65 }}>
                  I will answer based on your uploaded documents with proper citations.
                </p>
                <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap' }}>
                  {QUICK_PROMPTS.map(q => (
                    <button key={q} onClick={() => setInput(q)} className="btn-secondary" style={{ fontSize: 12.5, padding: '7px 14px' }}>
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, i) => (
              <div key={i} style={{ marginBottom: 20, display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }} className="animate-in">
                <div className={msg.role === 'user' ? 'chat-user chat-bubble' : 'chat-assistant chat-bubble'}>
                  <div className={msg.role === 'user' ? '' : 'prose prose-invert max-w-none text-[14px] leading-relaxed markdown-content'}>
                    {msg.role === 'user' ? (
                      <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.7 }}>{msg.content}</div>
                    ) : (
                      <TypewriterMessage content={msg.content} animate={msg.animate} />
                    )}
                  </div>

                  {msg.citations?.length > 0 && (
                    <div style={{ marginTop: 12, paddingTop: 10, borderTop: '1px solid rgba(255,255,255,0.08)', animation: msg.animate ? 'fadeIn 0.5s ease 1.5s both' : 'none' }}>
                      <p style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-3)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Sources</p>
                      {msg.citations.map((c: any, j: number) => (
                        <div key={j} style={{ fontSize: 12, color: 'var(--color-text-3)', padding: '4px 8px', background: 'rgba(255,255,255,0.04)', borderRadius: 'var(--radius-sm)', marginBottom: 3 }}>
                          {c.material_name} — Page {c.page_number}
                        </div>
                      ))}
                    </div>
                  )}

                  {msg.has_sufficient_evidence === false && (
                    <div style={{ marginTop: 10, padding: '8px 12px', background: 'var(--color-warning-dim)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: 'var(--radius)', fontSize: 12, color: 'var(--color-warning)', animation: msg.animate ? 'fadeIn 0.5s ease 1s both' : 'none' }}>
                      ⚠ Answer based on general knowledge — limited document coverage
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 20 }}>
                <div className="chat-assistant chat-bubble">
                  <div style={{ display: 'flex', gap: 5, alignItems: 'center', padding: '4px 0' }}>
                    {[0, 0.2, 0.4].map((delay, i) => (
                      <div key={i} style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--color-text-3)', animation: 'pulse 1.2s ease infinite', animationDelay: `${delay}s` }} />
                    ))}
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input bar */}
          <div style={{ padding: '16px 32px', borderTop: '1px solid var(--color-border-soft)', background: 'var(--color-bg)' }}>
            <div style={{ display: 'flex', gap: 10, maxWidth: 800, margin: '0 auto' }}>
              <input
                className="input-field"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), sendMessage())}
                placeholder="Ask about your materials..."
                disabled={loading}
                style={{ flex: 1, height: 42 }}
              />
              <button onClick={sendMessage} className="btn-primary" disabled={loading || !input.trim()} style={{ flexShrink: 0, padding: '0 20px', height: 42 }}>
                Send
              </button>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
          40% { transform: scale(1); opacity: 1; }
        }
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
      `}</style>
    </div>
  );
}