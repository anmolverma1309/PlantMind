import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Shield, Hammer, AlertOctagon, RefreshCw } from 'lucide-react';
import { API_BASE } from '../config';
import './DashboardView.css';

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
                {rcaResult.recurring_failure_modes?.length > 0 ? (
                  rcaResult.recurring_failure_modes.map((fm, idx) => (
                    <div key={idx} className="failure-item">
                      <span className="fm-badge">{fm.mode}</span>
                      <span className="fm-freq">Count: {fm.frequency}</span>
                    </div>
                  ))
                ) : (
                  <p className="summary-text">No recurring failures noted in work order history.</p>
                )}
              </div>

              <div className="root-cause-block">
                <h3>Root Cause Conclusion</h3>
                <div className="cause-box">
                  <strong>{rcaResult.root_cause_analysis?.primary_cause || "No clear cause determined."}</strong>
                  <ul>
                    {rcaResult.root_cause_analysis?.contributing_factors?.map((factor, idx) => (
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
