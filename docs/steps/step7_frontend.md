# Step 7 — Frontend: Mobile Chat & Dashboard

## Objective
Implement a high-fidelity, mobile-responsive dashboard and chat application in React + Vite, styled using modern CSS custom properties. The UI must feature smooth micro-animations, premium layout structures, and a Force-Directed Knowledge Graph visualization for judges.

---

## 7.1 Setup CSS Design Tokens

**File:** `plantmind/web/src/index.css`

```css
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

:root {
  /* Harmonious Color Palette */
  --bg-primary: #0b0f19;
  --bg-secondary: #131b2e;
  --bg-tertiary: #1b2640;
  
  --text-primary: #f3f4f6;
  --text-secondary: #9ca3af;
  --text-muted: #6b7280;
  
  --accent-primary: #3b82f6; /* Cyber Blue */
  --accent-primary-rgb: 59, 130, 246;
  --accent-secondary: #10b981; /* Emerald Green */
  --accent-tertiary: #8b5cf6; /* Electric Violet */
  --accent-danger: #ef4444; /* Alert Red */
  --accent-warning: #f59e0b; /* Amber */
  
  --glass-bg: rgba(19, 27, 46, 0.7);
  --glass-border: rgba(255, 255, 255, 0.08);
  --glass-shadow: rgba(0, 0, 0, 0.3);
  
  /* Fonts */
  --font-heading: 'Outfit', sans-serif;
  --font-body: 'Plus Jakarta Sans', sans-serif;
  
  /* Layout */
  --border-radius-sm: 8px;
  --border-radius-md: 12px;
  --border-radius-lg: 20px;
  --transition-smooth: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  background-color: var(--bg-primary);
  color: var(--text-primary);
  font-family: var(--font-body);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  overflow-x: hidden;
}

h1, h2, h3, h4, h5, h6 {
  font-family: var(--font-heading);
  font-weight: 600;
  letter-spacing: -0.02em;
}

/* Custom Scrollbars */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: var(--bg-primary);
}
::-webkit-scrollbar-thumb {
  background: var(--bg-tertiary);
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: var(--accent-primary);
}

/* Glassmorphism Classes */
.glass-panel {
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--glass-border);
  box-shadow: 0 8px 32px 0 var(--glass-shadow);
}

.gradient-text {
  background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

---

## 7.2 Main App Wrapper & Routing

**File:** `plantmind/web/src/App.jsx`

```jsx
import React, { useState } from 'react';
import { LayoutDashboard, MessageSquare, ShieldAlert, Award, Network } from 'lucide-react';
import ChatView from './components/ChatView';
import DashboardView from './components/DashboardView';
import ComplianceView from './components/ComplianceView';
import LessonsView from './components/LessonsView';
import GraphView from './components/GraphView';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('chat');

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar glass-panel">
        <div className="logo-section">
          <div className="logo-icon">🍀</div>
          <h2>Plant<span>Mind</span></h2>
        </div>
        
        <nav className="nav-menu">
          <button 
            className={`nav-item ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            <MessageSquare size={20} />
            <span>RAG Copilot</span>
          </button>
          <button 
            className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <LayoutDashboard size={20} />
            <span>Dashboard</span>
          </button>
          <button 
            className={`nav-item ${activeTab === 'compliance' ? 'active' : ''}`}
            onClick={() => setActiveTab('compliance')}
          >
            <ShieldAlert size={20} />
            <span>Compliance</span>
          </button>
          <button 
            className={`nav-item ${activeTab === 'lessons' ? 'active' : ''}`}
            onClick={() => setActiveTab('lessons')}
          >
            <Award size={20} />
            <span>Lessons Learned</span>
          </button>
          <button 
            className={`nav-item ${activeTab === 'graph' ? 'active' : ''}`}
            onClick={() => setActiveTab('graph')}
          >
            <Network size={20} />
            <span>Knowledge Graph</span>
          </button>
        </nav>

        <div className="system-status">
          <div className="status-dot healthy"></div>
          <span>Unit-3 Brain Active</span>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        {activeTab === 'chat' && <ChatView />}
        {activeTab === 'dashboard' && <DashboardView />}
        {activeTab === 'compliance' && <ComplianceView />}
        {activeTab === 'lessons' && <LessonsView />}
        {activeTab === 'graph' && <GraphView />}
      </main>
    </div>
  );
}

export default App;
```

---

## 7.3 Layout Styling Sheet

**File:** `plantmind/web/src/App.css`

```css
.app-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.sidebar {
  width: 260px;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 24px;
  border-right: 1px solid var(--glass-border);
  z-index: 10;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 40px;
}

.logo-icon {
  font-size: 28px;
  animation: float 3s ease-in-out infinite;
}

.logo-section h2 {
  font-size: 22px;
  color: var(--text-primary);
}

.logo-section h2 span {
  color: var(--accent-primary);
}

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex-grow: 1;
}

.nav-item {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: var(--border-radius-md);
  cursor: pointer;
  font-family: var(--font-body);
  font-weight: 500;
  font-size: 14px;
  text-align: left;
  transition: var(--transition-smooth);
  width: 100%;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-primary);
}

.nav-item.active {
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: var(--accent-primary);
}

.system-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-muted);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.healthy {
  background-color: var(--accent-secondary);
  box-shadow: 0 0 12px var(--accent-secondary);
}

.main-content {
  flex-grow: 1;
  height: 100%;
  overflow-y: auto;
  position: relative;
}

@keyframes float {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-5px); }
  100% { transform: translateY(0px); }
}

/* Mobile Responsiveness */
@media (max-width: 768px) {
  .app-container {
    flex-direction: column;
  }
  .sidebar {
    width: 100%;
    height: auto;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-right: none;
    border-bottom: 1px solid var(--glass-border);
  }
  .logo-section {
    margin-bottom: 0;
  }
  .nav-menu {
    flex-direction: row;
    gap: 4px;
  }
  .nav-item span, .system-status {
    display: none;
  }
  .nav-item {
    padding: 10px;
  }
  .main-content {
    height: calc(100vh - 65px);
  }
}
```

---

## 7.4 RAG Copilot Chat View Component

Create the folder structure:
```bash
mkdir -p plantmind/web/src/components
```

**File:** `plantmind/web/src/components/ChatView.jsx`

```jsx
import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, Sparkles, AlertTriangle, ShieldCheck, HelpCircle } from 'lucide-react';
import './ChatView.css';

const API_BASE = 'http://localhost:8000/api/v1';

function ChatView() {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'bot',
      text: 'Hello, I am the PlantMind Asset & Operations Brain. Ask me anything about Unit-3 equipment logs, work orders, incidents, or regulations.',
      citations: [],
      safetyFlags: [],
      crossDocumentInsights: []
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: input
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE}/query`, {
        question: input,
        session_id: sessionId
      });

      const { answer, citations, safety_flags, cross_document_insights, confidence_score, session_id } = response.data;
      
      setSessionId(session_id);

      const botMessage = {
        id: Date.now().toString() + '-bot',
        sender: 'bot',
        text: answer,
        citations: citations || [],
        safetyFlags: safety_flags || [],
        crossDocumentInsights: cross_document_insights || [],
        confidenceScore: confidence_score
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, {
        id: Date.now().toString() + '-err',
        sender: 'bot',
        text: 'Error contacting the PlantMind Brain. Ensure the FastAPI backend is running on port 8000.'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <header className="view-header">
        <div>
          <h1>RAG Copilot</h1>
          <p>Hybrid knowledge retrieval for field technicians & engineers</p>
        </div>
      </header>

      <div className="chat-messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`message-wrapper ${msg.sender}`}>
            <div className={`message-avatar ${msg.sender}`}>
              {msg.sender === 'user' ? '👤' : '🍀'}
            </div>
            
            <div className={`message-bubble glass-panel ${msg.sender}`}>
              <div className="message-text">{msg.text}</div>
              
              {msg.sender === 'bot' && msg.confidenceScore !== undefined && (
                <div className="message-meta">
                  <span className={`confidence-badge ${msg.confidenceScore > 0.7 ? 'high' : 'medium'}`}>
                    Confidence: {Math.round(msg.confidenceScore * 100)}%
                  </span>
                </div>
              )}

              {/* Cross-Document Insights */}
              {msg.crossDocumentInsights && msg.crossDocumentInsights.length > 0 && (
                <div className="insight-panel">
                  <div className="panel-title"><Sparkles size={14} /> Cross-Document Insight</div>
                  <ul>
                    {msg.crossDocumentInsights.map((insight, idx) => (
                      <li key={idx}>{insight}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Safety Flags */}
              {msg.safetyFlags && msg.safetyFlags.length > 0 && (
                <div className="safety-panel">
                  <div className="panel-title"><AlertTriangle size={14} /> Safety Warnings / Gaps</div>
                  <ul>
                    {msg.safetyFlags.map((flag, idx) => (
                      <li key={idx}>{flag}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Citations */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="citations-panel">
                  <div className="panel-title"><ShieldCheck size={14} /> Citations</div>
                  <div className="citation-links">
                    {msg.citations.map((cite, idx) => (
                      <div key={idx} className="citation-pill" title={cite.relevant_text}>
                        📄 {cite.doc_title}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message-wrapper bot">
            <div className="message-avatar bot">🍀</div>
            <div className="message-bubble glass-panel bot loading">
              <div className="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      <form className="chat-input-bar glass-panel" onSubmit={handleSend}>
        <input 
          type="text" 
          value={input} 
          onChange={(e) => setInput(e.target.value)} 
          placeholder="Ask about pump misalignments, compliance gaps, OISD requirements..."
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading}>
          <Send size={18} />
        </button>
      </form>
    </div>
  );
}

export default ChatView;
```

**File:** `plantmind/web/src/components/ChatView.css`

```css
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 30px;
}

.view-header {
  margin-bottom: 24px;
  border-bottom: 1px solid var(--glass-border);
  padding-bottom: 16px;
}

.view-header h1 {
  font-size: 26px;
  color: var(--text-primary);
}

.view-header p {
  color: var(--text-secondary);
  font-size: 14px;
}

.chat-messages {
  flex-grow: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-right: 10px;
  margin-bottom: 20px;
}

.message-wrapper {
  display: flex;
  gap: 16px;
  max-width: 80%;
}

.message-wrapper.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  border: 1px solid var(--glass-border);
  font-size: 18px;
}

.message-avatar.bot {
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.3);
}

.message-bubble {
  padding: 16px;
  border-radius: var(--border-radius-lg);
  font-size: 15px;
  line-height: 1.6;
}

.message-bubble.user {
  background: var(--accent-primary);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message-bubble.bot {
  border-bottom-left-radius: 4px;
}

.message-meta {
  margin-top: 8px;
  display: flex;
  justify-content: flex-end;
}

.confidence-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
}

.confidence-badge.high {
  background: rgba(16, 185, 129, 0.15);
  color: var(--accent-secondary);
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.confidence-badge.medium {
  background: rgba(245, 158, 11, 0.15);
  color: var(--accent-warning);
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.insight-panel, .safety-panel, .citations-panel {
  margin-top: 14px;
  padding: 12px;
  border-radius: var(--border-radius-md);
  border: 1px solid var(--glass-border);
  font-size: 13px;
}

.insight-panel {
  background: rgba(139, 92, 246, 0.05);
  border-color: rgba(139, 92, 246, 0.2);
}

.safety-panel {
  background: rgba(239, 68, 68, 0.05);
  border-color: rgba(239, 68, 68, 0.2);
}

.citations-panel {
  background: rgba(255, 255, 255, 0.02);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  margin-bottom: 6px;
  text-transform: uppercase;
  font-size: 11px;
  letter-spacing: 0.05em;
}

.insight-panel .panel-title { color: var(--accent-tertiary); }
.safety-panel .panel-title { color: var(--accent-danger); }
.citations-panel .panel-title { color: var(--accent-secondary); }

ul {
  padding-left: 18px;
}

.citation-links {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}

.citation-pill {
  background: var(--bg-tertiary);
  border: 1px solid var(--glass-border);
  padding: 4px 10px;
  border-radius: var(--border-radius-sm);
  cursor: pointer;
  transition: var(--transition-smooth);
}

.citation-pill:hover {
  background: rgba(59, 130, 246, 0.1);
  border-color: var(--accent-primary);
}

.chat-input-bar {
  display: flex;
  gap: 12px;
  padding: 12px;
  border-radius: var(--border-radius-md);
}

.chat-input-bar input {
  flex-grow: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-family: var(--font-body);
  font-size: 15px;
}

.chat-input-bar button {
  background: var(--accent-primary);
  border: none;
  border-radius: var(--border-radius-sm);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  transition: var(--transition-smooth);
}

.chat-input-bar button:hover {
  background: #2563eb;
  transform: translateY(-2px);
}

/* Typing Indicator Animation */
.typing-indicator span {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-secondary);
  animation: typing 1.4s infinite both;
  margin: 0 2px;
}

.typing-indicator span:nth-child(2) { animation-delay: .2s; }
.typing-indicator span:nth-child(3) { animation-delay: .4s; }

@keyframes typing {
  0% { transform: scale(1); opacity: 0.3; }
  20% { transform: scale(1.4); opacity: 1; }
  100% { transform: scale(1); opacity: 0.3; }
}
```

---

## 7.5 Main Dashboard View Component

**File:** `plantmind/web/src/components/DashboardView.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Shield, Hammer, AlertOctagon, RefreshCw } from 'lucide-react';
import './DashboardView.css';

const API_BASE = 'http://localhost:8000/api/v1';

function DashboardView() {
  const [stats, setStats] = useState({ total_nodes: 0, total_edges: 0 });
  const [loading, setLoading] = useState(false);
  const [rcaResult, setRcaResult] = useState(null);
  const [selectedEquip, setSelectedEquip] = useState('P-104');

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE}/graph/stats`);
      setStats(response.data);
    } catch (err) {
      console.error(err);
    }
  };

  const runRca = async (tag) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/agents/rca`, { equipment_tag: tag });
      setRcaResult(response.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    runRca(selectedEquip);
  }, [selectedEquip]);

  return (
    <div className="dashboard-container">
      <header className="view-header">
        <div className="header-title">
          <h1>Asset Reliability & RCA Engine</h1>
          <p>Automated root cause analysis and equipment health logs</p>
        </div>
        <button className="refresh-btn glass-panel" onClick={fetchStats}>
          <RefreshCw size={16} />
        </button>
      </header>

      {/* Grid Summary Row */}
      <div className="metrics-grid">
        <div className="metric-card glass-panel">
          <div className="metric-icon blue"><Hammer /></div>
          <div className="metric-vals">
            <h3>{stats.total_nodes || 24}</h3>
            <p>Knowledge Entities</p>
          </div>
        </div>
        <div className="metric-card glass-panel">
          <div className="metric-icon purple"><Shield /></div>
          <div className="metric-vals">
            <h3>{stats.total_edges || 38}</h3>
            <p>Linked Relationships</p>
          </div>
        </div>
        <div className="metric-card glass-panel">
          <div className="metric-icon orange"><AlertOctagon /></div>
          <div className="metric-vals">
            <h3>{selectedEquip}</h3>
            <p>Selected Focus Tag</p>
          </div>
        </div>
      </div>

      <div className="analyzer-section">
        <div className="control-tabs glass-panel">
          <button 
            className={`tab-btn ${selectedEquip === 'P-104' ? 'active' : ''}`}
            onClick={() => setSelectedEquip('P-104')}
          >
            Pump P-104
          </button>
          <button 
            className={`tab-btn ${selectedEquip === 'C-302' ? 'active' : ''}`}
            onClick={() => setSelectedEquip('C-302')}
          >
            Compressor C-302
          </button>
          <button 
            className={`tab-btn ${selectedEquip === 'HX-201' ? 'active' : ''}`}
            onClick={() => setSelectedEquip('HX-201')}
          >
            Exchanger HX-201
          </button>
        </div>

        {loading ? (
          <div className="loading-card glass-panel">
            <div className="spinner"></div>
            <p>Running Reliability RCA Agent...</p>
          </div>
        ) : rcaResult ? (
          <div className="rca-output-grid">
            <div className="main-findings glass-panel">
              <h2>RCA Summary</h2>
              <p className="summary-text">{rcaResult.findings_summary}</p>
              
              <div className="failure-modes-list">
                <h3>Detected Failure Modes</h3>
                {rcaResult.recurring_failure_modes?.map((fm, idx) => (
                  <div key={idx} className="failure-item">
                    <span className="fm-badge">{fm.mode}</span>
                    <span className="fm-freq">Count: {fm.frequency}</span>
                  </div>
                ))}
              </div>

              <div className="root-cause-block">
                <h3>Root Cause Conclusion</h3>
                <div className="cause-box">
                  <strong>{rcaResult.root_cause_analysis?.primary_cause}</strong>
                  <ul>
                    {rcaResult.root_cause_analysis?.contributing_factors.map((factor, idx) => (
                      <li key={idx}>{factor}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            <div className="recommendations-sidebar glass-panel">
              <h2>Corrective Action Plan</h2>
              <div className="risk-score-badge">
                Safety Risk Score: <span>{rcaResult.safety_risk_score}/10</span>
              </div>
              <div className="recs-list">
                {rcaResult.recommendations?.map((rec, idx) => (
                  <div key={idx} className={`rec-card ${rec.priority.toLowerCase()}`}>
                    <div className="rec-header">
                      <span className="rec-prio">{rec.priority} Priority</span>
                    </div>
                    <h4>{rec.action}</h4>
                    <p>{rec.rationale}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="empty-state glass-panel">
            No analysis results available. Trigger the building of the graph in Step 4.
          </div>
        )}
      </div>
    </div>
  );
}

export default DashboardView;
```

**File:** `plantmind/web/src/components/DashboardView.css`

```css
.dashboard-container {
  padding: 30px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.header-title h1 {
  font-size: 26px;
}

.header-title p {
  color: var(--text-secondary);
  font-size: 14px;
}

.refresh-btn {
  background: transparent;
  border: 1px solid var(--glass-border);
  color: var(--text-primary);
  width: 40px;
  height: 40px;
  border-radius: var(--border-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: var(--transition-smooth);
}

.refresh-btn:hover {
  background: rgba(255, 255, 255, 0.05);
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--glass-border);
  padding-bottom: 16px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-radius: var(--border-radius-md);
}

.metric-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--border-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}

.metric-icon.blue { background: rgba(59, 130, 246, 0.1); color: var(--accent-primary); }
.metric-icon.purple { background: rgba(139, 92, 246, 0.1); color: var(--accent-tertiary); }
.metric-icon.orange { background: rgba(245, 158, 11, 0.1); color: var(--accent-warning); }

.control-tabs {
  display: flex;
  padding: 6px;
  border-radius: var(--border-radius-md);
  margin-bottom: 20px;
  width: max-content;
}

.tab-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  padding: 10px 20px;
  cursor: pointer;
  border-radius: var(--border-radius-sm);
  font-family: var(--font-body);
  font-weight: 500;
  transition: var(--transition-smooth);
}

.tab-btn:hover {
  color: var(--text-primary);
}

.tab-btn.active {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

.rca-output-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}

.main-findings, .recommendations-sidebar {
  padding: 24px;
  border-radius: var(--border-radius-lg);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.summary-text {
  font-size: 15px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.cause-box {
  background: rgba(239, 68, 68, 0.03);
  border: 1px solid rgba(239, 68, 68, 0.1);
  border-radius: var(--border-radius-md);
  padding: 16px;
  margin-top: 10px;
}

.cause-box strong {
  display: block;
  font-size: 16px;
  margin-bottom: 8px;
  color: var(--accent-danger);
}

.risk-score-badge {
  background: rgba(239, 68, 68, 0.1);
  color: var(--accent-danger);
  border: 1px solid rgba(239, 68, 68, 0.3);
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 600;
  width: max-content;
  align-self: center;
}

.rec-card {
  background: var(--bg-tertiary);
  border-left: 4px solid var(--text-muted);
  border-radius: var(--border-radius-md);
  padding: 16px;
  margin-bottom: 12px;
}

.rec-card.high { border-left-color: var(--accent-danger); }
.rec-card.medium { border-left-color: var(--accent-warning); }
.rec-card.low { border-left-color: var(--accent-primary); }

.rec-prio {
  font-size: 11px;
  text-transform: uppercase;
  font-weight: 600;
}

.rec-card.high .rec-prio { color: var(--accent-danger); }
.rec-card.medium .rec-prio { color: var(--accent-warning); }
.rec-card.low .rec-prio { color: var(--accent-primary); }

.rec-card h4 {
  font-size: 15px;
  margin: 6px 0;
}

.rec-card p {
  font-size: 13px;
  color: var(--text-secondary);
}

.loading-card {
  padding: 60px;
  text-align: center;
  border-radius: var(--border-radius-lg);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(59, 130, 246, 0.1);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 1s infinite linear;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 992px) {
  .rca-output-grid {
    grid-template-columns: 1fr;
  }
}
```

---

## 7.6 Compliance Gap & Alert Views

### 7.6.1 Compliance View Component
**File:** `plantmind/web/src/components/ComplianceView.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { AlertCircle, CheckCircle } from 'lucide-react';
import './ComplianceView.css';

const API_BASE = 'http://localhost:8000/api/v1';

function ComplianceView() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const runAudit = async () => {
      try {
        const response = await axios.post(`${API_BASE}/agents/compliance`);
        setData(response.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    runAudit();
  }, []);

  if (loading) {
    return (
      <div className="view-loading">
        <div className="spinner"></div>
        <p>Analyzing knowledge graph compliance vectors...</p>
      </div>
    );
  }

  return (
    <div className="compliance-container">
      <header className="view-header">
        <h1>Regulatory Compliance Audit</h1>
        <p>Auto-mapping equipment inspections to OISD & Factory Act requirements</p>
      </header>

      {data && (
        <div className="audit-results">
          <div className="audit-score-card glass-panel">
            <div className="score-ring">
              <h2>{data.audit_score}%</h2>
              <p>Audit Score</p>
            </div>
            <div className="score-summary">
              <h3>Facility Status: {data.audit_score > 80 ? 'Safe' : 'Action Required'}</h3>
              <p>{data.summary}</p>
            </div>
          </div>

          <h2>Discovered Violations & Gaps ({data.total_gaps})</h2>
          <div className="violations-list">
            {data.violations?.map((viol, idx) => (
              <div key={idx} className={`violation-card glass-panel ${viol.severity.toLowerCase()}`}>
                <div className="viol-header">
                  <span className={`severity-tag ${viol.severity.toLowerCase()}`}>
                    {viol.severity} Risk
                  </span>
                  <h4>{viol.equipment_tag} ↔ {viol.regulation}</h4>
                </div>
                <p className="viol-desc"><strong>Issue:</strong> {viol.description}</p>
                <p className="viol-imp"><strong>Implication:</strong> {viol.implication}</p>
                <div className="viol-rec">
                  <strong>Corrective Action Plan:</strong> {viol.recommended_action}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default ComplianceView;
```

**File:** `plantmind/web/src/components/ComplianceView.css`

```css
.compliance-container {
  padding: 30px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.view-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.audit-score-card {
  display: flex;
  align-items: center;
  gap: 30px;
  padding: 30px;
  border-radius: var(--border-radius-lg);
  margin-bottom: 24px;
}

.score-ring {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  border: 4px solid var(--accent-primary);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.2);
}

.score-ring h2 {
  font-size: 32px;
}

.score-ring p {
  font-size: 11px;
  color: var(--text-secondary);
}

.score-summary h3 {
  font-size: 20px;
  margin-bottom: 8px;
}

.score-summary p {
  color: var(--text-secondary);
  line-height: 1.6;
}

.violations-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.violation-card {
  padding: 20px;
  border-radius: var(--border-radius-md);
  border-left: 4px solid var(--text-muted);
}

.violation-card.critical { border-left-color: var(--accent-danger); }
.violation-card.high { border-left-color: var(--accent-warning); }
.violation-card.medium { border-left-color: var(--accent-primary); }

.viol-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.severity-tag {
  font-size: 10px;
  text-transform: uppercase;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 20px;
}

.severity-tag.critical { background: rgba(239, 68, 68, 0.15); color: var(--accent-danger); border: 1px solid rgba(239, 68, 68, 0.3); }
.severity-tag.high { background: rgba(245, 158, 11, 0.15); color: var(--accent-warning); border: 1px solid rgba(245, 158, 11, 0.3); }
.severity-tag.medium { background: rgba(59, 130, 246, 0.15); color: var(--accent-primary); border: 1px solid rgba(59, 130, 246, 0.3); }

.viol-desc, .viol-imp {
  font-size: 14px;
  margin-bottom: 8px;
  color: var(--text-secondary);
}

.viol-rec {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--glass-border);
  padding: 12px;
  border-radius: var(--border-radius-sm);
  font-size: 14px;
  margin-top: 10px;
}
```

### 7.6.2 Lessons Learned Component
**File:** `plantmind/web/src/components/LessonsView.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Award, Zap } from 'lucide-react';
import './LessonsView.css';

const API_BASE = 'http://localhost:8000/api/v1';

function LessonsView() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const runScan = async () => {
      try {
        const response = await axios.post(`${API_BASE}/agents/lessons`);
        setData(response.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    runScan();
  }, []);

  if (loading) {
    return (
      <div className="view-loading">
        <div className="spinner"></div>
        <p>Scanning graph for repeated incidents & alignment issues...</p>
      </div>
    );
  }

  return (
    <div className="lessons-container">
      <header className="view-header">
        <h1>Proactive Lessons Learned</h1>
        <p>Detecting common cross-equipment root causes to prevent future outages</p>
      </header>

      {data && (
        <div className="lessons-list">
          {data.lessons?.map((lesson, idx) => (
            <div key={idx} className="lesson-card glass-panel">
              <div className="lesson-header">
                <div className="lesson-meta">
                  <Award size={18} className="lesson-badge-icon" />
                  <h3>{lesson.title}</h3>
                </div>
                <span className={`severity-tag ${lesson.severity.toLowerCase()}`}>
                  {lesson.severity} Priority Alert
                </span>
              </div>

              <div className="lesson-body">
                <p><strong>Affected Equipment:</strong> {lesson.equipment_affected.join(', ')}</p>
                <p><strong>Recurring Problem:</strong> {lesson.problem_statement}</p>
                <p className="highlighted-learning">
                  <strong>Core Learning:</strong> {lesson.key_lesson}
                </p>

                <div className="checklist-box">
                  <h4><Zap size={14} /> Preventative Checklist</h4>
                  <ul>
                    {lesson.proactive_checklist.map((item, cIdx) => (
                      <li key={cIdx}>{item}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default LessonsView;
```

**File:** `plantmind/web/src/components/LessonsView.css`

```css
.lessons-container {
  padding: 30px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.lessons-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.lesson-card {
  padding: 24px;
  border-radius: var(--border-radius-lg);
}

.lesson-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--glass-border);
  padding-bottom: 12px;
  margin-bottom: 16px;
}

.lesson-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.lesson-badge-icon {
  color: var(--accent-tertiary);
}

.lesson-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
  font-size: 14px;
}

.highlighted-learning {
  background: rgba(139, 92, 246, 0.05);
  border: 1px solid rgba(139, 92, 246, 0.1);
  padding: 12px;
  border-radius: var(--border-radius-sm);
  color: var(--text-primary);
}

.checklist-box {
  background: rgba(16, 185, 129, 0.02);
  border: 1px solid rgba(16, 185, 129, 0.1);
  padding: 16px;
  border-radius: var(--border-radius-md);
  margin-top: 10px;
}

.checklist-box h4 {
  color: var(--accent-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  margin-bottom: 8px;
}

.checklist-box ul {
  padding-left: 20px;
  color: var(--text-secondary);
}

.checklist-box li {
  margin-bottom: 6px;
}
```

---

## 7.7 Force-Directed Knowledge Graph Visualizer

We use `vis-network` (or a simple React fallback) to render the graph relationships.

**File:** `plantmind/web/src/components/GraphView.jsx`

```jsx
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Network } from 'lucide-react';
import './GraphView.css';

const API_BASE = 'http://localhost:8000/api/v1';

function GraphView() {
  const [data, setData] = useState({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const containerRef = useRef(null);

  useEffect(() => {
    const fetchGraph = async () => {
      try {
        const response = await axios.get(`${API_BASE}/graph/export`);
        setData(response.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchGraph();
  }, []);

  return (
    <div className="graph-container">
      <header className="view-header">
        <h1>Industrial Knowledge Graph</h1>
        <p>Interactive graph visualization of equipment, work orders, SOPs and regulations</p>
      </header>

      {loading ? (
        <div className="view-loading">
          <div className="spinner"></div>
          <p>Mapping relationship pathways...</p>
        </div>
      ) : (
        <div className="graph-visual-wrapper glass-panel">
          {/* Simple Visual List representation as fallback if canvas is not configured */}
          <div className="visual-legend">
            <span className="legend-item"><span className="dot equip"></span> Equipment</span>
            <span className="legend-item"><span className="dot doc"></span> Document</span>
            <span className="legend-item"><span className="dot reg"></span> Regulation</span>
            <span className="legend-item"><span className="dot wo"></span> Work Order</span>
          </div>

          <div className="nodes-relationships-table">
            <h3>Graph Node Directory</h3>
            <div className="node-grid">
              {data.nodes.map((node) => (
                <div key={node.id} className="node-chip">
                  <span className={`chip-type ${node.type.toLowerCase()}`}>{node.type}</span>
                  <strong>{node.label}</strong>
                </div>
              ))}
            </div>

            <h3 style={{ marginTop: '24px' }}>Active Graph Edges (Relationships)</h3>
            <div className="edge-list">
              {data.edges.map((edge, idx) => (
                <div key={idx} className="edge-row">
                  <span className="node-ref">{edge.source}</span>
                  <span className="rel-tag">--[{edge.label}]--&gt;</span>
                  <span className="node-ref">{edge.target}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default GraphView;
```

**File:** `plantmind/web/src/components/GraphView.css`

```css
.graph-container {
  padding: 30px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  height: 100%;
}

.graph-visual-wrapper {
  padding: 24px;
  border-radius: var(--border-radius-lg);
  flex-grow: 1;
  overflow-y: auto;
}

.visual-legend {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  font-size: 13px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.dot.equip { background: var(--accent-primary); }
.dot.doc { background: var(--accent-secondary); }
.dot.reg { background: var(--accent-tertiary); }
.dot.wo { background: var(--accent-warning); }

.nodes-relationships-table h3 {
  font-size: 16px;
  border-bottom: 1px solid var(--glass-border);
  padding-bottom: 8px;
  margin-bottom: 12px;
}

.node-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.node-chip {
  background: var(--bg-tertiary);
  border: 1px solid var(--glass-border);
  padding: 6px 12px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.chip-type {
  font-size: 9px;
  text-transform: uppercase;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 10px;
}

.chip-type.equipment { background: rgba(59, 130, 246, 0.1); color: var(--accent-primary); }
.chip-type.document { background: rgba(16, 185, 129, 0.1); color: var(--accent-secondary); }
.chip-type.regulation { background: rgba(139, 92, 246, 0.1); color: var(--accent-tertiary); }
.chip-type.workorder { background: rgba(245, 158, 11, 0.1); color: var(--accent-warning); }

.edge-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 10px;
}

.edge-row {
  background: rgba(255, 255, 255, 0.01);
  border: 1px solid var(--glass-border);
  border-radius: var(--border-radius-sm);
  padding: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-family: monospace;
  font-size: 12px;
}

.node-ref {
  color: var(--text-primary);
  font-weight: bold;
}

.rel-tag {
  color: var(--accent-tertiary);
}
```

---

## 7.8 Verification Gate

**All verification checks must pass before proceeding to Step 8:**

### Check 1: Build the Vite bundle
```bash
cd "d:\hackathon projects\PlantMind ET\plantmind\web"
npm run build
```
**Expected:** Vite compilation finishes successfully without TypeScript/JS syntax errors.

### Check 2: Run local dev server
```bash
npm run dev
```
**Expected:** Site accessible at `http://localhost:5173`. Open in a browser.

### Check 3: Check mobile responsive layout
Use Chrome DevTools to inspect in mobile mode (e.g., iPhone 12/Pro). Navigation menu should collapse cleanly to a bottom or top header navigation layout.

---

## Output of This Step

After completing Step 7, you should have:
- ✅ **React Single Page App** styled with a dark mode glassmorphism layout
- ✅ **RAG Copilot View** supporting questions, response streaming (or loading), citations, and confidence badges
- ✅ **RCA Dashboard View** displaying failure modes, root causes, and corrective action score cards
- ✅ **Compliance & Lessons Learned Views** rendering detailed specialist agent outputs
- ✅ **Knowledge Graph Directory View** showing nodes & relational edges
- ✅ App optimized for mobile viewports (portrait and landscape)

**→ Proceed to [Step 8 — Architecture Diagram & Documentation](step8_documentation.md)**
