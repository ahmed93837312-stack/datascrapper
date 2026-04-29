/**
 * ProgressBar Component
 * =====================
 * Animated progress bar with Framer Motion.
 * Black and Yellow Theme.
 */

import { motion } from 'framer-motion';

export default function ProgressBar({ percentage = 0, status = 'idle', label = '' }) {
  const isActive = status === 'running';
  const isComplete = status === 'completed';
  const isFailed = status === 'failed';

  // Color based on status
  let barGradient = 'linear-gradient(90deg, #FFCC00, #FFD700)';
  let glowColor = 'rgba(255, 215, 0, 0.4)';

  if (isComplete) {
    barGradient = 'linear-gradient(90deg, #10b981, #34d399)';
    glowColor = 'rgba(16, 185, 129, 0.4)';
  } else if (isFailed) {
    barGradient = 'linear-gradient(90deg, #f43f5e, #fb7185)';
    glowColor = 'rgba(244, 63, 94, 0.4)';
  }

  return (
    <div style={{ width: '100%' }}>
      {/* Label row */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '8px',
      }}>
        <span style={{
          fontSize: '0.75rem',
          color: 'var(--text-secondary)',
          fontWeight: 500,
        }}>
          {label || (isActive ? 'Scraping in progress…' : isComplete ? 'Completed' : isFailed ? 'Failed' : 'Ready to scrape')}
        </span>
        <span style={{
          fontSize: '0.8rem',
          fontWeight: 700,
          fontVariantNumeric: 'tabular-nums',
          color: isActive ? '#FFD700' : isComplete ? '#10b981' : 'var(--text-muted)',
        }}>
          {percentage}%
        </span>
      </div>

      {/* Track */}
      <div
        style={{
          width: '100%',
          height: '6px',
          borderRadius: '100px',
          background: '#0A0A0A', // Deep black track
          border: '1px solid rgba(255, 215, 0, 0.1)',
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        {/* Fill */}
        <motion.div
          initial={{ width: '0%' }}
          animate={{ width: `${Math.min(percentage, 100)}%` }}
          transition={{
            duration: 0.8,
            ease: [0.25, 0.46, 0.45, 0.94],
          }}
          style={{
            height: '100%',
            borderRadius: '100px',
            background: barGradient,
            boxShadow: isActive ? `0 0 12px ${glowColor}` : 'none',
            position: 'relative',
          }}
        >
          {/* Shimmer effect when active */}
          {isActive && (
            <motion.div
              animate={{ x: ['0%', '200%'] }}
              transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '50%',
                height: '100%',
                background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)',
                borderRadius: '100px',
              }}
            />
          )}
        </motion.div>
      </div>
    </div>
  );
}
