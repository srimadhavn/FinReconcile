import React, { useState } from 'react';
import { 
  X, 
  UploadCloud, 
  FileText, 
  Download, 
  CheckCircle2, 
  AlertCircle,
  Play,
  RotateCcw,
  Sparkles
} from 'lucide-react';
import axios from 'axios';

export default function UploadCSVModal({ onClose, onUploadSuccess }) {
  const [ledgerFile, setLedgerFile] = useState(null);
  const [bankFile, setBankFile] = useState(null);
  const [gatewayFile, setGatewayFile] = useState(null);
  
  const [dateTolerance, setDateTolerance] = useState(3);
  const [feeTolerance, setFeeTolerance] = useState(0.035);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Handle Download Templates
  const handleDownloadTemplate = (type) => {
    window.open(`/api/csv/template/${type}`, '_blank');
  };

  // Load Sample Demo Data into CSV Blobs for 1-Click Test
  const handleLoadSampleCSVs = async () => {
    try {
      setLoading(true);
      const res = await axios.get('/api/csv/templates');
      const templates = res.data;

      const ledgerBlob = new File([templates.ledger], "sample_general_ledger.csv", { type: "text/csv" });
      const bankBlob = new File([templates.bank], "sample_bank_statement.csv", { type: "text/csv" });
      const gatewayBlob = new File([templates.gateway], "sample_gateway_settlements.csv", { type: "text/csv" });

      setLedgerFile(ledgerBlob);
      setBankFile(bankBlob);
      setGatewayFile(gatewayBlob);
      setError(null);
    } catch (err) {
      console.error(err);
      setError("Failed to load sample templates.");
    } finally {
      setLoading(false);
    }
  };

  // Submit Upload to Backend
  const handleReconcileUpload = async () => {
    if (!ledgerFile && !bankFile && !gatewayFile) {
      setError("Please select or drop at least one CSV file to reconcile.");
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    if (ledgerFile) formData.append('ledger_file', ledgerFile);
    if (bankFile) formData.append('bank_file', bankFile);
    if (gatewayFile) formData.append('gateway_file', gatewayFile);
    formData.append('date_tolerance_days', dateTolerance);
    formData.append('fee_tolerance_pct', feeTolerance);

    try {
      const res = await axios.post('/api/upload/csv', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      onUploadSuccess(res.data);
      onClose();
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || "Failed to process and reconcile custom CSV files.");
    } finally {
      setLoading(false);
    }
  };

  const renderDropzone = (title, subtitle, file, setFile, templateType) => (
    <div style={{
      background: '#0a0c10',
      border: file ? '1px solid var(--status-match)' : '1px dashed var(--border-strong)',
      borderRadius: '6px',
      padding: '0.85rem 1rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.5rem',
      position: 'relative'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-hero)' }}>
            {title}
          </span>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginLeft: '0.5rem' }}>
            {subtitle}
          </span>
        </div>

        <button
          onClick={() => handleDownloadTemplate(templateType)}
          className="btn-ghost"
          style={{ padding: '0.15rem 0.45rem', fontSize: '0.68rem' }}
          title={`Download ${title} sample template`}
        >
          <Download size={11} />
          <span>Template</span>
        </button>
      </div>

      {file ? (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          background: '#13161c', 
          padding: '0.4rem 0.65rem', 
          borderRadius: '4px',
          border: '1px solid var(--border-subtle)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <FileText size={13} color="var(--status-match)" />
            <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-primary)' }}>
              {file.name}
            </span>
            <span style={{ fontSize: '0.68rem', color: 'var(--text-dim)' }}>
              ({(file.size / 1024).toFixed(1)} KB)
            </span>
          </div>

          <button
            onClick={() => setFile(null)}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center'
            }}
          >
            <X size={13} />
          </button>
        </div>
      ) : (
        <label style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.5rem',
          padding: '0.65rem',
          background: '#11141a',
          borderRadius: '4px',
          cursor: 'pointer',
          border: '1px solid var(--border-subtle)',
          transition: 'all 0.15s ease'
        }}>
          <UploadCloud size={14} color="var(--accent)" />
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Choose or drop {title} CSV
          </span>
          <input
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => e.target.files?.[0] && setFile(e.target.files[0])}
            style={{ display: 'none' }}
          />
        </label>
      )}
    </div>
  );

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0, 0, 0, 0.8)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '0.75rem'
    }}>
      <div style={{
        background: '#11141a',
        border: '1px solid var(--border-strong)',
        borderRadius: '8px',
        width: '100%',
        maxWidth: '680px',
        maxHeight: '90vh',
        overflowY: 'auto',
        boxShadow: '0 25px 60px rgba(0, 0, 0, 0.8)',
        padding: 'clamp(1rem, 3vw, 1.5rem)'
      }}>
        
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.85rem', marginBottom: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <UploadCloud size={16} color="var(--accent)" />
              <h2 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-hero)' }}>
                Upload Custom Reconciliation Dataset
              </h2>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Upload your own 3-way financial CSV files to run automated matching & AI exception auditing
            </div>
          </div>

          <button 
            onClick={onClose}
            style={{
              background: 'transparent',
              border: '1px solid var(--border-subtle)',
              borderRadius: '4px',
              width: '28px',
              height: '28px',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <X size={15} />
          </button>
        </div>

        {/* 1-Click Sample Preloader */}
        <div style={{
          background: 'rgba(99, 102, 241, 0.06)',
          border: '1px solid rgba(99, 102, 241, 0.2)',
          borderRadius: '6px',
          padding: '0.6rem 0.85rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '1rem',
          flexWrap: 'wrap',
          gap: '0.5rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.75rem', color: 'var(--text-primary)' }}>
            <Sparkles size={13} color="var(--accent)" />
            <span>Want to test custom upload quickly?</span>
          </div>

          <button
            onClick={handleLoadSampleCSVs}
            disabled={loading}
            className="btn-ghost"
            style={{ padding: '0.25rem 0.6rem', fontSize: '0.72rem', color: 'var(--accent)', borderColor: 'var(--accent)' }}
          >
            <span>Load Sample 3-Way CSVs</span>
          </button>
        </div>

        {/* Dropzones */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', marginBottom: '1rem' }}>
          {renderDropzone("1. General Ledger CSV", "(txn_id, date, amount, counterparty, reference)", ledgerFile, setLedgerFile, "ledger")}
          {renderDropzone("2. Bank Statement CSV", "(bank_txn_id, date, amount, narration, utr_reference)", bankFile, setBankFile, "bank")}
          {renderDropzone("3. Gateway Settlement CSV", "(payment_id, settlement_date, gross_amount, fee_deducted)", gatewayFile, setGatewayFile, "gateway")}
        </div>

        {/* Calibration Sliders */}
        <div style={{ background: '#0a0c10', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '0.75rem 1rem', marginBottom: '1rem' }}>
          <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            Matching Tolerances for this Upload:
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>
                <span>Date Lag Window:</span>
                <span className="mono" style={{ color: 'var(--text-primary)' }}>±{dateTolerance}d</span>
              </div>
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

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>
                <span>MDR Fee Tolerance:</span>
                <span className="mono" style={{ color: 'var(--text-primary)' }}>{(feeTolerance * 100).toFixed(1)}%</span>
              </div>
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
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--status-exception)', fontSize: '0.75rem', marginBottom: '0.75rem' }}>
            <AlertCircle size={13} />
            <span>{error}</span>
          </div>
        )}

        {/* Footer Actions */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.85rem' }}>
          <button 
            onClick={onClose}
            disabled={loading}
            className="btn-ghost"
          >
            Cancel
          </button>

          <button 
            onClick={handleReconcileUpload}
            disabled={loading || (!ledgerFile && !bankFile && !gatewayFile)}
            className="btn-primary"
            style={{ padding: '0.45rem 1rem' }}
          >
            <Play size={12} className={loading ? "animate-spin" : ""} />
            <span>{loading ? "Reconciling Upload..." : "Run 3-Way Reconciliation"}</span>
          </button>
        </div>

      </div>
    </div>
  );
}
