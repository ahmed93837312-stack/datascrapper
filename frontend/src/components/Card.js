/**
 * Card Component
 * ==============
 * Scraper card with 3D hover effects, run/download buttons,
 * progress indicator, and lead count display in Black & Yellow theme.
 */

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import ProgressBar from './ProgressBar';

const API_BASE = 'http://localhost:8000';

// Card accent colors per module (All unified to Yellow theme under the hood but with subtle variance)
const moduleThemes = {
  upwork: {
    glow: 'rgba(255, 215, 0, 0.08)',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#FFD700" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
        <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
      </svg>
    ),
  },
  linkedin: {
    glow: 'rgba(255, 204, 0, 0.08)',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#FFCC00" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
        <rect x="2" y="9" width="4" height="12" />
        <circle cx="4" cy="4" r="2" />
      </svg>
    ),
  },
  directories: {
    glow: 'rgba(255, 215, 0, 0.06)',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#FFD700" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
        <circle cx="12" cy="10" r="3" />
      </svg>
    ),
  },
  google_maps: {
    glow: 'rgba(255, 215, 0, 0.12)',
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#FFD700" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
        <path d="M12 7v6l4 2" />
        <circle cx="12" cy="10" r="10" />
      </svg>
    ),
  },
};

const moduleLabels = {
  upwork: 'Upwork Jobs',
  linkedin: 'LinkedIn Jobs',
  directories: 'Local Directories',
  google_maps: 'Google Maps',
};

const moduleDescriptions = {
  upwork: 'Scrape AI, SaaS, and development job postings from Upwork.',
  linkedin: 'Authenticate and scrape LinkedIn job listings with Selenium.',
  directories: 'Extract business listings from Yellow Pages, Yelp, and Canada411.',
  google_maps: 'Scrape business leads from Google Maps with email harvesting.',
};

export default function Card({ module, leads = 0, lastRun = null, onStatsUpdate }) {
  const [status, setStatus] = useState('idle');
  const [percentage, setPercentage] = useState(0);
  const [message, setMessage] = useState('');
  const [isHovered, setIsHovered] = useState(false);

  const theme = moduleThemes[module] || moduleThemes.upwork;
  const label = moduleLabels[module] || module;
  const description = moduleDescriptions[module] || '';

  // Poll status while running
  useEffect(() => {
    let interval;
    if (status === 'running') {
      interval = setInterval(async () => {
        try {
          const res = await fetch(`${API_BASE}/api/status/${module}`);
          const data = await res.json();
          setPercentage(data.percentage || 0);
          setMessage(data.message || '');

          if (data.status === 'completed') {
            setStatus('completed');
            setPercentage(100);
            setMessage('Scraping completed successfully');
            if (onStatsUpdate) onStatsUpdate();
          } else if (data.status === 'failed') {
            setStatus('failed');
            setMessage(data.error || 'Scraping failed');
          }
        } catch {
          // API not reachable — keep polling
        }
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [status, module, onStatsUpdate]);

  const handleRunScraper = useCallback(async () => {
    setStatus('running');
    setPercentage(0);
    setMessage('Initializing…');

    try {
      const res = await fetch(`${API_BASE}/api/scrape/${module}`, { method: 'POST' });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to start scraper');
      }
    } catch (err) {
      setStatus('failed');
      setMessage(err.message);
    }
  }, [module]);

  const handleDownload = useCallback(() => {
    window.open(`${API_BASE}/api/download/${module}`, '_blank');
  }, [module]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      style={{ perspective: '1000px' }}
    >
      <motion.div
        animate={{
          rotateX: isHovered ? -2 : 0,
          rotateY: isHovered ? 2 : 0,
          scale: isHovered ? 1.01 : 1,
        }}
        transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
        className="glass glass-hover"
        style={{
          padding: '32px',
          display: 'flex',
          flexDirection: 'column',
          gap: '24px',
          position: 'relative',
          overflow: 'hidden',
          transformStyle: 'preserve-3d',
        }}
      >
        {/* Subtle yellow top border accent */}
        <div style={{
           position: 'absolute', top: 0, left: 0, right: 0, height: '2px',
           background: 'linear-gradient(90deg, #FFD700, #FFCC00)'
        }} />

        {/* Glow accent in top-right corner */}
        <div
          style={{
            position: 'absolute',
            top: '-40px',
            right: '-40px',
            width: '120px',
            height: '120px',
            borderRadius: '50%',
            background: theme.glow,
            filter: 'blur(40px)',
            pointerEvents: 'none',
          }}
        />

        {/* Header row */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            {/* Icon container */}
            <div style={{
              width: '52px',
              height: '52px',
              borderRadius: '14px',
              background: 'rgba(255,215,0,0.05)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '1px solid rgba(255,215,0,0.2)',
            }}>
              {theme.icon}
            </div>
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '2px', color: '#FFFFFF' }}>{label}</h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{description}</p>
            </div>
          </div>

          {/* Status badge */}
          <div className={`status-badge status-${status}`}>
            {status === 'running' && (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                style={{ width: '10px', height: '10px' }}
              >
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                  <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                </svg>
              </motion.div>
            )}
            {status}
          </div>
        </div>

        {/* Stats row */}
        <div style={{
          display: 'flex',
          gap: '20px',
          padding: '16px 20px',
          borderRadius: 'var(--radius-md)',
          background: '#0A0A0A',
          border: '1px solid rgba(255, 215, 0, 0.08)',
        }}>
          <div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800, fontVariantNumeric: 'tabular-nums', color: '#FFD700' }}>
              {leads.toLocaleString()}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Leads
            </div>
          </div>
          <div style={{ width: '1px', background: 'rgba(255,215,0,0.1)' }} />
          <div>
            <div style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-secondary)' }}>
              {lastRun ? new Date(lastRun).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—'}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Last Run
            </div>
          </div>
        </div>

        {/* Progress bar */}
        <ProgressBar percentage={percentage} status={status} label={message} />

        {/* Action buttons */}
        <div style={{ display: 'flex', gap: '12px' }}>
          <motion.button
            whileTap={{ scale: 0.97 }}
            className="btn-primary"
            onClick={handleRunScraper}
            disabled={status === 'running'}
            style={{ flex: 1 }}
          >
            <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {status === 'running' ? (
                <>
                  <motion.svg
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                  >
                    <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                  </motion.svg>
                  Running…
                </>
              ) : (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="5 3 19 12 5 21 5 3" />
                  </svg>
                  Run Scraper
                </>
              )}
            </span>
          </motion.button>

          <motion.button
            whileTap={{ scale: 0.97 }}
            className="btn-secondary"
            onClick={handleDownload}
            disabled={leads === 0}
            style={{ opacity: leads > 0 ? 1 : 0.4 }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            CSV
          </motion.button>
        </div>
      </motion.div>
    </motion.div>
  );
}
