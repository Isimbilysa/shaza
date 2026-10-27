import styles from './Logo.module.css';

/**
 * Ported from the landing site's `client/src/components/ui/Logo.tsx`.
 *
 * The geometry is copied verbatim and follows docs/brand/SHAZA-brand-guide.md section 3.
 * Change it in both places or not at all.
 *
 * One deliberate difference from the original: the wordmark's `<clipPath>` and its `useId()`
 * are gone. The outermost `<svg>` already clips to its viewBox, so the clip path was
 * redundant, and dropping it is what keeps this a server component -- a static logo has no
 * business shipping JavaScript to the browser.
 */

interface LogoProps {
  size?: number;
  className?: string;
}

/**
 * Terraces: a farmed hillside seen from above, its terraces bending into the letter S, with a
 * seed at the top of the hill. At 24px and below it drops to two thicker terraces so the lines
 * do not merge.
 */
export function LogoMark({ size = 34, className = '' }: LogoProps) {
  const small = size <= 24;
  return (
    <svg
      className={[styles.mark, className].filter(Boolean).join(' ')}
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      aria-hidden="true"
      focusable="false"
    >
      {small ? (
        <>
          <path
            d="M44.12 15 A14 14 0 1 0 32 36 A6 6 0 1 1 26.8 45 M37.2 19 A6 6 0 1 0 32 28 A14 14 0 1 1 19.88 49"
            className={styles.terrace}
            strokeWidth="5.5"
          />
          <ellipse cx="52" cy="9" rx="4.5" ry="7" transform="rotate(40 52 9)" className={styles.seed} />
        </>
      ) : (
        <>
          <path
            d="M45.86 14 A16 16 0 1 0 32 38 A4 4 0 1 1 28.54 44 M42.39 16 A12 12 0 1 0 32 34 A8 8 0 1 1 25.07 46 M38.93 18 A8 8 0 1 0 32 30 A12 12 0 1 1 21.61 48 M35.46 20 A4 4 0 1 0 32 26 A16 16 0 1 1 18.14 50"
            className={styles.terrace}
            strokeWidth="2.8"
          />
          <ellipse cx="51.5" cy="9" rx="3.2" ry="5" transform="rotate(40 51.5 9)" className={styles.seed} />
        </>
      )}
    </svg>
  );
}

/**
 * The custom wordmark: S H, leaf A, Z, leaf A. Both As are drawn as pointed leaves and the
 * first one holds the seed. Letters are drawn rather than typed so the name looks the same
 * everywhere, whatever fonts have loaded. Never retype it in a font.
 */
export function Wordmark({ className = '' }: { className?: string }) {
  return (
    <svg
      className={[styles.wordmark, className].filter(Boolean).join(' ')}
      viewBox="0 0 185 46"
      role="img"
      aria-label="SHAZA"
    >
      <g className={styles.leaf} strokeWidth="6">
        <path d="M21.19 7.26 A10 10 0 1 0 13 23 A10 10 0 1 1 4.81 38.74" />
        <path d="M38 0 V46 M58 0 V46 M38 23 H58" />
        <path d="M72 50 A80 80 0 0 1 87 2 A80 80 0 0 1 102 50" />
        <path d="M113 3 H139 L113 43 H139" />
        <path d="M150 50 A80 80 0 0 1 165 2 A80 80 0 0 1 180 50" />
      </g>
      <ellipse cx="87" cy="33" rx="3.2" ry="5" className={styles.seed} />
    </svg>
  );
}

export function Logo({ size = 34, className = '' }: LogoProps) {
  return (
    <span className={[styles.logo, className].filter(Boolean).join(' ')}>
      <LogoMark size={size} />
      <Wordmark />
    </span>
  );
}
