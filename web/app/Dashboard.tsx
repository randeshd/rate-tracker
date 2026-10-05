"use client";

import { useState } from "react";
import type { Institution, Rate, TrackerData } from "@/lib/types";
import {
  STANDARD_TENURES,
  bestOffer,
  ceilingFor,
  institutionsAboveCeiling,
  offersForTenure,
  otherTenures,
  pct,
  shortDate,
  tenureLabel,
} from "@/lib/rates";

const DIRECTIONS_URL =
  "https://www.cbsl.gov.lk/en/laws/directions-circulars-guidelines-for-non-banks";

type Row = { institution: Institution; rate: Rate };

export default function Dashboard({ data }: { data: TrackerData }) {
  // 0 means "best across all tenures", -1 means the all-tenures grid
  const [tenure, setTenure] = useState(12);
  const [type, setType] = useState<"all" | "bank" | "finance">("all");
  const institutions = data.institutions.filter(
    (i) => type === "all" || i.type === type,
  );
  const others = otherTenures(data.institutions);
  const best = tenure === 0;

  const rows: Row[] = best
    ? institutions
        .flatMap((institution) => {
          const rate = bestOffer(institution);
          return rate ? [{ institution, rate }] : [];
        })
        .sort((a, b) => b.rate.aer_pct - a.rate.aer_pct)
    : offersForTenure(institutions, tenure);
  const grid = tenure === -1;
  const ceiling = best || grid ? null : ceilingFor(data.ceiling, tenure);
  const newDirections = data.ceiling?.unreviewed_directions ?? [];
  const ceilingDoubt =
    newDirections.length > 0 ||
    institutionsAboveCeiling(data.institutions, data.ceiling) >= 3;

  return (
    <main className="page">
      <header className="header">
        <h1>Investment Tracker</h1>
        <span className="updated">
          Updated {shortDate(data.updatedAt) || "—"}
        </span>
      </header>

      <nav className="pills">
        {STANDARD_TENURES.map((m) => (
          <button
            key={m}
            className={tenure === m ? "pill active" : "pill"}
            onClick={() => setTenure(m)}
          >
            {m} {m === 1 ? "month" : "months"}
          </button>
        ))}
        <select
          className={others.includes(tenure) ? "pill active" : "pill"}
          value={others.includes(tenure) ? tenure : ""}
          onChange={(e) => e.target.value && setTenure(Number(e.target.value))}
        >
          <option value="">Other</option>
          {others.map((m) => (
            <option key={m} value={m}>
              {m} months
            </option>
          ))}
        </select>
        <button
          className={grid ? "pill push active" : "pill push"}
          onClick={() => setTenure(-1)}
        >
          All tenures
        </button>
        <button
          className={best ? "pill active" : "pill"}
          onClick={() => setTenure(0)}
        >
          Best AER
        </button>
      </nav>

      <div className="filter">
        {(["all", "bank", "finance"] as const).map((t) => (
          <button
            key={t}
            className={type === t ? "active" : ""}
            onClick={() => setType(t)}
          >
            {t === "all" ? "All" : t === "bank" ? "Banks" : "Finance companies"}
          </button>
        ))}
      </div>

      {ceilingDoubt && (
        <p className="warning">
          The CBSL ceiling may be out of date.{" "}
          {newDirections.length > 0 ? (
            <>
              CBSL has published{" "}
              <a href={newDirections[0].url} target="_blank" rel="noreferrer">
                a new direction on deposit rates
              </a>
              . Open it, then ask Claude to update the ceiling margins with the
              table in that document.
            </>
          ) : (
            <>
              Several finance companies are advertising above it. Check{" "}
              <a href={DIRECTIONS_URL} target="_blank" rel="noreferrer">
                CBSL&apos;s directions
              </a>{" "}
              for a new one on maximum deposit rates, then ask Claude to update
              the ceiling margins.
            </>
          )}
        </p>
      )}
      {!best && !grid && (
        <p className="ceiling">
          CBSL ceiling for finance companies:{" "}
          {ceiling ? (
            <strong>{pct(ceiling.nominal)}</strong>
          ) : (
            "none at this tenure"
          )}
        </p>
      )}

      {grid ? (
        <Grid institutions={institutions} data={data} />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th className="rank" />
                <th>Institution</th>
                {best && <th>Tenure</th>}
                <th className="num">Nominal</th>
                <th className="num">AER</th>
                <th>Rating</th>
                <th>Outlook</th>
                <th>Rated</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(({ institution, rate }, index) => (
                <tr
                  key={`${institution.id}-${rate.tenure_months}-${rate.note}`}
                >
                  <td className="rank">{index + 1}</td>
                  <td>
                    <a
                      className="name"
                      href={institution.source_url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {institution.name}
                    </a>
                    {institution.status !== "ok" && (
                      <span className="stale">
                        stale since {shortDate(institution.last_success)}
                      </span>
                    )}
                    {rate.note && <div className="note">{rate.note}</div>}
                  </td>
                  {best && <td>{tenureLabel(rate)}</td>}
                  <td className="num">{pct(rate.nominal_pct)}</td>
                  <td className="num aer">{pct(rate.aer_pct)}</td>
                  <td>
                    {institution.ratings.map((r) => (
                      <div key={r.agency}>
                        {r.rating}{" "}
                        <span className="muted">
                          {r.agency === "Lanka Rating Agency" ? "LRA" : "Fitch"}
                        </span>
                      </div>
                    ))}
                  </td>
                  <td>
                    {institution.ratings.map((r) => (
                      <div key={r.agency}>
                        {r.outlook || <span className="muted">–</span>}
                      </div>
                    ))}
                  </td>
                  <td>
                    {institution.ratings.map((r) => (
                      <div key={r.agency}>
                        {shortDate(r.date) || <span className="muted">–</span>}
                      </div>
                    ))}
                  </td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={8} className="empty">
                    No offers
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}

function Grid({
  institutions,
  data,
}: {
  institutions: Institution[];
  data: TrackerData;
}) {
  const [sortBy, setSortBy] = useState(12);
  const aer = (i: Institution, m: number) => bestOffer(i, m)?.aer_pct ?? -1;
  const rows = [...institutions].sort(
    (a, b) => aer(b, sortBy) - aer(a, sortBy),
  );
  const top = Object.fromEntries(
    STANDARD_TENURES.map((m) => [m, Math.max(...rows.map((i) => aer(i, m)))]),
  );

  return (
    <div className="table-wrap">
      <table className="grid">
        <thead>
          <tr>
            <th>Institution</th>
            {STANDARD_TENURES.map((m) => (
              <th key={m} className="num">
                <button
                  className={sortBy === m ? "sort active" : "sort"}
                  onClick={() => setSortBy(m)}
                >
                  {m}m{sortBy === m ? " ↓" : ""}
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr className="ceiling-row">
            <td>CBSL ceiling (finance companies)</td>
            {STANDARD_TENURES.map((m) => {
              const c = ceilingFor(data.ceiling, m);
              return (
                <td key={m} className="num">
                  {c ? pct(c.nominal) : "–"}
                </td>
              );
            })}
          </tr>
          {rows.map((institution) => (
            <tr key={institution.id}>
              <td>
                <a
                  className="name"
                  href={institution.source_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  {institution.name}
                </a>
              </td>
              {STANDARD_TENURES.map((m) => {
                const rate = bestOffer(institution, m);
                return (
                  <td key={m} className="num">
                    {rate && (
                      <>
                        <div
                          className={
                            rate.aer_pct === top[m] ? "aer" : "aer plain"
                          }
                        >
                          {pct(rate.aer_pct)}
                        </div>
                        <div className="note">{pct(rate.nominal_pct)}</div>
                      </>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
