import type { Metadata } from 'next';
import { Logo } from '@/components/Logo';
import './globals.css';
import styles from './layout.module.css';

export const metadata: Metadata = {
  title: 'SHAZA — environmental data',
  description:
    'SHAZA retrieves, labels and serves environmental data for Rwanda. Every value carries its provenance.',
};

/**
 * Fonts are loaded with a stylesheet link rather than `next/font` on purpose: `next/font`
 * fetches at build time, and a build that fails without a network is a bad trade for a
 * dashboard whose token layer already falls back to system sans and mono.
 */
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap"
        />
      </head>
      <body>
        <header className={styles.header}>
          <div className={styles.headerInner}>
            <Logo size={30} />
            <span className={styles.stage}>Stage 1 · Foundation</span>
          </div>
        </header>

        <main className={styles.main}>{children}</main>

        <footer className={styles.footer}>
          <div className={styles.footerInner}>
            <p>
              SHAZA retrieves this data from external providers. It does not collect it. Nothing
              here is farming advice.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
