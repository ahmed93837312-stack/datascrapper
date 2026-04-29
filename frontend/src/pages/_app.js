/**
 * _app.js — Custom App Component
 * ================================
 * Wraps all pages with Layout and imports global styles.
 */

import '@/styles/globals.css';
import Layout from '@/components/Layout';
import { AnimatePresence } from 'framer-motion';

export default function App({ Component, pageProps, router }) {
  // Allow pages to override the layout title via getLayout or pageTitle
  const pageTitle = Component.pageTitle || 'DataScrap Agent';

  return (
    <Layout title={pageTitle}>
      <AnimatePresence mode="wait">
        <Component key={router.route} {...pageProps} />
      </AnimatePresence>
    </Layout>
  );
}
