/**
 * Layout Component
 * ================
 * Wraps all pages with Navbar, animated page transitions, and consistent structure.
 */

import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/router';
import Navbar from './Navbar';
import Head from 'next/head';

const pageVariants = {
  initial: {
    opacity: 0,
    y: 20,
    filter: 'blur(4px)',
  },
  animate: {
    opacity: 1,
    y: 0,
    filter: 'blur(0px)',
    transition: {
      duration: 0.5,
      ease: [0.25, 0.46, 0.45, 0.94],
    },
  },
  exit: {
    opacity: 0,
    y: -10,
    filter: 'blur(2px)',
    transition: {
      duration: 0.3,
    },
  },
};

export default function Layout({ children, title = 'DataScrap Agent' }) {
  const router = useRouter();

  return (
    <>
      <Head>
        <title>{title}</title>
        <meta name="description" content="DataScrap Agent — AI-powered lead generation scraper with premium dashboard" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>⚡</text></svg>" />
      </Head>

      <Navbar />

      <main style={{ minHeight: 'calc(100vh - 100px)' }}>
        <AnimatePresence mode="wait">
          <motion.div
            key={router.pathname}
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Footer */}
      <footer style={{
        padding: '32px 24px',
        textAlign: 'center',
        color: 'var(--text-muted)',
        fontSize: '0.75rem',
        borderTop: '1px solid rgba(255, 215, 0, 0.1)',
        marginTop: '60px',
      }}>
        <p style={{ color: '#FFD700', fontWeight: 600 }}>DataScrap Agent v1.0 — Lead Generation Platform</p>
        <p style={{ marginTop: '4px', opacity: 0.6 }}>Built with Python · FastAPI · Next.js</p>
      </footer>
    </>
  );
}
