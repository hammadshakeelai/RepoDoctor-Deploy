import { useState, useRef } from 'react'
import './index.css'

const AGENTS = [
  { id: 'cloner', name: 'Clone', icon: '📥', color: '#64748b' },
  { id: 'mapper', name: 'Mapper', icon: '🗺️', color: '#0ea5e9' },
  { id: 'storyteller', name: 'Storyteller', icon: '📖', color: '#f59e0b' },
  { id: 'hacker', name: 'Hacker', icon: '🔓', color: '#ef4444' },
  { id: 'sre', name: 'SRE', icon: '⚙️', color: '#10b981' },
  { id: 'fixer', name: 'Fixer', icon: '🔧', color: '#8b5cf6' },
  { id: 'quizzer', name: 'Quizzer', icon: '🎓', color: '#ec4899' },
]

const TABS = [
  { id: 'mapper', label: 'Architecture', icon: '🗺️' },
  { id: 'storyteller', label: 'Narrative', icon: '📖' },
  { id: 'hacker', label: 'Security', icon: '🔓' },
  { id: 'sre', label: 'Reliability', icon: '⚙️' },
  { id: 'fixer', label: 'Fixes', icon: '🔧' },
  { id: 'quizzer', label: 'Quiz', icon: '🎓' },
]

export default function App() {
  const [url, setUrl] = useState('')
  const [status, setStatus] = useState('idle') // idle | running | done | error
  const [agentStates, setAgentStates] = useState({})
  const [results, setResults] = useState({})
  const [activeTab, setActiveTab] = useState('mapper')
  const [error, setError] = useState(null)
  const abortRef = useRef(null)

  const startAnalysis = async () => {
    if (!url.trim()) return
    setStatus('running')
    setError(null)
    setResults({})
    setAgentStates({})

    try {
      const API_BASE = import.meta.env.VITE_API_BASE ?? ''
      const response = await fetch(`${API_BASE}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ github_url: url.trim() }),
      })

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('event:')) {
            var currentEvent = line.slice(6).trim()
          }
          if (line.startsWith('data:')) {
            const dataStr = line.slice(5).trim()
            if (!dataStr) continue
            try {
              const data = JSON.parse(dataStr)
              handleSSEEvent(currentEvent, data)
            } catch (e) {
              console.warn('SSE parse error:', e)
            }
          }
        }
      }
    } catch (err) {
      setError(err.message)
      setStatus('error')
    }
  }

  const handleSSEEvent = (event, data) => {
    switch (event) {
      case 'agent_start':
        setAgentStates(prev => ({ ...prev, [data.agent]: 'running' }))
        break
      case 'agent_complete':
        setAgentStates(prev => ({ ...prev, [data.agent]: 'complete' }))
        if (data.data) {
          setResults(prev => ({ ...prev, [data.agent]: data.data }))
          if (!['cloner'].includes(data.agent)) {
            setActiveTab(data.agent)
          }
        }
        break
      case 'analysis_done':
        setStatus('done')
        break
      case 'error':
        setError(data.error)
        setStatus('error')
        break
    }
  }

  const hasResults = Object.keys(results).length > 0

  return (
    <>
      <div className="bg-glow" />
      <div className="app-container">
        {/* Hero */}
        <header className="hero animate-in">
          <div className="hero-badge">🩺 Multi-Agent System</div>
          <h1><span className="gradient-text">RepoDoctor</span> AI</h1>
          <p>Paste a GitHub repo. 6 AI agents dissect it — architecture, security, reliability, fixes, and onboarding — in real time.</p>
          <div className="input-group">
            <div className="input-wrapper">
              <span className="input-icon">🔗</span>
              <input
                id="repo-url-input"
                type="text"
                placeholder="https://github.com/user/repo"
                value={url}
                onChange={e => setUrl(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && startAnalysis()}
                disabled={status === 'running'}
              />
            </div>
            <button
              id="analyze-btn"
              className="btn-primary"
              onClick={startAnalysis}
              disabled={status === 'running' || !url.trim()}
            >
              {status === 'running' ? '⏳ Analyzing...' : '🚀 Analyze'}
            </button>
          </div>
        </header>

        {/* Pipeline */}
        {status !== 'idle' && (
          <section className="pipeline-section animate-in">
            <div className="pipeline-header">
              <h2>🔬 Agent Pipeline</h2>
              {status === 'running' && <div className="node-spinner" />}
              {status === 'done' && <span style={{color:'var(--accent-green)'}}>✓ Complete</span>}
            </div>
            <div className="pipeline-grid">
              {AGENTS.map(agent => {
                const state = agentStates[agent.id] || 'pending'
                return (
                  <div key={agent.id} className={`pipeline-node ${state}`}>
                    <div className="node-icon" style={{background: `${agent.color}20`}}>
                      {agent.icon}
                    </div>
                    <div className="node-label">{agent.name}</div>
                    {state === 'running' && <div className="node-spinner" />}
                    {state === 'complete' && <div className="node-status" style={{color:'var(--accent-green)'}}>✓ Done</div>}
                    {state === 'pending' && <div className="node-status">Waiting</div>}
                  </div>
                )
              })}
            </div>
          </section>
        )}

        {/* Error */}
        {error && (
          <div className="result-card animate-in" style={{borderColor:'var(--accent-red)'}}>
            <h3>❌ Error</h3>
            <p style={{color:'var(--accent-red)'}}>{error}</p>
          </div>
        )}

        {/* Results */}
        {hasResults && (
          <section className="results-section animate-in">
            <div className="tabs">
              {TABS.map(tab => (
                <button
                  key={tab.id}
                  className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.id)}
                  disabled={!results[tab.id]}
                >
                  <span>{tab.icon}</span>
                  <span>{tab.label}</span>
                </button>
              ))}
            </div>
            <div className="tab-content">
              {activeTab === 'mapper' && results.mapper && <MapperView data={results.mapper} />}
              {activeTab === 'storyteller' && results.storyteller && <StorytellerView data={results.storyteller} />}
              {activeTab === 'hacker' && results.hacker && <HackerView data={results.hacker} />}
              {activeTab === 'sre' && results.sre && <SREView data={results.sre} />}
              {activeTab === 'fixer' && results.fixer && <FixerView data={results.fixer} />}
              {activeTab === 'quizzer' && results.quizzer && <QuizzerView data={results.quizzer} />}
            </div>
          </section>
        )}

        {/* Empty state */}
        {status === 'idle' && (
          <div className="empty-state animate-in">
            <div className="empty-icon">🩺</div>
            <h3>Ready to diagnose</h3>
            <p>Paste a GitHub URL above and let 6 AI agents analyze it.</p>
          </div>
        )}
      </div>
    </>
  )
}

/* ====== MAPPER VIEW ====== */
function MapperView({ data }) {
  if (typeof data === 'string') return <div className="result-card"><pre style={{whiteSpace:'pre-wrap',color:'var(--text-secondary)'}}>{data}</pre></div>
  return (
    <div className="result-card">
      <h3>🗺️ Architecture Map</h3>
      {data.project_name && <h3 style={{fontSize:'1.3rem',marginBottom:4}}>{data.project_name}</h3>}
      {data.description && <p style={{color:'var(--text-secondary)',marginBottom:16}}>{data.description}</p>}
      {data.tech_stack && (
        <div className="tech-badges">
          {data.tech_stack.map((t,i) => <span key={i} className="tech-badge">{t}</span>)}
        </div>
      )}
      <div className="info-grid">
        {data.architecture_pattern && (
          <div className="info-item">
            <div className="info-label">Architecture</div>
            <div className="info-value">{data.architecture_pattern}</div>
          </div>
        )}
        {data.languages && Object.entries(data.languages).slice(0,4).map(([lang, lines]) => (
          <div className="info-item" key={lang}>
            <div className="info-label">{lang}</div>
            <div className="info-value">{Number(lines).toLocaleString()} lines</div>
          </div>
        ))}
      </div>
      {data.entry_points && data.entry_points.length > 0 && (
        <div style={{marginTop:16}}>
          <div className="info-label" style={{marginBottom:8}}>Entry Points</div>
          {data.entry_points.map((ep,i) => (
            <div key={i} style={{display:'flex',gap:8,marginBottom:4,fontSize:'0.88rem'}}>
              <code style={{color:'var(--accent-blue)'}}>{ep.file}</code>
              <span style={{color:'var(--text-muted)'}}>— {ep.description}</span>
            </div>
          ))}
        </div>
      )}
      {data.file_tree_summary && (
        <div style={{marginTop:16}}>
          <div className="info-label" style={{marginBottom:8}}>Structure Summary</div>
          <p style={{color:'var(--text-secondary)',fontSize:'0.9rem'}}>{data.file_tree_summary}</p>
        </div>
      )}
    </div>
  )
}

/* ====== STORYTELLER VIEW ====== */
function StorytellerView({ data }) {
  const html = simpleMarkdown(typeof data === 'string' ? data : JSON.stringify(data, null, 2))
  return (
    <div className="result-card">
      <h3>📖 How This Codebase Thinks</h3>
      <div className="narrative-content" dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  )
}

/* ====== HACKER VIEW ====== */
function HackerView({ data }) {
  if (typeof data === 'string') return <div className="result-card"><pre style={{whiteSpace:'pre-wrap',color:'var(--text-secondary)'}}>{data}</pre></div>
  const riskClass = (data.risk_score || 0) >= 7 ? 'risk-high' : (data.risk_score || 0) >= 4 ? 'risk-medium' : 'risk-low'
  return (
    <div className="result-card">
      <h3>🔓 Security Audit</h3>
      <div className="risk-header">
        <div className={`risk-score-circle ${riskClass}`}>
          {data.risk_score ?? '?'}
        </div>
        <div>
          <div style={{fontWeight:700,marginBottom:4}}>Risk Score: {data.risk_score ?? 'N/A'} / 10</div>
          <div className="severity-badges">
            {data.critical > 0 && <span className="severity-badge severity-critical">{data.critical} Critical</span>}
            {data.high > 0 && <span className="severity-badge severity-high">{data.high} High</span>}
            {data.medium > 0 && <span className="severity-badge severity-medium">{data.medium} Medium</span>}
            {data.low > 0 && <span className="severity-badge severity-low">{data.low} Low</span>}
            {data.total_findings === 0 && <span className="severity-badge severity-low">No issues found 🎉</span>}
          </div>
        </div>
      </div>
      {data.findings && data.findings.map((f, i) => (
        <div key={i} className={`finding-card ${f.severity}`}>
          <div className="finding-title">
            <span className={`severity-badge severity-${f.severity}`}>{f.severity?.toUpperCase()}</span>
            {f.title}
          </div>
          <div className="finding-meta">{f.file} {f.line_range ? `(L${f.line_range})` : ''} {f.cwe_id ? `• ${f.cwe_id}` : ''}</div>
          <div className="finding-desc">{f.description}</div>
          {f.evidence && <div style={{fontFamily:'var(--font-mono)',fontSize:'0.8rem',color:'var(--accent-red)',margin:'6px 0',background:'rgba(0,0,0,0.3)',padding:8,borderRadius:6}}>{f.evidence}</div>}
          {f.recommendation && <div className="finding-rec">💡 {f.recommendation}</div>}
        </div>
      ))}
    </div>
  )
}

/* ====== SRE VIEW ====== */
function SREView({ data }) {
  if (typeof data === 'string') return <div className="result-card"><pre style={{whiteSpace:'pre-wrap',color:'var(--text-secondary)'}}>{data}</pre></div>
  const score = data.reliability_score ?? 0
  const scoreColor = score >= 7 ? 'var(--accent-green)' : score >= 4 ? 'var(--accent-orange)' : 'var(--accent-red)'
  return (
    <div className="result-card">
      <h3>⚙️ Reliability Report</h3>
      <div className="score-gauge" style={{borderColor: scoreColor, color: scoreColor}}>
        <div className="score-value">{score}</div>
        <div className="score-label">/ 10</div>
      </div>
      {renderSRESection('🔥 Bottlenecks', data.bottlenecks)}
      {renderSRESection('💥 Failure Points', data.failure_points)}
      {renderSRESection('📈 Scaling Issues', data.scaling_issues)}
      {data.positive_patterns && data.positive_patterns.length > 0 && (
        <div className="sre-section">
          <h4>✅ Positive Patterns</h4>
          {data.positive_patterns.map((p, i) => <div key={i} className="positive-tag">{p}</div>)}
        </div>
      )}
    </div>
  )
}

function renderSRESection(title, items) {
  if (!items || items.length === 0) return null
  return (
    <div className="sre-section">
      <h4>{title}</h4>
      {items.map((item, i) => (
        <div key={i} className={`finding-card ${item.severity || 'medium'}`}>
          <div className="finding-title">
            <span className={`severity-badge severity-${item.severity || 'medium'}`}>{(item.severity || 'medium').toUpperCase()}</span>
            {item.component}
          </div>
          <div className="finding-desc">{item.description}</div>
          {item.impact && <div style={{fontSize:'0.85rem',color:'var(--accent-orange)',margin:'6px 0'}}>⚠️ Impact: {item.impact}</div>}
          {item.recommendation && <div className="finding-rec">💡 {item.recommendation}</div>}
        </div>
      ))}
    </div>
  )
}

/* ====== FIXER VIEW ====== */
function FixerView({ data }) {
  if (typeof data === 'string') return <div className="result-card"><pre style={{whiteSpace:'pre-wrap',color:'var(--text-secondary)'}}>{data}</pre></div>
  return (
    <div className="result-card">
      <h3>🔧 Proposed Fixes ({data.total_fixes ?? data.fixes?.length ?? 0})</h3>
      {data.fixes && data.fixes.map((fix, i) => (
        <div key={i} className="fix-card">
          <div className="fix-header">
            <span className={`severity-badge severity-${fix.severity || 'medium'}`}>{(fix.severity || 'medium').toUpperCase()}</span>
            <span className="fix-title">{fix.title}</span>
          </div>
          {fix.file && <div className="finding-meta">{fix.file}</div>}
          <p style={{color:'var(--text-secondary)',fontSize:'0.9rem',marginBottom:8}}>{fix.description}</p>
          {fix.original_code && (
            <div className="code-diff">
              <div className="code-label code-label-red">— Original</div>
              <pre className="code-block code-original">{fix.original_code}</pre>
            </div>
          )}
          {fix.fixed_code && (
            <div className="code-diff">
              <div className="code-label code-label-green">+ Fixed</div>
              <pre className="code-block code-fixed">{fix.fixed_code}</pre>
            </div>
          )}
          {fix.explanation && <div className="finding-rec">💡 {fix.explanation}</div>}
        </div>
      ))}
      {data.architectural_recommendations && data.architectural_recommendations.length > 0 && (
        <>
          <h4 style={{marginTop:20,marginBottom:10}}>🏗️ Architectural Recommendations</h4>
          {data.architectural_recommendations.map((rec, i) => (
            <div key={i} className="fix-card">
              <div className="fix-title">{rec.title}</div>
              <p style={{color:'var(--text-secondary)',fontSize:'0.9rem',marginTop:6}}>{rec.description}</p>
              {rec.implementation_hint && <div className="finding-rec" style={{marginTop:8}}>💡 {rec.implementation_hint}</div>}
            </div>
          ))}
        </>
      )}
    </div>
  )
}

/* ====== QUIZZER VIEW ====== */
function QuizzerView({ data }) {
  const [answers, setAnswers] = useState({})
  const [revealed, setRevealed] = useState({})

  if (typeof data === 'string') return <div className="result-card"><pre style={{whiteSpace:'pre-wrap',color:'var(--text-secondary)'}}>{data}</pre></div>

  const questions = data.questions || []

  const handleSelect = (qId, key) => {
    if (revealed[qId]) return
    setAnswers(prev => ({ ...prev, [qId]: key }))
    setRevealed(prev => ({ ...prev, [qId]: true }))
  }

  const correctCount = questions.filter(q => answers[q.id] === q.correct_answer).length

  return (
    <div className="result-card">
      <h3>🎓 {data.quiz_title || 'Onboarding Quiz'}</h3>
      {Object.keys(revealed).length === questions.length && questions.length > 0 && (
        <div style={{padding:12,background:'rgba(124,58,237,0.1)',borderRadius:8,marginBottom:16,fontWeight:600,textAlign:'center'}}>
          Score: {correctCount} / {questions.length} ({Math.round(correctCount/questions.length*100)}%)
        </div>
      )}
      {questions.map(q => (
        <div key={q.id} className="quiz-card">
          <div className="quiz-question">
            <span className="quiz-number">{q.id}</span>
            <span>{q.question}</span>
          </div>
          <div className="quiz-options">
            {(q.options || []).map(opt => {
              const isSelected = answers[q.id] === opt.key
              const isRevealed = revealed[q.id]
              const isCorrect = opt.key === q.correct_answer
              let cls = 'quiz-option'
              if (isRevealed && isCorrect) cls += ' correct'
              else if (isRevealed && isSelected && !isCorrect) cls += ' incorrect'
              else if (isSelected) cls += ' selected'
              return (
                <div key={opt.key} className={cls} onClick={() => handleSelect(q.id, opt.key)}>
                  <span className="option-key">{opt.key}</span>
                  <span>{opt.text}</span>
                  {isRevealed && isCorrect && <span style={{marginLeft:'auto'}}>✓</span>}
                  {isRevealed && isSelected && !isCorrect && <span style={{marginLeft:'auto'}}>✗</span>}
                </div>
              )
            })}
          </div>
          {revealed[q.id] && q.explanation && (
            <div className="quiz-explanation">
              💡 {q.explanation}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

/* ====== SIMPLE MARKDOWN RENDERER ====== */
function simpleMarkdown(text) {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h3 style="font-size:1.2rem">$1</h3>')
    .replace(/^# (.+)$/gm, '<h3 style="font-size:1.4rem">$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br/>')
}
