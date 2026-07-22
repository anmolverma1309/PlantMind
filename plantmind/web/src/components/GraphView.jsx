import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Network } from 'lucide-react';
import { API_BASE } from '../config';
import './GraphView.css';

function GraphView() {
  const [data, setData] = useState({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);

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
        <p>Interactive graph directory of equipment, work orders, SOPs and regulations</p>
      </header>

      {loading ? (
        <div className="view-loading">
          <div className="spinner"></div>
          <p>Mapping relationship pathways...</p>
        </div>
      ) : (
        <div className="graph-visual-wrapper glass-panel">
          <div className="visual-legend">
            <span className="legend-item"><span className="dot equip"></span> Equipment</span>
            <span className="legend-item"><span className="dot doc"></span> Document</span>
            <span className="legend-item"><span className="dot reg"></span> Regulation</span>
            <span className="legend-item"><span className="dot wo"></span> Work Order</span>
          </div>

          <div className="nodes-relationships-table">
            <h3>Graph Node Directory ({data.nodes.length})</h3>
            <div className="node-grid">
              {data.nodes.map((node) => (
                <div key={node.id} className="node-chip">
                  <span className={`chip-type ${node.type.toLowerCase()}`}>{node.type}</span>
                  <strong>{node.label}</strong>
                </div>
              ))}
            </div>

            <h3 style={{ marginTop: '24px' }}>Active Graph Edges / Relationships ({data.edges.length})</h3>
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
