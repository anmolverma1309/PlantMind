import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Award, Zap } from 'lucide-react';
import { API_BASE } from '../config';
import './LessonsView.css';

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
