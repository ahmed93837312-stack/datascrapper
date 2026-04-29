/**
 * Directories Detail Page
 * =======================
 * Detailed view for the Local Directories scraper module in Black & Yellow Theme.
 */

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import ProgressBar from '@/components/ProgressBar';
import { getApiUrl } from '@/utils/api';

export default function DirectoriesPage() {
  const [status, setStatus] = useState('idle');
  const [percentage, setPercentage] = useState(0);
  const [message, setMessage] = useState('');
  const [data, setData] = useState([]);
  const [totalRows, setTotalRows] = useState(0);

  // Search Parameters
  const [niches, setNiches] = useState('logistics, retail, healthcare, education');

  const fetchPreview = useCallback(async () => {
    try {
      const res = await fetch(getApiUrl('/api/preview/directories?limit=50'));
      if (res.ok) {
        const json = await res.json();
        setData(json.data || []);
        setTotalRows(json.total_rows || 0);
      }
    } catch { /* API not reachable */ }
  }, []);

  useEffect(() => { fetchPreview(); }, [fetchPreview]);

  useEffect(() => {
    let interval;
    if (status === 'running') {
      interval = setInterval(async () => {
        try {
          const res = await fetch(getApiUrl('/api/status/directories'));
          const d = await res.json();
          setPercentage(d.percentage || 0);
          setMessage(d.message || '');
          if (d.status === 'completed') { setStatus('completed'); setPercentage(100); fetchPreview(); }
          else if (d.status === 'failed') { setStatus('failed'); setMessage(d.error || 'Failed'); }
        } catch { /* ignore */ }
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [status, fetchPreview]);

  const handleRun = async () => {
    if (!niches) {
      alert('Please enter at least one niche');
      return;
    }
    setStatus('running'); setPercentage(0); setMessage('Initializing Directories Scraper…');
    try {
      const res = await fetch(getApiUrl(`/api/scrape/directories?niches=${encodeURIComponent(niches)}`), { 
        method: 'POST' 
      });
      if (!res.ok) { const err = await res.json(); throw new Error(err.detail); }
    } catch (err) { setStatus('failed'); setMessage(err.message); }
  };

  const handleDownload = () => { window.open(getApiUrl('/api/download/directories'), '_blank'); };

  // Calculate source breakdown from data
  const sourceCounts = data.reduce((acc, row) => {
    const src = row['Source'] || 'Unknown';
    acc[src] = (acc[src] || 0) + 1;
    return acc;
  }, {});

  const sourceColors = {
    'YellowPages': '#FFD700',
    'Yelp': '#FFCC00',
    'Canada411': '#CCAA00',
    'Unknown': '#6b7280',
  };

  return (
    <div className="container-main" style={{ padding: '40px 24px 80px' }}>
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: '40px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '8px' }}>
          <div style={{
            width: '48px', height: '48px', borderRadius: '14px',
            background: 'rgba(255, 215, 0, 0.1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            border: '1px solid rgba(255, 215, 0, 0.2)',
          }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFD700" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
              <circle cx="12" cy="10" r="3" />
            </svg>
          </div>
          <div>
            <h1 style={{ fontSize: '1.8rem', fontWeight: 800 }}>Local Directories</h1>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Yellow Pages, Yelp, and Canada411 business listings
            </p>
          </div>
        </div>
      </motion.div>

      {/* Source breakdown + Controls */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
        {/* Sources */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="glass"
          style={{ padding: '24px' }}
        >
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>
            Target Sources
          </span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '16px' }}>
            {[
              { name: 'Yellow Pages', region: 'U.S.', color: '#FFD700' },
              { name: 'Yelp', region: 'U.S.', color: '#FFCC00' },
              { name: 'Canada411', region: 'Canada', color: '#CCAA00' },
            ].map((src) => (
              <div key={src.name} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: src.color }} />
                  <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>{src.name}</span>
                  <span style={{
                    fontSize: '0.65rem', padding: '2px 8px', borderRadius: '100px',
                    background: 'rgba(255,255,255,0.05)', color: 'var(--text-muted)',
                  }}>
                    {src.region}
                  </span>
                </div>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: src.color, fontVariantNumeric: 'tabular-nums' }}>
                  {sourceCounts[src.name] || 0}
                </span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Search Parameters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass"
          style={{ padding: '24px' }}
        >
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>
            Search Configuration
          </span>
          <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '6px' }}>Target Niches (comma separated)</label>
              <textarea 
                value={niches} 
                onChange={(e) => setNiches(e.target.value)}
                placeholder="e.g. logistics, retail, real estate"
                rows={2}
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  background: '#050505',
                  border: '1px solid rgba(255, 215, 0, 0.2)',
                  borderRadius: '8px',
                  color: '#FFF',
                  fontSize: '0.9rem',
                  resize: 'none',
                  fontFamily: 'inherit'
                }}
              />
            </div>
            
            <div style={{ display: 'flex', gap: '12px', marginTop: '4px' }}>
              <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                className="btn-primary" onClick={handleRun} disabled={status === 'running'}>
                <span>{status === 'running' ? 'Running…' : 'Run Scraper'}</span>
              </motion.button>
              <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                className="btn-secondary" onClick={handleDownload} disabled={totalRows === 0}>
                Download CSV
              </motion.button>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Status Alert */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="glass"
        style={{ padding: '24px', marginBottom: '24px' }}
      >
        <ProgressBar percentage={percentage} status={status} label={message} />
      </motion.div>

      {/* Data Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
        className="glass"
        style={{ padding: '4px', overflow: 'hidden' }}
      >
        <div style={{ padding: '20px 24px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>
            Live Lead Preview
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 400, marginLeft: '8px' }}>
              ({totalRows} total records)
            </span>
          </h3>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,215,0,0.1)' }}>
                {['Business Name', 'Phone', 'Website', 'Location', 'Source'].map((h) => (
                  <th key={h} style={{
                    padding: '12px 16px', textAlign: 'left', color: 'var(--text-muted)',
                    fontWeight: 600, fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.08em',
                  }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    No leads found yet. Start the scraper to populate this list.
                  </td>
                </tr>
              ) : (
                data.map((row, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <td style={{ padding: '12px 16px', fontWeight: 600 }}>{row['Business Name'] || 'N/A'}</td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>{row['Phone'] || 'N/A'}</td>
                    <td style={{ padding: '12px 16px' }}>
                      {row['Website'] && row['Website'] !== 'N/A' ? (
                        <a href={row['Website']} target="_blank" rel="noreferrer" style={{ color: '#FFD700', textDecoration: 'none' }}>
                          Visit Site
                        </a>
                      ) : 'N/A'}
                    </td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-muted)', fontSize: '0.75rem' }}>{row['Location'] || 'N/A'}</td>
                    <td style={{ padding: '12px 16px' }}>
                      <span style={{
                        padding: '2px 10px', borderRadius: '100px', fontSize: '0.65rem',
                        background: 'rgba(255, 215, 0, 0.1)', color: sourceColors[row['Source']] || '#FFD700',
                        border: `1px solid ${sourceColors[row['Source']] || 'rgba(255, 215, 0, 0.2)'}`,
                      }}>
                        {row['Source'] || 'Unknown'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  );
}

DirectoriesPage.pageTitle = 'DataScrap — Local Directories';
