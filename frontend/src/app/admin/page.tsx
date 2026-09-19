'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import api from '@/lib/api';
import Link from 'next/link';

export default function AdminPage() {
  const { user, loading: authLoading, isAdmin } = useAuth();
  const router = useRouter();
  
  const [tab, setTab] = useState<'users' | 'projects' | 'health' | 'ai' | 'evals' | 'jobs'>('users');
  
  // Data states
  const [users, setUsers] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [health, setHealth] = useState<any>(null);
  const [aiLogs, setAiLogs] = useState<any[]>([]);
  const [evals, setEvals] = useState<any[]>([]);
  const [jobs, setJobs] = useState<any[]>([]);
  const [globalStats, setGlobalStats] = useState<any>(null);
  
  // UI states
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState<any>(null);
  const [journey, setJourney] = useState<any>(null);
  
  // Filter states
  const [userSearch, setUserSearch] = useState('');
  const [projectSearch, setProjectSearch] = useState('');
  
  const [aiFeature, setAiFeature] = useState('');
  const [aiModel, setAiModel] = useState('');
  const [aiStatus, setAiStatus] = useState('');
  
  const [evFeature, setEvFeature] = useState('');
  const [evPassed, setEvPassed] = useState('');
  
  const [jobStatus, setJobStatus] = useState('');
  const [jobType, setJobType] = useState('');

  useEffect(() => {
    if (!authLoading && !user) router.push('/login');
    if (!authLoading && user && !isAdmin) router.push('/dashboard');
  }, [user, authLoading, isAdmin, router]);

  useEffect(() => {
    if (user && isAdmin) {
      loadInitialData();
    }
  }, [user, isAdmin]);

  // Load static or un-paginated data once
  const loadInitialData = async () => {
    try {
      const [u, p, h, g] = await Promise.all([
        api.admin.users(),
        api.admin.projects(),
        api.admin.health(),
        api.analytics.global(),
      ]);
      setUsers(u); setProjects(p); setHealth(h); setGlobalStats(g);
    } catch { }
    setLoading(false);
  };

  // Reload filtered lists when filters or tabs change
  useEffect(() => {
    if (!user || !isAdmin) return;
    if (tab === 'ai') {
      api.admin.aiLogs(100, aiFeature, aiModel, aiStatus).then(setAiLogs).catch(()=>{});
    } else if (tab === 'evals') {
      const passedBool = evPassed === 'true' ? true : evPassed === 'false' ? false : undefined;
      api.admin.evaluations(100, evFeature, passedBool).then(setEvals).catch(()=>{});
    } else if (tab === 'jobs') {
      api.admin.jobs(jobStatus, jobType, 100).then(setJobs).catch(()=>{});
    }
  }, [tab, aiFeature, aiModel, aiStatus, evFeature, evPassed, jobStatus, jobType, user, isAdmin]);

  const viewJourney = async (userId: string) => {
    try {
      const j = await api.admin.userJourney(userId);
      setJourney(j);
      setSelectedUser(userId);
    } catch { }
  };

  if (authLoading || !user || !isAdmin) return <div className="mesh-bg" style={{ minHeight: '100vh' }} />;

  // Client side filtering for users and projects
  const filteredUsers = users.filter(u => 
    u.full_name.toLowerCase().includes(userSearch.toLowerCase()) || 
    u.email.toLowerCase().includes(userSearch.toLowerCase())
  );
  
  const filteredProjects = projects.filter(p => 
    p.name.toLowerCase().includes(projectSearch.toLowerCase()) || 
    p.user_email.toLowerCase().includes(projectSearch.toLowerCase())
  );

  return (
    <div style={{ minHeight: '100vh', position: 'relative' }}>
      <div className="mesh-bg" />
      <nav style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 32px', borderBottom: '1px solid var(--glass-border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Link href="/dashboard" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontSize: 14 }}>← Dashboard</Link>
          <span style={{ color: 'var(--text-muted)' }}>/</span>
          <span style={{ fontWeight: 600, fontSize: 14 }}>🔧 Admin</span>
        </div>
      </nav>

      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '32px 24px' }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>Admin Dashboard</h1>

        {/* Global Stats */}
        {globalStats && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12, marginBottom: 32 }}>
            {[
              { label: 'Users', value: globalStats.total_users, color: 'var(--accent-cyan)' },
              { label: 'Projects', value: globalStats.total_projects, color: 'var(--accent-violet)' },
              { label: 'Materials', value: globalStats.total_materials, color: 'var(--accent-emerald)' },
              { label: 'Quizzes', value: globalStats.total_quizzes, color: 'var(--accent-amber)' },
              { label: 'AI Requests', value: globalStats.ai_requests, color: 'var(--accent-rose)' },
            ].map((s, i) => (
              <div key={i} className="glass-card" style={{ padding: 16, textAlign: 'center' }}>
                <div style={{ fontSize: 24, fontWeight: 800, color: s.color }}>{s.value}</div>
                <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>{s.label}</div>
              </div>
            ))}
          </div>
        )}

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 24, overflowX: 'auto', paddingBottom: 4 }}>
          {(['users', 'projects', 'health', 'ai', 'evals', 'jobs'] as const).map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={tab === t ? 'btn-primary' : 'btn-secondary'}
              style={{ padding: '8px 16px', fontSize: 13, textTransform: 'capitalize', flexShrink: 0 }}>
              {t === 'ai' ? 'AI Usage' : t === 'evals' ? 'AI Evaluations' : t}
            </button>
          ))}
        </div>

        {/* Users Tab */}
        {tab === 'users' && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <input 
                type="text" 
                className="input-field" 
                placeholder="Search users by name or email..." 
                value={userSearch} 
                onChange={e => setUserSearch(e.target.value)}
                style={{ maxWidth: 300 }}
              />
            </div>
            
            {journey && (
              <div className="glass-card animate-in" style={{ padding: 24, marginBottom: 20 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                  <h3 style={{ fontSize: 16, fontWeight: 600 }}>📚 {journey.user.full_name}&apos;s Journey</h3>
                  <button onClick={() => { setJourney(null); setSelectedUser(null); }} className="btn-secondary" style={{ padding: '4px 12px', fontSize: 12 }}>Close</button>
                </div>
                {journey.projects.length === 0 ? <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>No projects yet.</p> : journey.projects.map((p: any) => (
                  <div key={p.id} style={{ padding: '10px 14px', background: 'rgba(255,255,255,0.02)', borderRadius: 8, marginBottom: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: 14, fontWeight: 500 }}>{p.name}</span>
                      <span style={{ fontSize: 13, color: 'var(--accent-cyan)' }}>Avg mastery: {p.average_mastery}%</span>
                    </div>
                    {p.learning_goal && <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>{p.learning_goal}</p>}
                  </div>
                ))}
                <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 12 }}>Recent events: {journey.recent_events.length}</p>
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {filteredUsers.length === 0 ? <p style={{ color: 'var(--text-muted)' }}>No users found.</p> : filteredUsers.map(u => (
                <div key={u.id} className="glass-card" style={{ padding: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span style={{ fontSize: 14, fontWeight: 600 }}>{u.full_name}</span>
                      <span className={`badge ${u.role === 'ADMIN' ? 'badge-rose' : 'badge-cyan'}`}>{u.role}</span>
                    </div>
                    <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                      {u.email} • {u.project_count} projects • {u.quiz_count} quizzes
                      {u.last_activity && ` • Active ${new Date(u.last_activity).toLocaleDateString()}`}
                    </span>
                  </div>
                  {u.role !== 'ADMIN' && (
                    <button onClick={() => viewJourney(u.id)} className="btn-secondary" style={{ padding: '6px 12px', fontSize: 12 }}>View Journey</button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Projects Tab */}
        {tab === 'projects' && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <input 
                type="text" 
                className="input-field" 
                placeholder="Search projects by name or owner email..." 
                value={projectSearch} 
                onChange={e => setProjectSearch(e.target.value)}
                style={{ maxWidth: 350 }}
              />
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {filteredProjects.length === 0 ? <p style={{ color: 'var(--text-muted)' }}>No projects found.</p> : filteredProjects.map(p => (
                <div key={p.id} className="glass-card" style={{ padding: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span style={{ fontSize: 14, fontWeight: 600 }}>{p.name}</span>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)', background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: 4 }}>{p.space_name}</span>
                    </div>
                    <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                      Owned by: <span style={{ color: 'var(--text-primary)' }}>{p.user_email}</span> • {p.material_count} materials • {p.quiz_count} quizzes
                    </span>
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    Created {new Date(p.created_at).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Health Tab */}
        {tab === 'health' && health && (
          <div className="glass-card" style={{ padding: 24 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>System Health</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
              <div style={{ padding: 16, background: 'rgba(255,255,255,0.02)', borderRadius: 8 }}>
                <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Database</span>
                <div style={{ fontSize: 16, fontWeight: 600, color: health.database === 'healthy' ? 'var(--accent-emerald)' : 'var(--accent-rose)', marginTop: 4 }}>
                  {health.database === 'healthy' ? '✅ Healthy' : '❌ Unhealthy'}
                </div>
              </div>
              <div style={{ padding: 16, background: 'rgba(255,255,255,0.02)', borderRadius: 8 }}>
                <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>AI Service</span>
                <div style={{ fontSize: 16, fontWeight: 600, color: health.ai_service === 'configured' ? 'var(--accent-emerald)' : 'var(--accent-amber)', marginTop: 4 }}>
                  {health.ai_service === 'configured' ? '✅ Configured' : '⚠️ Not configured'}
                </div>
              </div>
              <div style={{ padding: 16, background: 'rgba(255,255,255,0.02)', borderRadius: 8 }}>
                <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Jobs Queued</span>
                <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--accent-cyan)', marginTop: 4 }}>{health.background_jobs?.queued || 0}</div>
              </div>
              <div style={{ padding: 16, background: 'rgba(255,255,255,0.02)', borderRadius: 8 }}>
                <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Jobs Failed</span>
                <div style={{ fontSize: 16, fontWeight: 600, color: health.background_jobs?.failed > 0 ? 'var(--accent-rose)' : 'var(--accent-emerald)', marginTop: 4 }}>{health.background_jobs?.failed || 0}</div>
              </div>
            </div>
          </div>
        )}

        {/* AI Logs Tab */}
        {tab === 'ai' && (
          <div>
            <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
              <select className="input-field" value={aiFeature} onChange={e => setAiFeature(e.target.value)} style={{ width: 'auto', padding: '8px 12px' }}>
                <option value="">All Features</option>
                <option value="tutor">Tutor</option>
                <option value="quiz_gen">Quiz Generation</option>
                <option value="concept_extraction">Concept Extraction</option>
                <option value="assessment">Assessment</option>
              </select>
              <select className="input-field" value={aiModel} onChange={e => setAiModel(e.target.value)} style={{ width: 'auto', padding: '8px 12px' }}>
                <option value="">All Models</option>
                <option value="llama3-70b-8192">llama3-70b-8192</option>
                <option value="llama3-8b-8192">llama3-8b-8192</option>
              </select>
              <select className="input-field" value={aiStatus} onChange={e => setAiStatus(e.target.value)} style={{ width: 'auto', padding: '8px 12px' }}>
                <option value="">All Statuses</option>
                <option value="success">Success</option>
                <option value="error">Error</option>
              </select>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {aiLogs.length === 0 ? <p style={{ color: 'var(--text-muted)' }}>No AI logs found</p> : (
                aiLogs.map(log => (
                  <div key={log.id} className="glass-card" style={{ padding: 14, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                      <span className={`badge ${log.status === 'success' ? 'badge-emerald' : 'badge-rose'}`}>{log.status}</span>
                      <span style={{ fontSize: 13, fontWeight: 500 }}>{log.feature}</span>
                      <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{log.model}</span>
                    </div>
                    <div style={{ display: 'flex', gap: 16, fontSize: 12, color: 'var(--text-secondary)' }}>
                      <span>{log.latency_ms}ms</span>
                      <span>{log.input_tokens + log.output_tokens} tokens</span>
                      <span>${log.estimated_cost.toFixed(4)}</span>
                      <span>{new Date(log.created_at).toLocaleTimeString()}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* AI Evaluations Tab */}
        {tab === 'evals' && (
          <div>
            <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
              <select className="input-field" value={evFeature} onChange={e => setEvFeature(e.target.value)} style={{ width: 'auto', padding: '8px 12px' }}>
                <option value="">All Features</option>
                <option value="quiz_gen">Quiz Generation</option>
                <option value="tutor">Tutor</option>
                <option value="recommendation">Recommendations</option>
              </select>
              <select className="input-field" value={evPassed} onChange={e => setEvPassed(e.target.value)} style={{ width: 'auto', padding: '8px 12px' }}>
                <option value="">All Outcomes</option>
                <option value="true">Passed</option>
                <option value="false">Failed</option>
              </select>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {evals.length === 0 ? <p style={{ color: 'var(--text-muted)' }}>No evaluations found</p> : (
                evals.map(ev => (
                  <div key={ev.id} className="glass-card" style={{ padding: 14, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                      <span className={`badge ${ev.passed === true ? 'badge-emerald' : ev.passed === false ? 'badge-rose' : 'badge-amber'}`}>
                        {ev.passed === true ? 'PASS' : ev.passed === false ? 'FAIL' : 'PENDING'}
                      </span>
                      <span style={{ fontSize: 13, fontWeight: 500 }}>{ev.feature}</span>
                      <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{ev.test_case_name}</span>
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                      {ev.score !== null ? `Score: ${ev.score}` : '-'} • {new Date(ev.created_at).toLocaleString()}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Jobs Tab */}
        {tab === 'jobs' && (
          <div>
            <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
              <select className="input-field" value={jobStatus} onChange={e => setJobStatus(e.target.value)} style={{ width: 'auto', padding: '8px 12px' }}>
                <option value="">All Statuses</option>
                <option value="QUEUED">Queued</option>
                <option value="PROCESSING">Processing</option>
                <option value="COMPLETED">Completed</option>
                <option value="FAILED">Failed</option>
              </select>
              <select className="input-field" value={jobType} onChange={e => setJobType(e.target.value)} style={{ width: 'auto', padding: '8px 12px' }}>
                <option value="">All Job Types</option>
                <option value="PROCESS_MATERIAL">Process Material</option>
                <option value="EXTRACT_CONCEPTS">Extract Concepts</option>
                <option value="GENERATE_EMBEDDINGS">Generate Embeddings</option>
                <option value="UPDATE_MASTERY">Update Mastery</option>
              </select>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {jobs.length === 0 ? <p style={{ color: 'var(--text-muted)' }}>No background jobs found</p> : (
                jobs.map(job => (
                  <div key={job.id} className="glass-card" style={{ padding: 14, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span className={`badge ${job.status === 'COMPLETED' ? 'badge-emerald' : job.status === 'FAILED' ? 'badge-rose' : job.status === 'PROCESSING' ? 'badge-amber' : 'badge-cyan'}`}>{job.status}</span>
                      <span style={{ fontSize: 13, marginLeft: 10 }}>{job.job_type}</span>
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                      Retries: {job.retry_count} • {new Date(job.created_at).toLocaleString()}
                      {job.error_message && <span style={{ color: 'var(--accent-rose)', marginLeft: 8 }}>{job.error_message.substring(0, 50)}</span>}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
