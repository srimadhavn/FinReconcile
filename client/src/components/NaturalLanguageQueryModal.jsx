import React, { useState } from 'react';
import { X, Search } from 'lucide-react';
import axios from 'axios';

export default function NaturalLanguageQueryModal({ onClose, onSelectResult }) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);

  const sampleQueries = [
    "Show all exceptions above ₹10,000",
    "Find duplicate ledger vouchers",
    "Show unrecorded direct bank credits",
    "Show chargebacks and disputed payments"
  ];

  const handleRunQuery = async (qText) => {
    const textToRun = qText || query;
    if (!textToRun.trim()) return;
    setLoading(true);
    try {
      const res = await axios.post('/api/query', { query: textToRun });
      setResponse(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(3px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '1.25rem'
    }}>
      <div style={{
        background: '#11141a',
        border: '1px solid var(--border-strong)',
        borderRadius: '6px',
        width: '100%',
        maxWidth: '680px',
        maxHeight: '85vh',
        overflowY: 'auto',
        boxShadow: '0 20px 50px rgba(0, 0, 0, 0.7)',
        padding: '1.25rem 1.5rem'
      }}>
        
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.85rem', marginBottom: '1rem' }}>
          <div>
            <h2 style={{ fontSize: '0.9375rem', fontWeight: 600, color: 'var(--text-hero)' }}>
              AI Financial Controller Assistant
            </h2>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Natural language audit query interface powered by Gemini 3.6 Flash
            </div>
          </div>

          <button 
            onClick={onClose}
            style={{
              background: 'transparent',
              border: '1px solid var(--border-subtle)',
              borderRadius: '4px',
              width: '26px',
              height: '26px',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <X size={14} />
          </button>
        </div>

        {/* Input Bar */}
        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
          <input
            type="text"
            placeholder="e.g. Show duplicate entries and associated ledger risk..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleRunQuery()}
            style={{
              flex: 1,
              background: '#0a0c10',
              border: '1px solid var(--border-subtle)',
              borderRadius: '5px',
              padding: '0.45rem 0.75rem',
              color: 'var(--text-primary)',
              fontSize: '0.8125rem',
              outline: 'none'
            }}
          />
          <button
            onClick={() => handleRunQuery()}
            disabled={loading}
            className="btn-primary"
          >
            {loading ? "Querying..." : "Ask Agent"}
          </button>
        </div>

        {/* Suggested Queries */}
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginBottom: '0.35rem' }}>
            Suggested Queries:
          </div>
          <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
            {sampleQueries.map((sq, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setQuery(sq);
                  handleRunQuery(sq);
                }}
                style={{
                  background: '#0a0c10',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '4px',
                  padding: '0.2rem 0.5rem',
                  fontSize: '0.72rem',
                  color: 'var(--text-muted)',
                  cursor: 'pointer'
                }}
              >
                {sq}
              </button>
            ))}
          </div>
        </div>

        {/* Response Box */}
        {response && (
          <div style={{ background: '#0a0c10', border: '1px solid var(--border-subtle)', borderRadius: '5px', padding: '0.85rem' }}>
            
            <div style={{ fontSize: '0.78rem', color: 'var(--text-primary)', lineHeight: '1.5', marginBottom: '0.75rem' }}>
              {response.answer}
            </div>

            {response.ai_model && (
              <div style={{ marginBottom: '0.75rem', fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                <span className="mono" style={{ background: '#11141a', border: '1px solid var(--border-subtle)', padding: '0.15rem 0.45rem', borderRadius: '4px' }}>
                  Model: {response.ai_model}
                </span>
              </div>
            )}

            {/* Filtered Exceptions */}
            {response.filtered_exceptions && response.filtered_exceptions.length > 0 && (
              <div>
                <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--status-exception)', marginBottom: '0.4rem' }}>
                  Matched Discrepancy Records ({response.filtered_exceptions.length}):
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', maxHeight: '200px', overflowY: 'auto' }}>
                  {response.filtered_exceptions.map((exc, idx) => (
                    <div 
                      key={idx}
                      onClick={() => {
                        onSelectResult(exc);
                        onClose();
                      }}
                      style={{
                        background: '#11141a',
                        border: '1px solid var(--border-subtle)',
                        borderRadius: '4px',
                        padding: '0.45rem 0.75rem',
                        cursor: 'pointer',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                          <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-hero)' }}>
                            {exc.id}
                          </span>
                          <span className="status-indicator exception" style={{ fontSize: '0.68rem' }}>
                            <span className="status-dot exception" />
                            <span>{exc.category ? exc.category.replace(/_/g, ' ') : 'Exception'}</span>
                          </span>
                        </div>
                        <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                          {exc.counterparty} · {exc.reference}
                        </div>
                      </div>

                      <div style={{ textAlign: 'right' }}>
                        <div className="mono" style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-hero)' }}>
                          ₹{Number(exc.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </div>
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)' }}>Inspect</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

          </div>
        )}

      </div>
    </div>
  );
}
