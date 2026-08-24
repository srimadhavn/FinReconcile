import React from 'react';
import { 
  X, 
  Receipt,
  Building2,
  CreditCard,
  Lock,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';

export default function InspectorModal({ item, onClose }) {
  if (!item) return null;

  const isException = !!item.category || item.status === 'UNRESOLVED';
  
  // Extract records for 3-way comparison
  let ledger = item.ledger || (item.source === 'Ledger' ? item.raw_record : null);
  let bank = item.bank || (item.source === 'Bank Statement' ? item.raw_record : null);
  let gateway = item.gateway || (item.source === 'Gateway Settlement' ? item.raw_record : null);

  const confidencePct = item.confidence_score 
    ? (item.confidence_score * 100).toFixed(0) 
    : (item.ai_confidence ? (item.ai_confidence * 100).toFixed(0) : '100');

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
        maxWidth: '880px',
        maxHeight: '90vh',
        overflowY: 'auto',
        boxShadow: '0 25px 60px rgba(0, 0, 0, 0.8)',
        padding: 'clamp(1rem, 3vw, 1.5rem)'
      }}>
        
        {/* Modal Header */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'flex-start', 
          borderBottom: '1px solid var(--border-subtle)', 
          paddingBottom: '0.85rem', 
          marginBottom: '1rem',
          gap: '0.5rem'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
              <span className="mono" style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-hero)' }}>
                {item.match_id || item.id}
              </span>
              
              {isException ? (
                <span className="status-indicator exception" style={{ fontSize: '0.78rem' }}>
                  <span className="status-dot exception" />
                  <span>{item.category ? item.category.replace(/_/g, ' ') : 'Unresolved Exception'}</span>
                </span>
              ) : (
                <span className="status-indicator match" style={{ fontSize: '0.78rem' }}>
                  <span className="status-dot match" />
                  <span>{item.confidence_tier || 'Matched'} ({confidencePct}%)</span>
                </span>
              )}
            </div>
            
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
              3-Way Multi-Source Audit Inspection & Discrepancy Decomposition
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
              justifyContent: 'center',
              flexShrink: 0
            }}
          >
            <X size={15} />
          </button>
        </div>

        {/* 3-Way Side-by-Side Verification Columns */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', 
          gap: '0.75rem', 
          marginBottom: '1rem' 
        }}>
          
          {/* Source 1: General Ledger */}
          <div style={{ background: '#0a0c10', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '0.85rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.65rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.4rem' }}>
              <Receipt size={13} color="var(--text-muted)" />
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                1. General Ledger
              </span>
            </div>

            {ledger ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', fontSize: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Txn ID:</span>
                  <span className="mono" style={{ color: 'var(--text-primary)' }}>{ledger.txn_id}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Date:</span>
                  <span className="mono" style={{ color: 'var(--text-primary)' }}>{ledger.date}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Amount:</span>
                  <span className="mono" style={{ fontWeight: 600, color: 'var(--text-hero)' }}>
                    ₹{Number(ledger.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Counterparty:</span>
                  <span style={{ color: 'var(--text-primary)' }}>{ledger.counterparty}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Reference:</span>
                  <span className="mono" style={{ color: 'var(--text-muted)' }}>{ledger.reference}</span>
                </div>
              </div>
            ) : (
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontStyle: 'italic', padding: '0.5rem 0' }}>
                No matching Ledger entry found.
              </div>
            )}
          </div>

          {/* Source 2: Bank Statement */}
          <div style={{ background: '#0a0c10', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '0.85rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.65rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.4rem' }}>
              <Building2 size={13} color="var(--text-muted)" />
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                2. Bank Statement
              </span>
            </div>

            {bank ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', fontSize: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Bank Ref:</span>
                  <span className="mono" style={{ color: 'var(--text-primary)' }}>{bank.bank_txn_id}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Date:</span>
                  <span className="mono" style={{ color: 'var(--text-primary)' }}>{bank.date}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Amount:</span>
                  <span className="mono" style={{ fontWeight: 600, color: 'var(--text-hero)' }}>
                    ₹{Number(bank.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>UTR Ref:</span>
                  <span className="mono" style={{ color: 'var(--text-muted)' }}>{bank.utr_reference}</span>
                </div>
                <div style={{ marginTop: '0.15rem' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Narration:</div>
                  <div className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)', wordBreak: 'break-all' }}>
                    {bank.narration}
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontStyle: 'italic', padding: '0.5rem 0' }}>
                No matching Bank credit found.
              </div>
            )}
          </div>

          {/* Source 3: Gateway Settlement */}
          <div style={{ background: '#0a0c10', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '0.85rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.65rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.4rem' }}>
              <CreditCard size={13} color="var(--text-muted)" />
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                3. Gateway Settlement
              </span>
            </div>

            {gateway ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', fontSize: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Payment ID:</span>
                  <span className="mono" style={{ color: 'var(--text-primary)' }}>{gateway.payment_id}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Settled Date:</span>
                  <span className="mono" style={{ color: 'var(--text-primary)' }}>{gateway.settlement_date}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Gross:</span>
                  <span className="mono" style={{ color: 'var(--text-primary)' }}>
                    ₹{Number(gateway.gross_amount || gateway.amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Fee Deducted:</span>
                  <span className="mono" style={{ color: 'var(--status-fuzzy)' }}>
                    ₹{Number(gateway.fee_deducted || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Net Settled:</span>
                  <span className="mono" style={{ fontWeight: 600, color: 'var(--text-hero)' }}>
                    ₹{Number(gateway.settled_amount || gateway.amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                </div>
              </div>
            ) : (
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontStyle: 'italic', padding: '0.5rem 0' }}>
                No matching Gateway record found.
              </div>
            )}
          </div>

        </div>

        {/* Audit Reasoning & Remediation Box */}
        <div style={{ background: '#0a0c10', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '0.85rem' }}>
          
          <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
            Audit Reasoning & Cited Discrepancies
          </div>

          <div style={{ fontSize: '0.78rem', color: 'var(--text-primary)', lineHeight: '1.5', marginBottom: '0.65rem' }}>
            {item.plain_english_explanation || item.reasoning}
          </div>

          {/* Remediation */}
          {item.remediation_suggestion && (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', background: '#11141a', padding: '0.5rem 0.65rem', borderRadius: '4px', border: '1px solid var(--border-subtle)', marginBottom: '0.65rem' }}>
              <strong style={{ color: 'var(--text-primary)' }}>Recommended Action: </strong>
              <span>{item.remediation_suggestion}</span>
            </div>
          )}

          {/* Cited fields */}
          {item.cited_fields && (
            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginBottom: '0.5rem' }}>
              <span>Cited Fields: </span>
              <span className="mono" style={{ color: 'var(--text-muted)' }}>{item.cited_fields}</span>
            </div>
          )}

          {/* Guardrail & Engine Strip */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem', paddingTop: '0.5rem', borderTop: '1px solid var(--border-subtle)', fontSize: '0.72rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--text-dim)' }}>
              <Lock size={12} color="var(--status-exception)" />
              <span>Strict Unresolved — Guardrail protected (0 FP standard)</span>
            </div>

            {item.llm_engine && (
              <span className="mono" style={{ color: 'var(--text-dim)', fontSize: '0.7rem' }}>
                Engine: {item.llm_engine}
              </span>
            )}
          </div>

        </div>

      </div>
    </div>
  );
}
