/**
 * Navbar Component
 * ================
 * Minimal, premium navigation bar with Black and Yellow styling.
 * Includes animated logo, active underline, and navigation links.
 */

import Link from 'next/link';
import { useRouter } from 'next/router';
import { motion } from 'framer-motion';

const navLinks = [
  { href: '/', label: 'Dashboard' },
  { href: '/upwork', label: 'Upwork' },
  { href: '/linkedin', label: 'LinkedIn' },
  { href: '/directories', label: 'Directories' },
  { href: '/google_maps', label: 'Google Maps' },
];

export default function Navbar() {
  const router = useRouter();

  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 50,
        padding: '16px 0',
      }}
    >
      <div
        className="glass"
        style={{
          maxWidth: '1280px',
          margin: '0 auto',
          padding: '14px 28px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderRadius: '16px',
          marginLeft: '24px',
          marginRight: '24px',
          background: '#050505',
          borderBottom: '1px solid rgba(255, 215, 0, 0.1)',
        }}
      >
        {/* Logo */}
        <Link href="/">
          <motion.div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              cursor: 'pointer',
            }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                background: 'rgba(255, 215, 0, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 15px rgba(255, 215, 0, 0.15)',
                border: '1px solid rgba(255, 215, 0, 0.4)',
              }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#FFD700" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                <polyline points="7.5 4.21 12 6.81 16.5 4.21" />
                <polyline points="7.5 19.79 7.5 14.6 3 12" />
                <polyline points="21 12 16.5 14.6 16.5 19.79" />
                <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
                <line x1="12" y1="22.08" x2="12" y2="12" />
              </svg>
            </div>
            <div>
              <span style={{ fontWeight: 800, fontSize: '1.1rem', letterSpacing: '-0.02em', color: '#FFF' }}>
                Data<span style={{ color: '#FFCC00' }}>Scrap</span>
              </span>
              <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', display: 'block', marginTop: '-2px', letterSpacing: '0.05em' }}>
                AGENT v1.0
              </span>
            </div>
          </motion.div>
        </Link>

        {/* Navigation Links */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {navLinks.map((link) => {
            const isActive = router.pathname === link.href;
            return (
              <Link key={link.href} href={link.href}>
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  style={{
                    position: 'relative',
                    padding: '8px 16px',
                    borderRadius: '10px',
                    fontSize: '0.85rem',
                    fontWeight: isActive ? 600 : 400,
                    color: isActive ? '#FFD700' : 'var(--text-secondary)',
                    cursor: 'pointer',
                    transition: 'color 0.2s ease',
                  }}
                >
                  {link.label}
                  {isActive && (
                    <motion.div
                      layoutId="nav-underline"
                      style={{
                        position: 'absolute',
                        left: 0,
                        right: 0,
                        bottom: -4,
                        height: '2px',
                        background: '#FFD700',
                        borderRadius: '2px',
                        boxShadow: '0 2px 8px rgba(255, 215, 0, 0.4)',
                      }}
                      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                    />
                  )}
                </motion.div>
              </Link>
            );
          })}
        </div>

        {/* Status indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: '#10b981',
            boxShadow: '0 0 8px rgba(16, 185, 129, 0.5)',
          }} />
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Online</span>
        </div>
      </div>
    </motion.nav>
  );
}
