import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import Navbar from './components/Navbar';
import LandingPage from './components/LandingPage';
import KPIHeader from './components/KPIHeader';
import ToleranceControls from './components/ToleranceControls';
import ReconciliationTable from './components/ReconciliationTable';
import InspectorModal from './components/InspectorModal';
import NaturalLanguageQueryModal from './components/NaturalLanguageQueryModal';
import AuditHistoryModal from './components/AuditHistoryModal';
import UploadCSVModal from './components/UploadCSVModal';

export default function App() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [seed, setSeed] = useState(42);
  const [dateTolerance, setDateTolerance] = useState(3);
  const [feeTolerance, setFeeTolerance] = useState(0.035);
  
  // View Switcher: 'landing' (orientation) or 'dashboard' (active data controller)
  const [viewMode, setViewMode] = useState('landing');
  
  const [selectedItem, setSelectedItem] = useState(null);
  const [showNLQuery, setShowNLQuery] = useState(false);
  const [showAuditHistory, setShowAuditHistory] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);

  // Helper: Trigger non-intrusive toast
  const triggerToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage(prev => prev === msg ? null : prev);
    }, 3000);
  };

  // Fetch reconciliation data
  const fetchReconciliation = async (customSeed = seed, dateTol = dateTolerance, feeTol = feeTolerance) => {
    setLoading(true);
    try {
      const res = await axios.post('/api/reconcile', {
        seed: customSeed,
        count: 60,
        date_tolerance_days: dateTol,
        fee_tolerance_pct: feeTol
      });
      setData(res.data);
    } catch (err) {
      console.error('Failed to run reconciliation:', err);
      triggerToast('Error: Failed to connect to reconciliation engine.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReconciliation();
  }, []);

  // Handler: Custom CSV Upload Success
  const handleCustomUploadSuccess = (uploadResult) => {
    setData(uploadResult);
    setSeed('CUSTOM');
    setViewMode('dashboard'); // Automatically switch to dashboard on custom upload
    triggerToast(`✓ Reconciled custom CSV upload (${uploadResult.run_id})`);
  };

  // Keyboard Shortcuts (Cmd+K / Ctrl+K, Escape)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setShowNLQuery(prev => !prev);
      }
      if (e.key === 'Escape') {
        setSelectedItem(null);
        setShowNLQuery(false);
        setShowAuditHistory(false);
        setShowUpload(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Handler: Regenerate Fresh Batch with new random seed
  const handleRegenerate = async () => {
    const nextSeed = Math.floor(Math.random() * 9000) + 1000;
    setSeed(nextSeed);
    try {
      await axios.post('/api/regenerate', { seed: nextSeed, count: 60 });
      await fetchReconciliation(nextSeed, dateTolerance, feeTolerance);
      triggerToast(`✓ Generated fresh synthetic batch (Seed #${nextSeed})`);
    } catch (err) {
      console.error(err);
      triggerToast('Error regenerating batch.');
    }
  };

  // Handler: Apply what-if tolerance simulation
  const handleApplyTolerances = () => {
    fetchReconciliation(seed, dateTolerance, feeTolerance);
    triggerToast(`✓ Recalibrated tolerances: ±${dateTolerance}d lag, ${(feeTolerance * 100).toFixed(1)}% fee`);
  };

  // Handler: Export CSV
  const handleExportCsv = () => {
    window.open(`/api/export/csv?date_tolerance_days=${dateTolerance}&fee_tolerance_pct=${feeTolerance}`, '_blank');
    triggerToast('✓ Exporting reconciled CSV audit report...');
  };

  // Handler: Load snapshot from historical audit run
  const handleSelectHistoricalRun = (historicalRun) => {
    if (historicalRun.full_reconciliation) {
      setData({
        run_id: historicalRun.run_id,
        reconciliation: historicalRun.full_reconciliation,
        ground_truth_accuracy: historicalRun.ground_truth_evaluation,
        parameters: historicalRun.parameters,
        phase1: { match_rate_percentage: 63.93 }
      });
      if (historicalRun.parameters?.seed) {
        setSeed(historicalRun.parameters.seed);
      }
      setViewMode('dashboard');
      triggerToast(`✓ Loaded snapshot ${historicalRun.run_id}`);
    }
  };

  const reconciliation = data?.reconciliation;
  const summary = reconciliation?.summary;
  const thresholds = reconciliation?.thresholds_disclosed;
  const matchedRecords = reconciliation?.matched_records || [];
  const exceptions = reconciliation?.exceptions || [];
  const phase1Summary = data?.phase1;
  const groundTruthAccuracy = data?.ground_truth_accuracy;

  return (
    <div className="app-wrapper">
      {/* Top Navigation Bar */}
      <Navbar
        seed={seed}
        totalRecords={summary?.total_base_records || 60}
        loading={loading}
        onRegenerate={handleRegenerate}
        onExportCsv={handleExportCsv}
        onOpenNLQuery={() => setShowNLQuery(true)}
        onOpenAuditHistory={() => setShowAuditHistory(true)}
        onOpenUpload={() => setShowUpload(true)}
        currentView={viewMode}
        onToggleView={(mode) => setViewMode(mode)}
      />

      {/* Main Content Area */}
      {viewMode === 'landing' ? (
        <LandingPage
          onLaunchDashboard={() => setViewMode('dashboard')}
          onOpenUpload={() => setShowUpload(true)}
          onOpenNLQuery={() => setShowNLQuery(true)}
          data={data}
        />
      ) : (
        <>
          {/* Initial Loading Skeleton */}
          {!data && loading ? (
            <div style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '3rem 2rem',
              textAlign: 'center',
              color: 'var(--text-muted)'
            }}>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.6rem', fontSize: '0.85rem' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent)', display: 'inline-block' }} />
                <span>Initializing FinReconcile 3-Way Controller Engine...</span>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', animation: 'fadeIn 0.3s ease-out' }}>
              {/* KPI Header Bar */}
              <KPIHeader
                summary={summary}
                thresholds={thresholds}
                phase1Summary={phase1Summary}
                groundTruthAccuracy={groundTruthAccuracy}
              />

              {/* What-If Tolerance Simulation Panel */}
              <ToleranceControls
                dateTolerance={dateTolerance}
                setDateTolerance={setDateTolerance}
                feeTolerance={feeTolerance}
                setFeeTolerance={setFeeTolerance}
                onApply={handleApplyTolerances}
                loading={loading}
              />

              {/* Main Reconciliation & Audit Table */}
              <ReconciliationTable
                matchedRecords={matchedRecords}
                exceptions={exceptions}
                onSelectRow={(item) => setSelectedItem(item)}
              />
            </div>
          )}
        </>
      )}

      {/* Institutional Audit Footer Strip */}
      <footer style={{
        marginTop: '1rem',
        padding: '0.75rem 1rem',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '0.75rem',
        fontSize: '0.75rem',
        color: 'var(--text-muted)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--status-match)' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--status-match)', display: 'inline-block' }} />
            <span>Engine Active · Port 8000</span>
          </div>

          <span style={{ color: 'var(--border-medium)' }}>|</span>

          <span>AI: <strong style={{ color: 'var(--text-primary)', fontWeight: 500 }}>Google Gemini 3.6 Flash</strong> & HA Rule Fallback</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{ color: 'var(--text-dim)' }}>Tip: Press <kbd style={{ background: '#090b0e', border: '1px solid var(--border-subtle)', padding: '0.1rem 0.35rem', borderRadius: '3px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '0.7rem' }}>⌘K</kbd> for AI Query</span>
          <span style={{ color: 'var(--border-medium)' }}>|</span>
          <span>Zero False-Positive Audit Standard</span>
        </div>
      </footer>

      {/* Non-Intrusive Toast Feedback */}
      {toastMessage && (
        <div style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          background: '#161a22',
          border: '1px solid var(--border-medium)',
          color: 'var(--text-primary)',
          padding: '0.5rem 0.9rem',
          borderRadius: 'var(--radius-sm)',
          fontSize: '0.78rem',
          boxShadow: '0 10px 30px rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          zIndex: 2000,
          animation: 'fadeIn 0.2s ease'
        }}>
          <span>{toastMessage}</span>
        </div>
      )}

      {/* 3-Way Inspector Modal */}
      {selectedItem && (
        <InspectorModal
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
        />
      )}

      {/* Natural Language Query Modal */}
      {showNLQuery && (
        <NaturalLanguageQueryModal
          onClose={() => setShowNLQuery(false)}
          onSelectResult={(item) => setSelectedItem(item)}
        />
      )}

      {/* Audit History Modal */}
      {showAuditHistory && (
        <AuditHistoryModal
          onClose={() => setShowAuditHistory(false)}
          onSelectHistoricalRun={handleSelectHistoricalRun}
        />
      )}

      {/* Custom CSV Upload Modal */}
      {showUpload && (
        <UploadCSVModal
          onClose={() => setShowUpload(false)}
          onUploadSuccess={handleCustomUploadSuccess}
        />
      )}
    </div>
  );
}
