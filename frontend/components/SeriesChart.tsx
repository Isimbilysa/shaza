import type { Series } from '@/lib/types';
import styles from './SeriesChart.module.css';

/**
 * A daily series, drawn as SVG.
 *
 * ---------------------------------------------------------------------------------------------
 * Why there is no charting library here
 * ---------------------------------------------------------------------------------------------
 * Charter rule 7: a technology is adopted when a problem demands it. One line, one axis pair
 * and no interaction is not that problem. Recharts and friends earn their place when brushing,
 * linked selection or many overlaid series arrive, which is stage 3. Until then this is ~120
 * lines with no dependency, no bundle cost and no client JavaScript at all.
 *
 * ---------------------------------------------------------------------------------------------
 * The actual design problem: not letting a model look like a measurement
 * ---------------------------------------------------------------------------------------------
 * Every value in this chart is ERA5 reanalysis. Nobody stood in Kigali and read a thermometer;
 * a model reconstructed the day over a ~9-11 km grid cell. A conventional line chart implies the
 * opposite, and it does so through its defaults rather than through anything it says.
 *
 * Four of those defaults are changed, in descending order of how much work they do:
 *
 *   1. No point markers, ever, for modeled data. A dot says "a reading was taken here". It is
 *      the single most misleading mark available and it is on by default in most libraries.
 *   2. A dashed stroke for anything where `is_measurement` is false. The dashes are read off
 *      the provenance block, not hardcoded -- the day a real gauge writes to this location the
 *      same component draws it solid, with no edit.
 *   3. The claim is inside the plot frame, not in a caption beside it. Captions get cropped
 *      when a chart is screenshotted; this one cannot be separated from the line.
 *   4. The line takes the muted provenance colour, not the brand accent. Measured data is the
 *      only thing allowed to look solid and green.
 */

interface SeriesChartProps {
  series: Series;
}

const W = 960;
const H = 340;
const PAD = { top: 26, right: 18, bottom: 40, left: 56 };
const PLOT_W = W - PAD.left - PAD.right;
const PLOT_H = H - PAD.top - PAD.bottom;

/** Break the line rather than bridge it when days are missing. A straight segment across a gap
 *  is an interpolation the data does not contain. */
const MAX_GAP_DAYS = 2;
const DAY_MS = 86_400_000;

function niceTicks(min: number, max: number, target: number): number[] {
  if (!Number.isFinite(min) || !Number.isFinite(max) || min === max) return [min];
  const raw = (max - min) / target;
  const mag = 10 ** Math.floor(Math.log10(raw));
  const norm = raw / mag;
  const step = (norm >= 7.5 ? 10 : norm >= 3.5 ? 5 : norm >= 1.5 ? 2 : 1) * mag;
  const ticks: number[] = [];
  for (let t = Math.ceil(min / step) * step; t <= max + step / 1000; t += step) {
    ticks.push(Number(t.toFixed(6)));
  }
  return ticks;
}

function formatMonth(ms: number): string {
  return new Date(ms).toLocaleDateString('en-GB', {
    month: 'short',
    year: '2-digit',
    timeZone: 'UTC',
  });
}

export function SeriesChart({ series }: SeriesChartProps) {
  const parsed = series.points
    .map((p) => ({ t: Date.parse(`${p.observed_on}T00:00:00Z`), v: p.value }))
    .filter((p) => Number.isFinite(p.t) && Number.isFinite(p.v))
    .sort((a, b) => a.t - b.t);

  const first = parsed[0];
  const last = parsed[parsed.length - 1];

  if (parsed.length < 2 || first === undefined || last === undefined) {
    return (
      <p className={styles.empty}>
        Not enough points in this window to draw a series.
      </p>
    );
  }

  const values = parsed.map((p) => p.v);
  const vMin = Math.min(...values);
  const vMax = Math.max(...values);
  const headroom = (vMax - vMin || 1) * 0.12;
  const yLo = vMin - headroom;
  const yHi = vMax + headroom;

  const tSpan = last.t - first.t || 1;
  const x = (t: number) => PAD.left + ((t - first.t) / tSpan) * PLOT_W;
  const y = (v: number) => PAD.top + PLOT_H - ((v - yLo) / (yHi - yLo)) * PLOT_H;

  // Segments, split wherever the record skips days.
  const segments: string[] = [];
  let current: string[] = [];
  let previousT: number | null = null;
  for (const point of parsed) {
    const broken = previousT !== null && point.t - previousT > MAX_GAP_DAYS * DAY_MS;
    if (broken && current.length > 0) {
      segments.push(current.join(' '));
      current = [];
    }
    current.push(`${current.length === 0 ? 'M' : 'L'}${x(point.t).toFixed(2)} ${y(point.v).toFixed(2)}`);
    previousT = point.t;
  }
  if (current.length > 0) segments.push(current.join(' '));

  const yTicks = niceTicks(yLo, yHi, 5);

  // One tick per month boundary inside the window.
  const xTicks: number[] = [];
  const cursor = new Date(first.t);
  cursor.setUTCDate(1);
  cursor.setUTCHours(0, 0, 0, 0);
  while (cursor.getTime() <= last.t) {
    if (cursor.getTime() >= first.t) xTicks.push(cursor.getTime());
    cursor.setUTCMonth(cursor.getUTCMonth() + 1);
  }
  const xTickStride = Math.ceil(xTicks.length / 8);
  const shownXTicks = xTicks.filter((_, i) => i % xTickStride === 0);

  const modeled = !series.provenance.is_measurement;
  // Applied through `style` rather than the `stroke` attribute: var() inside an SVG
  // presentation attribute is not reliably resolved in Safari.
  const strokeStyle = { stroke: `var(--prov-${series.provenance.provenance})` };

  return (
    <figure className={styles.figure}>
      <svg
        className={styles.svg}
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label={`${series.label} at ${series.location.name}, ${series.provenance.label}, ${series.count} daily values from ${firstIso(series)} to ${lastIso(series)}`}
      >
        {/* horizontal grid + y axis */}
        {yTicks.map((t) => (
          <g key={`y${t}`}>
            <line
              x1={PAD.left}
              x2={PAD.left + PLOT_W}
              y1={y(t)}
              y2={y(t)}
              className={styles.grid}
            />
            <text x={PAD.left - 10} y={y(t)} className={styles.axisLabel} textAnchor="end" dy="0.32em">
              {t}
            </text>
          </g>
        ))}

        {/* x axis */}
        <line
          x1={PAD.left}
          x2={PAD.left + PLOT_W}
          y1={PAD.top + PLOT_H}
          y2={PAD.top + PLOT_H}
          className={styles.axis}
        />
        {shownXTicks.map((t) => (
          <text
            key={`x${t}`}
            x={x(t)}
            y={PAD.top + PLOT_H + 22}
            className={styles.axisLabel}
            textAnchor="middle"
          >
            {formatMonth(t)}
          </text>
        ))}

        {/* the series */}
        {segments.map((d, i) => (
          <path
            key={i}
            d={d}
            fill="none"
            style={strokeStyle}
            strokeWidth={1.6}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeDasharray={modeled ? '5 3' : undefined}
          />
        ))}

        {/* The claim, inside the frame. See the note at the top of this file. */}
        <text x={PAD.left} y={16} className={styles.stamp}>
          {series.provenance.label.toUpperCase()}
          {modeled ? ' · NOT MEASURED' : ''}
        </text>
      </svg>

      <figcaption className={styles.caption}>
        <span className={styles.unit}>
          {series.label} (<span className="num">{series.unit}</span>)
        </span>
        {modeled && (
          <span className={styles.legend}>
            <svg width="26" height="8" aria-hidden="true">
              <line
                x1="0"
                y1="4"
                x2="26"
                y2="4"
                style={strokeStyle}
                strokeWidth="1.6"
                strokeDasharray="5 3"
              />
            </svg>
            dashed = modeled, not measured
          </span>
        )}
      </figcaption>
    </figure>
  );
}

function firstIso(series: Series): string {
  return series.points[0]?.observed_on ?? '';
}

function lastIso(series: Series): string {
  return series.points[series.points.length - 1]?.observed_on ?? '';
}
