/**
 * LinkedIn Detail Page
 * ====================
 * Detailed view for the LinkedIn scraper module in Black & Yellow Theme.
 */

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import ProgressBar from '@/components/ProgressBar';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function LinkedinPage() {
  const [status, setStatus] = useState('idle');
  const [percentage, setPercentage] = useState(0);
  const [message, setMessage] = useState('');
  const [data, setData] = useState([]);
  const [totalRows, setTotalRows] = useState(0);

  // Search Parameters
  const [keywords, setKeywords] = useState('AI automation, AI chatbot, SaaS, web development, app development');
  const [location, setLocation] = useState('Worldwide');

  const fetchPreview = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/preview/linkedin?limit=50`);
      if (res.ok) {
        const json = await res.json();
        setData(json.data || []);
        setTotalRows(json.total_rows || 0);
      }
    } catch { /* API not reachable */ }
  }, []);

  useEffect(() => {
    fetchPreview();
  }, [fetchPreview]);

  // Poll status while running
  useEffect(() => {
    let interval;
    if (status === 'running') {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`${API_BASE}/api/status/linkedin`);
          const d = await res.json();
          setPercentage(d.percentage || 0);
          setMessage(d.message || '');
          if (d.status === 'completed') {
            setStatus('completed');
            setPercentage(100);
            fetchPreview();
          } else if (d.status === 'failed') {
            setStatus('failed');
            setMessage(d.error || 'Failed');
          }
        } catch { /* ignore */ }
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [status, fetchPreview]);
  const handleRun = async () => {
    if (!keywords) {
      alert('Please enter at least one keyword');
      return;
    }
    setStatus('running');
    setPercentage(0);
    setMessage('Initializing LinkedIn Scraper…');
    try {
      const url = `${API_BASE}/api/scrape/linkedin?keywords=${encodeURIComponent(keywords)}${location ? `&location=${encodeURIComponent(location)}` : ''}`;
      const res = await fetch(url, { method: 'POST' });
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
    window.open(`${API_BASE}/api/download/linkedin`, '_blank');
  };

  return (
    <div className="container-main" style={{ padding: '40px 24px 80px' }}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ marginBottom: '40px' }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '8px' }}>
          <div style={{
            width: '48px', height: '48px', borderRadius: '14px',
            background: 'rgba(255, 204, 0, 0.1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            border: '1px solid rgba(255, 204, 0, 0.2)',
          }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFCC00" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
              <rect x="2" y="9" width="4" height="12" />
              <circle cx="4" cy="4" r="2" />
            </svg>
          </div>
          <div>
            <h1 style={{ fontSize: '1.8rem', fontWeight: 800 }}>LinkedIn Jobs</h1>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Authenticate and scrape LinkedIn job listings with Selenium automation
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
          transition={{ delay: 0.1 }}
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
                placeholder="e.g. Worldwide, London, United States"
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  background: '#050505',
                  border: '1px solid rgba(255, 204, 0, 0.2)',
                  borderRadius: '8px',
                  color: '#FFF',
                  fontSize: '0.9rem'
                }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '6px' }}>Search Keywords (comma separated)</label>
              <textarea 
                value={keywords} 
                onChange={(e) => setKeywords(e.target.value)}
                placeholder="e.g. AI automation, SEO, Design"
                rows={2}
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  background: '#050505',
                  border: '1px solid rgba(255, 204, 0, 0.2)',
                  borderRadius: '8px',
                  color: '#FFF',
                  fontSize: '0.9rem',
                  resize: 'none',
                  fontFamily: 'inherit'
                }}
              />
            </div>
          </div>
        </motion.div>

        {/* Status Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="glass"
          style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}
        >
          <div style={{ display: 'flex', gap: '12px' }}>
            <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
              className="btn-primary" onClick={handleRun} disabled={status === 'running'}>
              <span>{status === 'running' ? 'Running…' : 'Run Scraper'}</span>
            </motion.button>
            <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
              className="btn-secondary" onClick={handleDownload} disabled={totalRows === 0}>
              Download CSV
            </motion.button>
          </div>
          <ProgressBar percentage={percentage} status={status} label={message} />
        </motion.div>
      </div>

    {/* Data Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="glass"
        style={{ padding: '4px', overflow: 'hidden' }}
      >
        <div style={{
          padding: '20px 24px 16px',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>
            Scraped Results
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 400, marginLeft: '8px' }}>
              ({totalRows} total)
            </span>
          </h3>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,215,0,0.1)' }}>
                {['Job Title', 'Company', 'Location', 'Posted Time', 'Keyword'].map((h) => (
                  <th key={h} style={{
                    padding: '12px 16px', textAlign: 'left', color: 'var(--text-muted)',
                    fontWeight: 600, fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.08em',
                    whiteSpace: 'nowrap',
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
                    No data yet. Run the scraper to collect leads.
                  </td>
                </tr>
              ) : (
                data.map((row, idx) => (
                  <motion.tr
                    key={idx}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: idx * 0.02 }}
                    style={{
                      borderBottom: '1px solid rgba(255,255,255,0.03)',
                      transition: 'background 0.2s',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 215, 0, 0.02)'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                  >
                    <td style={{ padding: '12px 16px', maxWidth: '250px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {row['Job Title'] || 'N/A'}
                    </td>
                    <td style={{ padding: '12px 16px', color: '#FFD700', fontWeight: 600 }}>
                      {row['Company'] || 'N/A'}
                    </td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-secondary)' }}>
                      {row['Location'] || 'N/A'}
                    </td>
                    <td style={{ padding: '12px 16px', color: 'var(--text-muted)' }}>
                      {row['Posted Time'] || 'N/A'}
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span style={{
                        padding: '2px 10px', borderRadius: '100px', fontSize: '0.7rem',
                        background: 'rgba(255, 204, 0, 0.1)', color: '#FFCC00',
                      }}>
                        {row['Keyword'] || ''}
                      </span>
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

LinkedinPage.pageTitle = 'DataScrap — LinkedIn Jobs';
