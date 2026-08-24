import React from 'react';
import { 
  Shield,
  RotateCw, 
  Download, 
  MessageSquare, 
  History,
  UploadCloud,
  LayoutDashboard,
  Sparkles
} from 'lucide-react';

export default function Navbar({ 
  seed, 
  totalRecords, 
  loading, 
  onRegenerate, 
  onExportCsv, 
  onOpenNLQuery,
  onOpenAuditHistory,
  onOpenUpload,
  currentView = 'landing',
  onToggleView
}) {
  return (
    <header style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '0.35rem 0',
      flexWrap: 'wrap',
      gap: '0.75rem',
      borderBottom: '1px solid var(--border-subtle)',
      paddingBottom: '0.85rem'
    }}>
      {/* Brand Identity & View Toggle */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
        <div 
          onClick={() => onToggleView && onToggleView('landing')}
          style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer' }}
        >
           <span style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-hero)', letterSpacing: '-0.02em' }}>
            FinReconcile AI
          </span>
        </div>

        {/* View Switcher (Overview vs Dashboard) */}
        <div style={{
          display: 'flex',
          background: '#101318',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-sm)',
          padding: '2px'
        }}>
          <button
            onClick={() => onToggleView && onToggleView('landing')}
            style={{
              background: currentView === 'landing' ? 'var(--bg-surface-hover)' : 'transparent',
              color: currentView === 'landing' ? 'var(--text-hero)' : 'var(--text-muted)',
              border: 'none',
              borderRadius: '4px',
              padding: '0.25rem 0.65rem',
              fontSize: '0.72rem',
              fontWeight: 500,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem'
            }}
          >
            <Sparkles size={12} color={currentView === 'landing' ? 'var(--accent)' : 'currentColor'} />
            <span>Overview</span>
          </button>

          <button
            onClick={() => onToggleView && onToggleView('dashboard')}
            style={{
              background: currentView === 'dashboard' ? 'var(--bg-surface-hover)' : 'transparent',
              color: currentView === 'dashboard' ? 'var(--text-hero)' : 'var(--text-muted)',
              border: 'none',
              borderRadius: '4px',
              padding: '0.25rem 0.65rem',
              fontSize: '0.72rem',
              fontWeight: 500,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem'
            }}
          >
            <LayoutDashboard size={12} color={currentView === 'dashboard' ? 'var(--status-match)' : 'currentColor'} />
            <span>Dashboard</span>
          </button>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="navbar-actions" style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', flexWrap: 'wrap' }}>
        
        {/* Upload Custom CSV */}
        <button 
          onClick={onOpenUpload}
          className="btn-ghost"
          title="Upload custom General Ledger, Bank, and Gateway CSV files"
        >
          <UploadCloud size={13} color="var(--accent)" />
          <span>Upload CSV</span>
        </button>

        {/* Audit History */}
        <button 
          onClick={onOpenAuditHistory}
          className="btn-ghost"
          title="Inspect immutable audit run history"
        >
          <History size={13} />
          <span>Audit History</span>
        </button>

        {/* AI Query */}
        <button 
          onClick={onOpenNLQuery}
          className="btn-ghost"
          title="Query reconciled dataset in natural language (⌘K)"
        >
          <MessageSquare size={13} />
          <span>AI Query <kbd style={{ fontSize: '0.65rem', opacity: 0.6, marginLeft: '0.2rem' }}>⌘K</kbd></span>
        </button>

        {/* Fresh Batch */}
        <button 
          onClick={onRegenerate}
          disabled={loading}
          className="btn-ghost"
          title="Regenerate synthetic test dataset"
        >
          <RotateCw size={13} className={loading ? "animate-spin" : ""} />
          <span>{loading ? "Reconciling..." : "Fresh Batch"}</span>
        </button>

        {/* Export CSV */}
        <button 
          onClick={onExportCsv}
          className="btn-primary"
          title="Download reconciled dataset as CSV"
        >
          <Download size={13} />
          <span>Export CSV</span>
        </button>

      </div>
    </header>
  );
}
