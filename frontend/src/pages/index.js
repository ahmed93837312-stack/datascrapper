/**
 * Dashboard — Home Page
 * =====================
 * Main dashboard with 3 glassmorphism scraper cards,
 * analytics summary, and hero section. Black & Yellow Theme.
 */

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import Card from '@/components/Card';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.15,
    },
  },
};

export default function Dashboard() {
  const [stats, setStats] = useState({
    total_leads: 0,
    modules: {
      upwork: { leads: 0, has_data: false, status: 'idle', last_run: null },
      linkedin: { leads: 0, has_data: false, status: 'idle', last_run: null },
      directories: { leads: 0, has_data: false, status: 'idle', last_run: null },
      google_maps: { leads: 0, has_data: false, status: 'idle', last_run: null },
    },
  });

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/stats`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch {
      // API not reachable
    }
  }, []);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, [fetchStats]);

  return (
    <div className="container-main" style={{ padding: '40px 24px 80px' }}>
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        style={{
          textAlign: 'center',
          marginBottom: '56px',
          position: 'relative',
        }}
      >
        {/* Background decorative glow */}
        <div style={{
          position: 'absolute',
          top: '-60px',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '400px',
          height: '200px',
          background: 'radial-gradient(ellipse, rgba(255, 215, 0, 0.15), transparent 70%)',
          pointerEvents: 'none',
          filter: 'blur(30px)',
        }} />

        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.1, duration: 0.5 }}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 16px',
            borderRadius: '100px',
            background: 'rgba(255, 215, 0, 0.05)',
            border: '1px solid rgba(255, 215, 0, 0.2)',
            marginBottom: '20px',
            fontSize: '0.8rem',
            fontWeight: 600,
            color: '#FFD700',
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
          </svg>
          Powered by AI Automation
        </motion.div>

        <h1 style={{ fontSize: '2.8rem', fontWeight: 900, letterSpacing: '-0.03em', marginBottom: '14px', color: '#FFF' }}>
          Lead Generation{' '}
          <span className="gradient-text">Command Center</span>
        </h1>

        <p style={{
          fontSize: '1.05rem',
          color: 'var(--text-secondary)',
          maxWidth: '560px',
          margin: '0 auto',
          lineHeight: 1.7,
        }}>
          Scrape, collect, and manage leads from Upwork, LinkedIn, and local business directories — all from one dashboard.
        </p>
      </motion.div>

      {/* Analytics Summary */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.6 }}
        className="glass"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '1px',
          background: 'rgba(255, 215, 0, 0.15)',
          borderRadius: 'var(--radius-lg)',
          overflow: 'hidden',
          marginBottom: '40px',
          border: '1px solid rgba(255, 215, 0, 0.2)',
        }}
      >
        {[
          { label: 'Total Leads', value: stats.total_leads, color: '#FFD700' },
          { label: 'Upwork', value: stats.modules.upwork.leads, color: '#FFCC00' },
          { label: 'LinkedIn', value: stats.modules.linkedin.leads, color: '#FFD700' },
          { label: 'Directories', value: stats.modules.directories.leads, color: '#FFCC00' },
          { label: 'Google Maps', value: stats.modules.google_maps.leads, color: '#FFD700' },
        ].map((stat, idx) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 + idx * 0.1 }}
            style={{
              padding: '28px 24px',
              background: '#050505',
              textAlign: 'center',
            }}
          >
            <div style={{
              fontSize: '2rem',
              fontWeight: 800,
              fontVariantNumeric: 'tabular-nums',
              color: stat.color,
              lineHeight: 1,
              marginBottom: '8px',
            }}>
              {stat.value.toLocaleString()}
            </div>
            <div style={{
              fontSize: '0.72rem',
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
              fontWeight: 600,
            }}>
              {stat.label}
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Scraper Cards Grid */}
      <motion.div
        variants={staggerContainer}
        initial="initial"
        animate="animate"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
          gap: '24px',
        }}
      >
        <Card
          module="upwork"
          leads={stats.modules.upwork.leads}
          lastRun={stats.modules.upwork.last_run}
          onStatsUpdate={fetchStats}
        />
        <Card
          module="linkedin"
          leads={stats.modules.linkedin.leads}
          lastRun={stats.modules.linkedin.last_run}
          onStatsUpdate={fetchStats}
        />
        <Card
          module="directories"
          leads={stats.modules.directories.leads}
          lastRun={stats.modules.directories.last_run}
          onStatsUpdate={fetchStats}
        />
        <Card
          module="google_maps"
          leads={stats.modules.google_maps.leads}
          lastRun={stats.modules.google_maps.last_run}
          onStatsUpdate={fetchStats}
        />
      </motion.div>
    </div>
  );
}

Dashboard.pageTitle = 'DataScrap Agent — Dashboard';
