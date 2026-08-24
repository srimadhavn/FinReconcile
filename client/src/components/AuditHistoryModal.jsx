import React, { useState, useEffect } from 'react';
import { X, History, ChevronRight } from 'lucide-react';
import axios from 'axios';

export default function AuditHistoryModal({ onClose, onSelectHistoricalRun }) {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRuns = async () => {
      try {
        const res = await axios.get('/api/audit/runs');
        setRuns(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchRuns();
  }, []);

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
        maxWidth: '740px',
        maxHeight: '85vh',
        overflowY: 'auto',
        boxShadow: '0 20px 50px rgba(0, 0, 0, 0.7)',
        padding: '1.25rem 1.5rem'
      }}>
        
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.85rem', marginBottom: '1rem' }}>
          <div>
            <h2 style={{ fontSize: '0.9375rem', fontWeight: 600, color: 'var(--text-hero)' }}>
              Audit Run Archives
            </h2>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Historical snapshots with immutable timestamp proofs and precision evaluations
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

        {/* List of Runs */}
        {loading ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-dim)', fontSize: '0.8125rem' }}>
            Loading audit run archives...
          </div>
        ) : runs.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-dim)', fontSize: '0.8125rem' }}>
            No historical runs recorded yet.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {runs.map((r, idx) => {
              const formattedDate = new Date(r.timestamp).toLocaleString();
              return (
                <div
                  key={r.run_id || idx}
                  style={{
                    background: '#0a0c10',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '5px',
                    padding: '0.65rem 0.85rem',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    gap: '0.75rem'
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                      <span className="mono" style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-hero)' }}>
                        {r.run_id}
                      </span>
                      <span className="status-indicator match" style={{ fontSize: '0.72rem' }}>
                        <span className="status-dot match" />
                        <span>{r.summary?.match_rate_percentage}% Match</span>
                      </span>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                        Seed: #{r.parameters?.seed}
                      </span>
                    </div>

                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                      {formattedDate} · Tol: ±{r.parameters?.date_tolerance_days}d / {(r.parameters?.fee_tolerance_pct * 100).toFixed(1)}% fee
                    </div>
                  </div>

                  <button
                    onClick={() => {
                      onSelectHistoricalRun(r);
                      onClose();
                    }}
                    className="btn-ghost"
                    style={{ fontSize: '0.75rem', padding: '0.3rem 0.65rem' }}
                  >
                    <span>Load</span>
                  </button>
                </div>
              );
            })}
          </div>
        )}

      </div>
    </div>
  );
}
