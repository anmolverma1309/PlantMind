import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { AlertCircle, CheckCircle } from 'lucide-react';
import { API_BASE } from '../config';
import { getErrorMessage } from '../utils/errorHandler';
import './ComplianceView.css';

function ComplianceView() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const runAudit = async () => {
      try {
        const response = await axios.post(`${API_BASE}/agents/compliance`);
        setData(response.data);
      } catch (err) {
        console.error('Compliance audit error:', err);
        setData({ audit_score: 0, errors: [getErrorMessage(err, API_BASE)] });
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
