import React from 'react';
import { SlidersHorizontal, RefreshCw } from 'lucide-react';

export default function ToleranceControls({ 
  dateTolerance, 
  setDateTolerance, 
  feeTolerance, 
  setFeeTolerance,
  onApply,
  loading 
}) {
  const setPreset = (d, f) => {
    setDateTolerance(d);
    setFeeTolerance(f);
  };

  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius-md)',
      padding: '0.85rem 1.25rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      flexWrap: 'wrap',
      gap: '1rem'
    }}>
      
      {/* Label & Presets */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-hero)' }}>
          <SlidersHorizontal size={13} color="var(--accent)" />
          <span>Calibration</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <button
            onClick={() => setPreset(0, 0.0)}
            className="btn-ghost"
            style={{ padding: '0.2rem 0.5rem', fontSize: '0.7rem' }}
          >
            Strict T+0
          </button>
          <button
            onClick={() => setPreset(3, 0.035)}
            className="btn-ghost"
            style={{ 
              padding: '0.2rem 0.5rem', 
              fontSize: '0.7rem',
              color: 'var(--text-primary)',
              background: 'rgba(99, 102, 241, 0.08)',
              borderColor: 'var(--accent-border)'
            }}
          >
            Standard (±3d / 3.5%)
          </button>
          <button
            onClick={() => setPreset(7, 0.06)}
            className="btn-ghost"
            style={{ padding: '0.2rem 0.5rem', fontSize: '0.7rem' }}
          >
            High Lag (±7d / 6%)
          </button>
        </div>
      </div>

      {/* Sliders & Apply Button */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', flexWrap: 'wrap', flex: 1, justifyContent: 'flex-end' }}>
        
        {/* Slider 1: Date */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', minWidth: '180px' }}>
          <span style={{ fontSize: '0.73rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
            Lag: <strong className="mono" style={{ color: 'var(--text-primary)' }}>±{dateTolerance}d</strong>
          </span>
          <input 
            type="range" 
            min="0" 
            max="7" 
            step="1"
            value={dateTolerance}
            onChange={(e) => setDateTolerance(Number(e.target.value))}
            style={{ width: '100%', height: '3px', accentColor: 'var(--accent)', cursor: 'pointer' }}
          />
        </div>

        {/* Slider 2: Fee */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', minWidth: '180px' }}>
          <span style={{ fontSize: '0.73rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
            MDR: <strong className="mono" style={{ color: 'var(--text-primary)' }}>{(feeTolerance * 100).toFixed(1)}%</strong>
          </span>
          <input 
            type="range" 
            min="0.00" 
            max="0.06" 
            step="0.005"
            value={feeTolerance}
            onChange={(e) => setFeeTolerance(Number(e.target.value))}
            style={{ width: '100%', height: '3px', accentColor: 'var(--accent)', cursor: 'pointer' }}
          />
        </div>

        {/* Apply Simulation */}
        <button 
          onClick={onApply}
          disabled={loading}
          className="btn-primary"
          style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
        >
          <RefreshCw size={11} className={loading ? "animate-spin" : ""} />
          <span>{loading ? "Simulating..." : "Apply"}</span>
        </button>

      </div>

    </div>
  );
}
