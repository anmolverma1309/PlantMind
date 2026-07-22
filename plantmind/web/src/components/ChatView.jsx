import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, Sparkles, AlertTriangle, ShieldCheck, HelpCircle } from 'lucide-react';
import { API_BASE } from '../config';
import './ChatView.css';

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
