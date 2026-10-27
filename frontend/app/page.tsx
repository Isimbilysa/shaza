import { fetchSeries } from '@/lib/api';
import type { Series } from '@/lib/types';
import { SeriesChart } from '@/components/SeriesChart';
import { ProvenanceNote } from '@/components/ProvenanceNote';
import styles from './page.module.css';

/**
 * The stage 1 dashboard.
 *
 * The charter's gate for stage 1 is *one* location flowing source -> database -> API ->
 * dashboard, documented. So this page shows one location and one variable, and the constants
 * below are deliberately constants rather than a picker.
 *
 * That is not laziness, it is the gate. A location selector, a variable selector, a date
 * brush and a comparison view are stage 3, and building them now would mean closing stage 1
 * on a page nobody has yet proven renders a single honest number.
 */
const LOCATION = 'kigali';
const VARIABLE = 'temperature_2m_mean';

export default async function Home() {
  const result = await fetchSeries(LOCATION, VARIABLE);

  if (!result.ok) {
    return (
      <section className={styles.failure}>
        <h1>{result.error}</h1>
        <p>{result.detail}</p>
        <p className={styles.failureHint}>
          This page shows nothing rather than an empty chart on purpose. An empty chart would be
          a claim that no data exists, which is a different statement from the one that is true:
          the dashboard could not reach the API.
        </p>
      </section>
    );
  }

  if (result.data.length === 0) {
    return (
      <section className={styles.failure}>
        <h1>No series in this window.</h1>
        <p>
          The API answered, and holds nothing for <span className="num">{VARIABLE}</span> at{' '}
          <span className="num">{LOCATION}</span> over the last year.
        </p>
      </section>
    );
  }

  return (
    <>
      <header className={styles.intro}>
        <h1 className={styles.title}>Environmental data, with its provenance</h1>
        <p className={styles.lede}>
          One location, one variable, from an external source through ingestion, validation and
          storage to this chart. Every number on this page carries what kind of claim it is.
        </p>
      </header>

      {result.data.map((series) => (
        <SeriesPanel key={`${series.variable}-${series.provenance.provenance}`} series={series} />
      ))}
    </>
  );
}

function SeriesPanel({ series }: { series: Series }) {
  const values = series.points.map((p) => p.value);
  const latest = series.points[series.points.length - 1];
  const firstDay = series.points[0]?.observed_on ?? '—';
  const lastDay = latest?.observed_on ?? '—';

  const min = values.length > 0 ? Math.min(...values) : null;
  const max = values.length > 0 ? Math.max(...values) : null;
  const mean =
    values.length > 0 ? values.reduce((sum, v) => sum + v, 0) / values.length : null;

  const fmt = (v: number | null) => (v === null ? '—' : v.toFixed(1));

  return (
    <section className={styles.panel}>
      <div className={styles.panelHead}>
        <div>
          <h2 className={styles.place}>
            {series.location.name}
            <span className={styles.admin}>
              {series.location.admin1 ?? series.location.country}
            </span>
          </h2>
          <p className={styles.coords}>
            <span className="num">{series.location.latitude.toFixed(4)}</span>,{' '}
            <span className="num">{series.location.longitude.toFixed(4)}</span>
            {series.location.elevation_m !== null && (
              <>
                {' · '}
                <span className="num">{series.location.elevation_m.toFixed(0)}</span> m
              </>
            )}
          </p>
        </div>

        {/* Brand guide section 7: gold marks the single most important value, and nothing else
            on the page competes with it. */}
        <div className={styles.headline}>
          <span className={styles.headlineLabel}>Latest · {lastDay}</span>
          <span className={styles.headlineValue}>
            <span className="num">{fmt(latest?.value ?? null)}</span>
            <span className={styles.headlineUnit}>{series.unit}</span>
          </span>
        </div>
      </div>

      <dl className={styles.stats}>
        <div>
          <dt>Minimum</dt>
          <dd className="num">
            {fmt(min)} <span className={styles.statUnit}>{series.unit}</span>
          </dd>
        </div>
        <div>
          <dt>Mean</dt>
          <dd className="num">
            {fmt(mean)} <span className={styles.statUnit}>{series.unit}</span>
          </dd>
        </div>
        <div>
          <dt>Maximum</dt>
          <dd className="num">
            {fmt(max)} <span className={styles.statUnit}>{series.unit}</span>
          </dd>
        </div>
        <div>
          <dt>Daily values</dt>
          <dd className="num">{series.count}</dd>
        </div>
      </dl>

      <SeriesChart series={series} />

      <ProvenanceNote
        provenance={series.provenance}
        coverage={`${series.count} daily values · ${firstDay} to ${lastDay}`}
      />
    </section>
  );
}
