/**
 * The API contract, mirrored.
 *
 * These types are hand-written against `backend/app/schemas/`, deliberately. Generating them
 * from the OpenAPI document is a stage 2 convenience; right now there is value in a human
 * having to notice when the backend's provenance block changes shape.
 *
 * The shape to preserve: there is no type here for a bare number. A `Point` only ever reaches
 * the UI inside a `Series`, and a `Series` always carries a `ProvenanceBlock`. That is the
 * charter's hard rule expressed in TypeScript -- a component physically cannot destructure a
 * value out of this API without also having the claim it makes in scope.
 */

export type ProvenanceKind =
  | 'observed'
  | 'reanalysis'
  | 'forecast'
  | 'simulated'
  | 'derived';

export type SourceKind =
  | 'external_api'
  | 'public_dataset'
  | 'synthetic'
  | 'field_observation';

export type Maturity = 'illustrative' | 'in-progress' | 'verified';

export interface SourceRef {
  slug: string;
  name: string;
  kind: SourceKind;
  url: string | null;
  licence: string | null;
  attribution: string | null;
}

export interface ProvenanceBlock {
  provenance: ProvenanceKind;
  label: string;
  /** False for anything modeled. The chart reads this, not the string label. */
  is_measurement: boolean;
  maturity: Maturity;
  source: SourceRef;
  caveat: string | null;
}

export interface Location {
  slug: string;
  name: string;
  country: string;
  admin1: string | null;
  latitude: number;
  longitude: number;
  elevation_m: number | null;
}

export interface Point {
  observed_on: string;
  value: number;
  uncertainty: number | null;
}

export interface Series {
  location: Location;
  variable: string;
  label: string;
  unit: string;
  provenance: ProvenanceBlock;
  count: number;
  points: Point[];
}

export interface Envelope<T> {
  ok: boolean;
  data: T;
}
