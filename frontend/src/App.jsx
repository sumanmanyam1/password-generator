import { useEffect, useMemo, useState } from 'react'
import { api } from './api'
import './App.css'

const STRENGTH_COLORS = {
  red: '#ff4d6d',
  orange: '#ff9f43',
  yellow: '#ffd43b',
  lightgreen: '#7bed9f',
  green: '#2ed573',
}

function strengthHue(color) {
  return STRENGTH_COLORS[color] || '#8b8ea3'
}

/* ───────────────────────── Shared bits ───────────────────────── */

function Toast({ toast }) {
  if (!toast) return null
  return <div className={`toast toast--${toast.type}`}>{toast.msg}</div>
}

function StrengthMeter({ score, level, color }) {
  const hue = strengthHue(color)
  return (
    <div className="meter">
      <div className="meter__head">
        <span className="meter__level" style={{ color: hue }}>
          {level}
        </span>
        <span className="meter__score">{score}/100</span>
      </div>
      <div className="meter__track">
        <div
          className="meter__fill"
          style={{ width: `${score}%`, background: hue }}
        />
      </div>
    </div>
  )
}

function CopyButton({ value, onCopied }) {
  return (
    <button
      className="icon-btn"
      title="Copy"
      onClick={() => {
        navigator.clipboard.writeText(value)
        onCopied?.()
      }}
    >
      ⧉
    </button>
  )
}

/* ───────────────────────── Options panel ───────────────────────── */

function OptionsPanel({ opts, setOpts }) {
  const toggle = (key) => setOpts((o) => ({ ...o, [key]: !o[key] }))
  return (
    <div className="options">
      <div className="slider-row">
        <label>Length</label>
        <input
          type="range"
          min="4"
          max="64"
          value={opts.length}
          onChange={(e) => setOpts((o) => ({ ...o, length: +e.target.value }))}
        />
        <span className="slider-val">{opts.length}</span>
      </div>
      <div className="chips">
        <button
          className={`chip ${!opts.no_upper ? 'chip--on' : ''}`}
          onClick={() => toggle('no_upper')}
        >
          A-Z Uppercase
        </button>
        <button
          className={`chip ${!opts.no_digits ? 'chip--on' : ''}`}
          onClick={() => toggle('no_digits')}
        >
          0-9 Digits
        </button>
        <button
          className={`chip ${!opts.no_symbols ? 'chip--on' : ''}`}
          onClick={() => toggle('no_symbols')}
        >
          !@# Symbols
        </button>
      </div>
    </div>
  )
}

/* ───────────────────────── Generate tab ───────────────────────── */

function GenerateTab({ notify, onSaved }) {
  const [opts, setOpts] = useState({
    length: 16,
    no_upper: false,
    no_digits: false,
    no_symbols: false,
  })
  const [result, setResult] = useState(null)
  const [label, setLabel] = useState('')
  const [busy, setBusy] = useState(false)

  const run = async (save) => {
    setBusy(true)
    try {
      const body = { ...opts }
      if (save) {
        if (!label.trim()) {
          notify('Enter a label to save.', 'error')
          setBusy(false)
          return
        }
        body.save = true
        body.label = label.trim()
      }
      const data = await api.generate(body)
      setResult(data)
      if (data.saved) {
        notify(
          data.overwritten
            ? `Updated "${data.label}"`
            : `Saved as "${data.label}"`,
          'success',
        )
        onSaved?.()
      }
    } catch (e) {
      notify(e.message, 'error')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="panel">
      <OptionsPanel opts={opts} setOpts={setOpts} />

      {result && (
        <div className="pw-display">
          <code className="pw-text">{result.password}</code>
          <CopyButton
            value={result.password}
            onCopied={() => notify('Copied to clipboard', 'success')}
          />
        </div>
      )}

      {result && (
        <StrengthMeter
          score={result.strength.score}
          level={result.strength.level}
          color={result.strength.color}
        />
      )}

      <div className="save-row">
        <input
          className="text-input"
          placeholder="Label (e.g. github) — optional"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
        />
        <button className="btn btn--ghost" disabled={busy} onClick={() => run(true)}>
          Save
        </button>
      </div>

      <button className="btn btn--primary btn--big" disabled={busy} onClick={() => run(false)}>
        {busy ? 'Working…' : '⚡ Generate Password'}
      </button>

      {result?.strength?.crack_time && (
        <p className="hint">
          Estimated crack time: <strong>{result.strength.crack_time}</strong>
        </p>
      )}
    </div>
  )
}

/* ───────────────────────── Analyze tab ───────────────────────── */

function AnalyzeTab({ notify }) {
  const [pw, setPw] = useState('')
  const [res, setRes] = useState(null)
  const [busy, setBusy] = useState(false)

  const run = async () => {
    if (!pw) {
      notify('Type a password to analyze.', 'error')
      return
    }
    setBusy(true)
    try {
      setRes(await api.analyze({ password: pw }))
    } catch (e) {
      notify(e.message, 'error')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="panel">
      <input
        className="text-input text-input--mono"
        placeholder="Type or paste a password…"
        value={pw}
        onChange={(e) => setPw(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && run()}
      />
      <button className="btn btn--primary" disabled={busy} onClick={run}>
        {busy ? 'Analyzing…' : '🔍 Analyze Strength'}
      </button>

      {res && (
        <>
          <StrengthMeter score={res.score} level={res.level} color={res.color} />
          <p className="hint">
            Length <strong>{res.length}</strong> · Crack time{' '}
            <strong>{res.crack_time}</strong>
          </p>
          <ul className="feedback">
            {res.feedback.map((f, i) => (
              <li key={i} className={f.startsWith('✓') ? 'ok' : f.startsWith('✗') ? 'bad' : 'warn'}>
                {f}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}

/* ───────────────────────── Vault tab ───────────────────────── */

function VaultTab({ notify, refreshKey }) {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [revealed, setRevealed] = useState({})

  const load = async () => {
    setLoading(true)
    try {
      const data = await api.list()
      setEntries(data.entries)
    } catch (e) {
      notify(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [refreshKey])

  const reveal = async (label) => {
    if (revealed[label]) {
      setRevealed((r) => ({ ...r, [label]: undefined }))
      return
    }
    try {
      const { password } = await api.reveal(label)
      setRevealed((r) => ({ ...r, [label]: password }))
    } catch (e) {
      notify(e.message, 'error')
    }
  }

  const remove = async (label) => {
    if (!confirm(`Delete "${label}"? This cannot be undone.`)) return
    try {
      await api.remove(label)
      notify(`Deleted "${label}"`, 'success')
      load()
    } catch (e) {
      notify(e.message, 'error')
    }
  }

  if (loading) return <div className="panel"><p className="hint">Loading vault…</p></div>

  return (
    <div className="panel">
      {entries.length === 0 ? (
        <p className="empty">🗝️ No saved passwords yet. Generate one and hit Save.</p>
      ) : (
        <div className="vault">
          {entries.map((e) => (
            <div className="vault-row" key={e.label}>
              <div className="vault-main">
                <span className="vault-label">{e.label}</span>
                <span className="vault-meta">
                  {e.length} chars · {e.created_at}
                </span>
                {revealed[e.label] && (
                  <code className="vault-pw">{revealed[e.label]}</code>
                )}
              </div>
              <div className="vault-actions">
                {revealed[e.label] && (
                  <CopyButton
                    value={revealed[e.label]}
                    onCopied={() => notify('Copied', 'success')}
                  />
                )}
                <button className="icon-btn" title="Reveal" onClick={() => reveal(e.label)}>
                  {revealed[e.label] ? '🙈' : '👁'}
                </button>
                <button className="icon-btn icon-btn--danger" title="Delete" onClick={() => remove(e.label)}>
                  🗑
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

/* ───────────────────────── App shell ───────────────────────── */

export default function App() {
  const [tab, setTab] = useState('generate')
  const [toast, setToast] = useState(null)
  const [online, setOnline] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)

  const notify = (msg, type = 'info') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 2600)
  }

  useEffect(() => {
    api.health().then(() => setOnline(true)).catch(() => setOnline(false))
  }, [])

  const tabs = useMemo(
    () => [
      { id: 'generate', label: 'Generate' },
      { id: 'analyze', label: 'Analyze' },
      { id: 'vault', label: 'Vault' },
    ],
    [],
  )

  return (
    <div className="app">
      <div className="bg-orb bg-orb--1" />
      <div className="bg-orb bg-orb--2" />

      <header className="header">
        <div className="brand">
          <span className="brand__mark">🔐</span>
          <h1>PassGen</h1>
        </div>
        <p className="tagline">Generate, analyze &amp; store strong passwords — locally.</p>
        <span className={`status ${online ? 'status--on' : online === false ? 'status--off' : ''}`}>
          {online === null ? 'Connecting…' : online ? 'API connected' : 'API offline'}
        </span>
      </header>

      <main className="card">
        <nav className="tabs">
          {tabs.map((t) => (
            <button
              key={t.id}
              className={`tab ${tab === t.id ? 'tab--active' : ''}`}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>

        {tab === 'generate' && (
          <GenerateTab notify={notify} onSaved={() => setRefreshKey((k) => k + 1)} />
        )}
        {tab === 'analyze' && <AnalyzeTab notify={notify} />}
        {tab === 'vault' && <VaultTab notify={notify} refreshKey={refreshKey} />}
      </main>

      <footer className="footer">
        Powered by your Python engine · runs entirely on your machine
      </footer>

      <Toast toast={toast} />
    </div>
  )
}
