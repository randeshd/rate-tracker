export type Rate = {
  tenure_months: number;
  nominal_pct: number;
  aer_pct: number;
  note: string;
  days: number | null;
};

export type Rating = {
  agency: string;
  rating: string;
  outlook: string;
  date: string;
  source: string;
  source_url: string;
  stale?: boolean;
};

export type Institution = {
  id: string;
  name: string;
  type: "bank" | "finance";
  source_url: string;
  status: "ok" | "stale" | "no_data";
  checked_at: string;
  last_success: string;
  error: string;
  rates: Rate[];
  ratings: Rating[];
};

export type CeilingBand = {
  from_months: number;
  to_months: number;
  tbill_days: number;
  margin: number;
  max_nominal_pct: number;
};

export type Ceiling = {
  based_on_quarter: string;
  source_url: string;
  stale?: boolean;
  bands: CeilingBand[];
} | null;

export type TrackerData = {
  updatedAt: string;
  ratingsUpdatedAt: string;
  institutions: Institution[];
  ceiling: Ceiling;
};
