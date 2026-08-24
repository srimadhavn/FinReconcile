import React, { useState, useMemo } from 'react';
import { 
  Search, 
  ChevronRight, 
  ChevronLeft, 
  ArrowUpDown, 
  ArrowUp, 
  ArrowDown, 
  X
} from 'lucide-react';

export default function ReconciliationTable({ 
  matchedRecords, 
  exceptions, 
  onSelectRow 
}) {
  const [activeFilter, setActiveFilter] = useState('ALL'); // ALL, EXACT, FUZZY, EXCEPTIONS
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  
  // Sorting state
  const [sortField, setSortField] = useState('date');
  const [sortAsc, setSortAsc] = useState(false);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 15;

  // Standardize items for unified table display
  const exactItems = useMemo(() => (matchedRecords || [])
    .filter(m => m.confidence_tier === 'Exact')
    .map(m => ({
      rawType: 'MATCH',
      id: m.match_id,
      status: 'MATCHED_EXACT',
      confidenceTier: 'Exact',
      confidenceScore: m.confidence_score,
      amount: m.ledger?.amount || 0,
      date: m.ledger?.date || '',
      counterparty: m.ledger?.counterparty || 'Unknown',
      reference: m.ledger?.reference || '',
      narration: m.bank?.narration || '',
      discrepancies: m.discrepancies || [],
      reasoning: m.reasoning,
      raw: m
    })), [matchedRecords]);

  const fuzzyItems = useMemo(() => (matchedRecords || [])
    .filter(m => m.confidence_tier !== 'Exact')
    .map(m => ({
      rawType: 'MATCH',
      id: m.match_id,
      status: 'MATCHED_FUZZY',
      confidenceTier: m.confidence_tier || 'High',
      confidenceScore: m.confidence_score,
      amount: m.ledger?.amount || 0,
      date: m.ledger?.date || '',
      counterparty: m.ledger?.counterparty || 'Unknown',
      reference: m.ledger?.reference || '',
      narration: m.bank?.narration || '',
      discrepancies: m.discrepancies || [],
      reasoning: m.reasoning,
      raw: m
    })), [matchedRecords]);

  const exceptionItems = useMemo(() => (exceptions || []).map(e => ({
    rawType: 'EXCEPTION',
    id: e.id,
    status: 'EXCEPTION',
    category: e.category,
    confidenceTier: 'Unresolved',
    confidenceScore: e.ai_confidence,
    amount: e.amount || 0,
    date: e.date || '',
    counterparty: e.counterparty || 'Flagged Entity',
    reference: e.reference || '',
    narration: e.raw_record?.narration || '',
    discrepancies: [e.category],
    reasoning: e.plain_english_explanation,
    raw: e
  })), [exceptions]);

  // Filter list
  const filteredList = useMemo(() => {
    let list = [];
    if (activeFilter === 'ALL') {
      list = [...exactItems, ...fuzzyItems, ...exceptionItems];
    } else if (activeFilter === 'EXACT') {
      list = exactItems;
    } else if (activeFilter === 'FUZZY') {
      list = fuzzyItems;
    } else if (activeFilter === 'EXCEPTIONS') {
      list = exceptionItems;
    }

    if (categoryFilter !== 'ALL') {
      list = list.filter(item => item.category === categoryFilter || item.discrepancies.includes(categoryFilter));
    }

    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      list = list.filter(item => (
        (item.id || '').toLowerCase().includes(q) ||
        (item.counterparty || '').toLowerCase().includes(q) ||
        (item.reference || '').toLowerCase().includes(q) ||
        (item.reasoning && item.reasoning.toLowerCase().includes(q)) ||
        (item.amount != null ? item.amount.toString() : '').includes(q)
      ));
    }

    // Sort list
    return list.sort((a, b) => {
      let aVal = a[sortField];
      let bVal = b[sortField];
      if (sortField === 'amount') {
        aVal = Number(aVal || 0);
        bVal = Number(bVal || 0);
      }
      if (aVal < bVal) return sortAsc ? -1 : 1;
      if (aVal > bVal) return sortAsc ? 1 : -1;
      return 0;
    });
  }, [activeFilter, categoryFilter, searchTerm, exactItems, fuzzyItems, exceptionItems, sortField, sortAsc]);

  // Paginated slice
  const totalPages = Math.max(1, Math.ceil(filteredList.length / pageSize));
  const currentPageClamped = Math.min(currentPage, totalPages);
  const paginatedList = useMemo(() => {
    const start = (currentPageClamped - 1) * pageSize;
    return filteredList.slice(start, start + pageSize);
  }, [filteredList, currentPageClamped]);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  const exceptionCategories = Array.from(new Set(exceptionItems.map(e => e.category).filter(Boolean)));

  const renderSortIcon = (field) => {
    if (sortField !== field) {
      return <ArrowUpDown size={11} color="var(--text-dim)" style={{ marginLeft: '4px' }} />;
    }
    return sortAsc 
      ? <ArrowUp size={11} color="var(--text-primary)" style={{ marginLeft: '4px' }} />
      : <ArrowDown size={11} color="var(--text-primary)" style={{ marginLeft: '4px' }} />;
  };

  return (
    <div className="table-card">
      
      {/* Filter Tabs & Search Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '0.75rem',
        padding: '0.75rem 1.15rem',
        borderBottom: '1px solid var(--border-subtle)',
        background: '#0b0e12'
      }}>
        
        {/* Modern Pill Tabs */}
        <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
          <button
            onClick={() => { setActiveFilter('ALL'); setCategoryFilter('ALL'); setCurrentPage(1); }}
            style={{
              background: activeFilter === 'ALL' ? '#181c24' : 'transparent',
              color: activeFilter === 'ALL' ? 'var(--text-hero)' : 'var(--text-muted)',
              border: '1px solid',
              borderColor: activeFilter === 'ALL' ? 'var(--border-medium)' : 'transparent',
              borderRadius: 'var(--radius-sm)',
              padding: '0.3rem 0.65rem',
              fontSize: '0.75rem',
              fontWeight: 500,
              cursor: 'pointer'
            }}
          >
            All <span className="mono" style={{ opacity: 0.6 }}>({exactItems.length + fuzzyItems.length + exceptionItems.length})</span>
          </button>
          
          <button
            onClick={() => { setActiveFilter('EXACT'); setCategoryFilter('ALL'); setCurrentPage(1); }}
            style={{
              background: activeFilter === 'EXACT' ? '#181c24' : 'transparent',
              color: activeFilter === 'EXACT' ? 'var(--status-match)' : 'var(--text-muted)',
              border: '1px solid',
              borderColor: activeFilter === 'EXACT' ? 'var(--border-medium)' : 'transparent',
              borderRadius: 'var(--radius-sm)',
              padding: '0.3rem 0.65rem',
              fontSize: '0.75rem',
              fontWeight: 500,
              cursor: 'pointer'
            }}
          >
            Exact <span className="mono" style={{ opacity: 0.6 }}>({exactItems.length})</span>
          </button>
          
          <button
            onClick={() => { setActiveFilter('FUZZY'); setCategoryFilter('ALL'); setCurrentPage(1); }}
            style={{
              background: activeFilter === 'FUZZY' ? '#181c24' : 'transparent',
              color: activeFilter === 'FUZZY' ? 'var(--status-fuzzy)' : 'var(--text-muted)',
              border: '1px solid',
              borderColor: activeFilter === 'FUZZY' ? 'var(--border-medium)' : 'transparent',
              borderRadius: 'var(--radius-sm)',
              padding: '0.3rem 0.65rem',
              fontSize: '0.75rem',
              fontWeight: 500,
              cursor: 'pointer'
            }}
          >
            Fuzzy <span className="mono" style={{ opacity: 0.6 }}>({fuzzyItems.length})</span>
          </button>
          
          <button
            onClick={() => { setActiveFilter('EXCEPTIONS'); setCurrentPage(1); }}
            style={{
              background: activeFilter === 'EXCEPTIONS' ? '#181c24' : 'transparent',
              color: activeFilter === 'EXCEPTIONS' ? 'var(--status-exception)' : 'var(--text-muted)',
              border: '1px solid',
              borderColor: activeFilter === 'EXCEPTIONS' ? 'var(--border-medium)' : 'transparent',
              borderRadius: 'var(--radius-sm)',
              padding: '0.3rem 0.65rem',
              fontSize: '0.75rem',
              fontWeight: 500,
              cursor: 'pointer'
            }}
          >
            Exceptions <span className="mono" style={{ opacity: 0.6 }}>({exceptionItems.length})</span>
          </button>
        </div>

        {/* Search & Category Filter */}
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap', flex: 1, justifyContent: 'flex-end' }}>
          {activeFilter === 'EXCEPTIONS' && exceptionCategories.length > 0 && (
            <select
              value={categoryFilter}
              onChange={(e) => { setCategoryFilter(e.target.value); setCurrentPage(1); }}
              style={{
                background: '#13161c',
                color: 'var(--text-muted)',
                border: '1px solid var(--border-subtle)',
                padding: '0.3rem 0.6rem',
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.75rem',
                outline: 'none',
                maxWidth: '180px'
              }}
            >
              <option value="ALL">All Categories</option>
              {exceptionCategories.map(cat => (
                <option key={cat} value={cat}>{cat.replace(/_/g, ' ')}</option>
              ))}
            </select>
          )}

          <div style={{ position: 'relative', width: 'clamp(170px, 22vw, 230px)' }}>
            <Search size={13} color="var(--text-dim)" style={{ position: 'absolute', left: '9px', top: '9px' }} />
            <input
              type="text"
              placeholder="Search reference, party..."
              value={searchTerm}
              onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1); }}
              style={{
                width: '100%',
                background: '#13161c',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.35rem 1.8rem 0.35rem 1.85rem',
                color: 'var(--text-primary)',
                fontSize: '0.75rem',
                outline: 'none'
              }}
            />
            {searchTerm && (
              <X 
                size={12} 
                color="var(--text-muted)" 
                style={{ position: 'absolute', right: '8px', top: '9px', cursor: 'pointer' }} 
                onClick={() => setSearchTerm('')}
              />
            )}
          </div>
        </div>

      </div>

      {/* High-Legibility Table */}
      <div style={{ overflowX: 'auto', WebkitOverflowScrolling: 'touch' }}>
        <table className="fin-table" style={{ minWidth: '760px' }}>
          <thead>
            <tr>
              <th style={{ width: '135px', cursor: 'pointer' }} onClick={() => handleSort('id')}>
                <div style={{ display: 'inline-flex', alignItems: 'center' }}>
                  ID {renderSortIcon('id')}
                </div>
              </th>
              
              <th style={{ width: '150px', cursor: 'pointer' }} onClick={() => handleSort('status')}>
                <div style={{ display: 'inline-flex', alignItems: 'center' }}>
                  Status {renderSortIcon('status')}
                </div>
              </th>
              
              <th style={{ width: '95px', cursor: 'pointer' }} onClick={() => handleSort('date')}>
                <div style={{ display: 'inline-flex', alignItems: 'center' }}>
                  Date {renderSortIcon('date')}
                </div>
              </th>
              
              <th style={{ width: '130px', textAlign: 'right', cursor: 'pointer' }} onClick={() => handleSort('amount')}>
                <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'flex-end', width: '100%' }}>
                  Amount {renderSortIcon('amount')}
                </div>
              </th>
              
              <th style={{ width: '185px' }}>Counterparty & Ref</th>
              <th>Audit Reasoning & Field Citations</th>
              <th style={{ width: '65px', textAlign: 'center' }}></th>
            </tr>
          </thead>
          <tbody>
            {paginatedList.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-dim)' }}>
                  No records match the current filter or search.
                </td>
              </tr>
            ) : (
              paginatedList.map((item, idx) => (
                <tr 
                  key={item.id + idx}
                  style={{ cursor: 'pointer' }}
                  onClick={() => onSelectRow(item.raw)}
                >
                  {/* Transaction ID */}
                  <td>
                    <span className="mono" style={{ fontSize: '0.78rem', color: 'var(--text-hero)', whiteSpace: 'nowrap', fontWeight: 500 }}>
                      {item.id}
                    </span>
                  </td>

                  {/* Status Indicator */}
                  <td>
                    {item.status === 'MATCHED_EXACT' && (
                      <span className="status-indicator match">
                        <span className="status-dot match" />
                        <span>Exact 1.00</span>
                      </span>
                    )}
                    {item.status === 'MATCHED_FUZZY' && (
                      <span className="status-indicator fuzzy">
                        <span className="status-dot fuzzy" />
                        <span>Fuzzy ({typeof item.confidenceScore === 'number' ? (item.confidenceScore * 100).toFixed(0) : '85'}%)</span>
                      </span>
                    )}
                    {item.status === 'EXCEPTION' && (
                      <span className="status-indicator exception" title={item.category}>
                        <span className="status-dot exception" />
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '120px' }}>
                          {item.category ? item.category.replace(/_/g, ' ') : 'Exception'}
                        </span>
                      </span>
                    )}
                  </td>

                  {/* Date */}
                  <td>
                    <span className="mono" style={{ fontSize: '0.78rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                      {item.date || '—'}
                    </span>
                  </td>

                  {/* Amount */}
                  <td style={{ textAlign: 'right' }}>
                    <span className="mono" style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-hero)', whiteSpace: 'nowrap' }}>
                      ₹{Number(item.amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                  </td>

                  {/* Counterparty & Ref */}
                  <td>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-primary)', fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '175px' }}>
                      {item.counterparty}
                    </div>
                    <div className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-dim)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '175px' }}>
                      {item.reference}
                    </div>
                  </td>

                  {/* AI Audit Reasoning */}
                  <td>
                    <div style={{
                      fontSize: '0.75rem',
                      color: item.status === 'EXCEPTION' ? 'var(--text-primary)' : 'var(--text-muted)',
                      lineHeight: '1.4',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      maxWidth: 'clamp(200px, 32vw, 480px)'
                    }}>
                      {item.reasoning}
                    </div>
                  </td>

                  {/* Inspect Button */}
                  <td style={{ textAlign: 'center' }}>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectRow(item.raw);
                      }}
                      className="btn-ghost"
                      style={{ padding: '0.2rem 0.5rem', fontSize: '0.72rem' }}
                      title="Inspect 3-way discrepancy details"
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '0.7rem 1.15rem',
        borderTop: '1px solid var(--border-subtle)',
        fontSize: '0.75rem',
        color: 'var(--text-muted)',
        background: '#0b0e12',
        flexWrap: 'wrap',
        gap: '0.5rem'
      }}>
        <div>
          Showing <span className="mono" style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
            {filteredList.length === 0 ? 0 : (currentPageClamped - 1) * pageSize + 1}–{Math.min(currentPageClamped * pageSize, filteredList.length)}
          </span> of <span className="mono" style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{filteredList.length}</span> records
        </div>

        {totalPages > 1 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPageClamped === 1}
              className="btn-ghost"
              style={{ padding: '0.2rem 0.5rem', fontSize: '0.72rem', opacity: currentPageClamped === 1 ? 0.4 : 1 }}
            >
              <ChevronLeft size={13} />
              <span>Prev</span>
            </button>

            <span className="mono" style={{ fontSize: '0.72rem', padding: '0 0.4rem' }}>
              Page {currentPageClamped} of {totalPages}
            </span>

            <button
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPageClamped === totalPages}
              className="btn-ghost"
              style={{ padding: '0.2rem 0.5rem', fontSize: '0.72rem', opacity: currentPageClamped === totalPages ? 0.4 : 1 }}
            >
              <span>Next</span>
              <ChevronRight size={13} />
            </button>
          </div>
        )}
      </div>

    </div>
  );
}
