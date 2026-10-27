import type { ProvenanceBlock } from '@/lib/types';
import styles from './ProvenanceNote.module.css';

/**
 * The provenance block, rendered in full.
 *
 * This is not a caption and not a tooltip. The charter's hard rule is that a number never
 * travels without the claim it makes, and a disclosure the reader has to open is a disclosure
 * most readers never see. Everything the API says about where this data came from is on the
 * page, unprompted:
 *
 *   - what kind of claim it is (reanalysis, not measurement)
 *   - how mature SHAZA considers it
 *   - who produced it, under what licence, with the attribution their terms require
 *   - the caveat the backend attached to the source
 *
 * `maturity` is rendered from the same three-value vocabulary the landing site uses
 * (illustrative / in-progress / verified), so the two surfaces make the same claim in the
 * same words.
 */

interface ProvenanceNoteProps {
  provenance: ProvenanceBlock;
  /** Rendered alongside the source, e.g. "731 daily values, 2024-09-24 to 2026-09-24". */
  coverage?: string;
}

const MATURITY_COPY: Record<ProvenanceBlock['maturity'], string> = {
  illustrative: 'Illustrative — shape only, not a finding.',
  'in-progress': 'In progress — ingested and validated, not yet independently checked.',
  verified: 'Verified — checked against an independent source.',
};

export function ProvenanceNote({ provenance, coverage }: ProvenanceNoteProps) {
  const { source } = provenance;

  return (
    <aside className={styles.note} aria-label="Data provenance">
      <div className={styles.header}>
        <span
          className={styles.badge}
          style={{ ['--badge-colour' as string]: `var(--prov-${provenance.provenance})` }}
        >
          {provenance.label}
        </span>
        <span className={styles.measurement}>
          {provenance.is_measurement ? 'Measured' : 'Not a measurement'}
        </span>
      </div>

      <dl className={styles.rows}>
        <div className={styles.row}>
          <dt>Source</dt>
          <dd>
            {source.url ? (
              <a href={source.url} target="_blank" rel="noreferrer noopener">
                {source.name}
              </a>
            ) : (
              source.name
            )}
          </dd>
        </div>

        {coverage && (
          <div className={styles.row}>
            <dt>Coverage</dt>
            <dd className="num">{coverage}</dd>
          </div>
        )}

        <div className={styles.row}>
          <dt>Maturity</dt>
          <dd>{MATURITY_COPY[provenance.maturity]}</dd>
        </div>

        {source.licence && (
          <div className={styles.row}>
            <dt>Licence</dt>
            <dd>{source.licence}</dd>
          </div>
        )}

        {source.attribution && (
          <div className={styles.row}>
            <dt>Attribution</dt>
            <dd>{source.attribution}</dd>
          </div>
        )}
      </dl>

      {provenance.caveat && <p className={styles.caveat}>{provenance.caveat}</p>}
    </aside>
  );
}
