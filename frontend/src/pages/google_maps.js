/**
 * Google Maps Detail Page
 * =======================
 * Detailed view for the Google Maps scraper module.
 * Allows custom Location and Niche search with lead preview table.
 */

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import ProgressBar from '@/components/ProgressBar';
import { getApiUrl } from '@/utils/api';

const QUICK_NICHES = ['restaurants', 'gyms', 'marketing agencies', 'real estate', 'dentists', 'coworking spaces'];

export default function GoogleMapsPage() {
  const [status, setStatus] = useState('idle');
  const [percentage, setPercentage] = useState(0);
  const [message, setMessage] = useState('');
  const [data, setData] = useState([]);
  const [totalRows, setTotalRows] = useState(0);

  // Search Parameters
  const [location, setLocation] = useState('Dubai');
  const [niche, setNiche] = useState('gyms');

  const fetchPreview = useCallback(async () => {
    try {
      const res = await fetch(getApiUrl('/api/preview/google_maps?limit=50'));
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
          const res = await fetch(getApiUrl('/api/status/google_maps'));
          const d = await res.json();
          setPercentage(d.percentage || 0);
          setMessage(d.message || '');
          if (d.status === 'completed') { 
            setStatus('completed'); 
            setPercentage(100); 
            fetchPreview(); 
          }
          else if (d.status === 'failed') { 
            setStatus('failed'); 
            setMessage(d.error || 'Failed'); 
          }
        } catch { /* ignore */ }
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [status, fetchPreview]);

  const handleRun = async () => {
    if (!location || !niche) {
      alert('Please enter both location and niche');
      return;
    }
    setStatus('running'); 
    setPercentage(0); 
    setMessage('Initializing Google Maps Scraper…');
    try {
      const res = await fetch(getApiUrl(`/api/scrape/google_maps?location=${encodeURIComponent(location)}&niche=${encodeURIComponent(niche)}`), { 
        method: 'POST' 
      });
      if (!res.ok) { 
        const err = await res.json(); 
        throw new Error(err.detail); 
      }
    } catch (err) { 
      setStatus('failed'); 
      setMessage(err.message); 
    }
  };

  const handleDownload = () => { 
    window.open(getApiUrl('/api/download/google_maps'), '_blank');

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
            <h1 style={{ fontSize: '1.8rem', fontWeight: 800 }}>Google Maps Scraper</h1>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Harvest leads globally with custom location and niche queries
            </p>
          </div>
        </div>
      </motion.div>

      {/* Controls & Inputs */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
        {/* Search Parameters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="glass"
          style={{ padding: '24px' }}
        >
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>
            Search Configuration
          </span>
          <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '6px' }}>Target Location</label>
              <input 
                type="text" 
                value={location} 
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. Dubai, New York, London"
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  background: '#050505',
                  border: '1px solid rgba(255, 215, 0, 0.2)',
                  borderRadius: '8px',
                  color: '#FFF',
                  fontSize: '0.9rem'
                }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '6px' }}>Business Niche</label>
              <input 
                type="text" 
                value={niche} 
                onChange={(e) => setNiche(e.target.value)}
                placeholder="e.g. gym, restaurant, marketing"
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  background: '#050505',
                  border: '1px solid rgba(255, 215, 0, 0.2)',
                  borderRadius: '8px',
                  color: '#FFF',
                  fontSize: '0.9rem'
                }}
              />
            </div>
          </div>
        </motion.div>

        {/* Quick Niches & Action */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass"
          style={{ padding: '24px' }}
        >
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>
            Quick Niche Select
          </span>
          <div style={{ display: 'flex', gap: '8px', marginTop: '16px', flexWrap: 'wrap', minHeight: '80px' }}>
            {QUICK_NICHES.map((q) => (
              <button 
                key={q} 
                onClick={() => setNiche(q)}
                style={{
                  padding: '6px 14px',
                  borderRadius: '100px',
                  fontSize: '0.75rem',
                  background: niche === q ? 'rgba(255, 215, 0, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                  border: niche === q ? '1px solid #FFD700' : '1px solid rgba(255,255,255,0.1)',
                  color: niche === q ? '#FFD700' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  textTransform: 'capitalize'
                }}
              >
                {q}
              </button>
            ))}
          </div>
          <div style={{ marginTop: '24px', display: 'flex', gap: '12px' }}>
            <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
              className="btn-primary" onClick={handleRun} disabled={status === 'running'} style={{ flex: 1 }}>
              <span>{status === 'running' ? 'Running…' : 'Start Global Search'}</span>
            </motion.button>
            <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
              className="btn-secondary" onClick={handleDownload} disabled={totalRows === 0}>
              CSV
            </motion.button>
          </div>
        </motion.div>
      </div>

      {/* Progress */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="glass"
        style={{ padding: '20px 28px', marginBottom: '24px' }}
      >
        <ProgressBar percentage={percentage} status={status} label={message} />
      </motion.div>

      {/* Data Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="glass"
        style={{ padding: '4px', overflow: 'hidden' }}
      >
        <div style={{ padding: '20px 24px 16px', display: 'flex', justifyContent: 'space-between' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>
            Scraped Lead Results 
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 400, marginLeft: '8px' }}>
              ({totalRows} entries)
            </span>
          </h3>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,215,0,0.1)' }}>
                {['Business Name', 'Phone', 'Rating', 'Category', 'Email', 'Address'].map((h) => (
                  <th key={h} style={{
                    padding: '12px 16px', textAlign: 'left', color: 'var(--text-muted)',
                    fontWeight: 600, fontSize: '0.7rem', textTransform: 'uppercase',
                    letterSpacing: '0.08em', whiteSpace: 'nowrap',
                  }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    No results found. Perform a search to extract leads.
                  </td>
                </tr>
              ) : (
                data.map((row, idx) => (
                  <motion.tr key={idx} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: idx * 0.02 }}
                    style={{ borderBottom: '1px solid rgba(255,255,255,0.03)', transition: 'background 0.2s' }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 215, 0, 0.02)'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
                    <td style={{ padding: '12px 16px', maxWidth: '180px', fontWeight: 600, color: '#FFF' }}>
                      <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {row['Business Name'] || 'N/A'}
                      </div>
                    </td>
                    <td style={{ padding: '12px 16px', color: '#FFD700', fontVariantNumeric: 'tabular-nums' }}>
                      {row['Phone Number'] || 'N/A'}
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#FFCC00' }}>
                        <span>★</span>
                        <span>{row['Rating'] || '0'}</span>
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>({row['Reviews'] || '0'})</span>
                      </div>
                    </td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                      {row['Category'] || 'N/A'}
                    </td>
                    <td style={{ padding: '12px 16px', color: '#FFCC00', fontSize: '0.75rem' }}>
                      {row['Email'] || 'N/A'}
                    </td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-muted)', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {row['Full Address'] || 'N/A'}
                    </td>
                  </motion.tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  );
}

GoogleMapsPage.pageTitle = 'DataScrap — Google Maps';
