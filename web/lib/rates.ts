import type { Ceiling, Institution, Rate } from "./types";

export const STANDARD_TENURES = [1, 3, 6, 12, 13, 18, 24];

export type Offer = { institution: Institution; rate: Rate };

/** AER for interest paid at maturity: (1 + r*t)^(1/t) - 1, t in years. */
export function aerAtMaturity(nominalPct: number, months: number): number {
  const t = months / 12;
  return (Math.pow(1 + (nominalPct / 100) * t, 1 / t) - 1) * 100;
}

export function offersForTenure(institutions: Institution[], months: number): Offer[] {
  return institutions
    .flatMap((institution) =>
      institution.rates.filter((r) => r.tenure_months === months).map((rate) => ({ institution, rate })),
    )
    .sort((a, b) => b.rate.aer_pct - a.rate.aer_pct);
}

export function bestOffer(institution: Institution, months?: number): Rate | null {
  const rates = months ? institution.rates.filter((r) => r.tenure_months === months) : institution.rates;
  return rates.reduce<Rate | null>((best, r) => (!best || r.aer_pct > best.aer_pct ? r : best), null);
}

export function otherTenures(institutions: Institution[]): number[] {
  const all = new Set(institutions.flatMap((i) => i.rates.map((r) => r.tenure_months)));
  return [...all].filter((m) => !STANDARD_TENURES.includes(m)).sort((a, b) => a - b);
}

/** CBSL maximum nominal rate (finance companies) for a tenure, with its AER equivalent. */
export function ceilingFor(ceiling: Ceiling, months: number): { nominal: number; aer: number } | null {
  const band = ceiling?.bands.find((b) => months >= b.from_months && months < b.to_months);
  return band ? { nominal: band.max_nominal_pct, aer: aerAtMaturity(band.max_nominal_pct, months) } : null;
}

export function tenureLabel(rate: Rate): string {
  return rate.days ? `${rate.days} days` : `${rate.tenure_months} ${rate.tenure_months === 1 ? "month" : "months"}`;
}

export const pct = (n: number) => `${n.toFixed(2)}%`;

export function shortDate(iso: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  return isNaN(d.getTime())
    ? iso
    : d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "Asia/Colombo" });
}

/**
 * Finance companies advertising above the computed ceiling: a sign that CBSL has
 * changed the rule and the ceiling shown is out of date.
 */
export function institutionsAboveCeiling(institutions: Institution[], ceiling: Ceiling): Institution[] {
  return institutions.filter(
    (i) =>
      i.type === "finance" &&
      i.rates.some((r) => {
        const c = ceilingFor(ceiling, r.tenure_months);
        return c !== null && r.nominal_pct > c.nominal + 0.005;
      }),
  );
}
