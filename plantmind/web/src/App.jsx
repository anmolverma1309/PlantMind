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
