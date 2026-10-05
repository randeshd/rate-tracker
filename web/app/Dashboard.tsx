"use client";

import { useMemo, useState } from "react";
import type { Institution, Rate, TrackerData } from "@/lib/types";
import {
  STANDARD_TENURES,
  bestOffer,
  ceilingFor,
  offersForTenure,
  otherTenures,
  pct,
  shortDate,
  tenureLabel,
} from "@/lib/rates";

type View = "tenure" | "best" | "grid";
type TypeFilter = "all" | "bank" | "finance";

const VIEWS: { id: View; label: string }[] = [
  { id: "tenure", label: "By tenure" },
  { id: "best", label: "Best AER across tenures" },
  { id: "grid", label: "All tenures grid" },
];

export default function Dashboard({ data }: { data: TrackerData }) {
  const [view, setView] = useState<View>("tenure");
  const [tenure, setTenure] = useState(12);
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("all");

  const institutions = useMemo(
    () => data.institutions.filter((i) => typeFilter === "all" || i.type === typeFilter),
    [data.institutions, typeFilter],
  );
  const extraTenures = useMemo(() => otherTenures(data.institutions), [data.institutions]);
  const problems = data.institutions.filter((i) => i.status !== "ok");

  return (
    <main className="page">
      <header className="header">
        <div>
          <h1>Investment Tracker</h1>
        </div>
        <div className="updated">
          <div>Rates updated {shortDate(data.updatedAt) || "—"}</div>
          <div>Ratings checked {shortDate(data.ratingsUpdatedAt) || "—"}</div>
        </div>
      </header>

      {problems.length > 0 && (
        <div className="notice">
          {problems.map((i) => (
            <span key={i.id}>
              <strong>{i.name}</strong>:{" "}
              {i.status === "stale" ? `showing older data from ${shortDate(i.last_success)}` : "no data available"}
            </span>
          ))}
        </div>
      )}

      <nav className="toolbar">
        <div className="tabs">
          {VIEWS.map((v) => (
            <button key={v.id} className={view === v.id ? "tab active" : "tab"} onClick={() => setView(v.id)}>
              {v.label}
            </button>
          ))}
        </div>
        <div className="segmented">
          {(["all", "bank", "finance"] as TypeFilter[]).map((t) => (
            <button key={t} className={typeFilter === t ? "active" : ""} onClick={() => setTypeFilter(t)}>
              {t === "all" ? "All" : t === "bank" ? "Banks" : "Finance companies"}
            </button>
          ))}
        </div>
      </nav>

      {view === "tenure" && (
        <TenureView
          institutions={institutions}
          data={data}
          tenure={tenure}
          setTenure={setTenure}
          extraTenures={extraTenures}
        />
      )}
      {view === "best" && <BestView institutions={institutions} data={data} />}
      {view === "grid" && <GridView institutions={institutions} data={data} />}
    </main>
  );
}

function TenureView({
  institutions,
  data,
  tenure,
  setTenure,
  extraTenures,
}: {
  institutions: Institution[];
  data: TrackerData;
  tenure: number;
  setTenure: (m: number) => void;
  extraTenures: number[];
}) {
  const offers = offersForTenure(institutions, tenure);
  const missing = institutions.filter((i) => !i.rates.some((r) => r.tenure_months === tenure));
  const ceiling = ceilingFor(data.ceiling, tenure);

  return (
    <section>
      <div className="pills">
        {STANDARD_TENURES.map((m) => (
          <button key={m} className={tenure === m ? "pill active" : "pill"} onClick={() => setTenure(m)}>
            {m} {m === 1 ? "month" : "months"}
          </button>
        ))}
        <span className="pill-sep">Other tenures</span>
        {extraTenures.map((m) => (
          <button key={m} className={tenure === m ? "pill small active" : "pill small"} onClick={() => setTenure(m)}>
            {m}m
          </button>
        ))}
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th className="num">#</th>
              <th>Institution</th>
              <th className="num">Nominal</th>
              <th className="num">AER</th>
              <th>Offer</th>
              <th>Rating</th>
              <th>Outlook</th>
              <th>Rating date</th>
            </tr>
          </thead>
          <tbody>
            {ceiling && (
              <tr className="ceiling">
                <td />
                <td>CBSL ceiling (finance companies)</td>
                <td className="num">{pct(ceiling.nominal)}</td>
                <td className="num">{pct(ceiling.aer)}</td>
                <td colSpan={4} />
              </tr>
            )}
            {offers.map(({ institution, rate }, index) => (
              <tr key={`${institution.id}-${rate.note}`}>
                <td className="num rank">{index + 1}</td>
                <td>
                  <InstitutionName institution={institution} />
                </td>
                <td className="num">{pct(rate.nominal_pct)}</td>
                <td className="num aer">{pct(rate.aer_pct)}</td>
                <td className="note">{rate.note || "Standard"}</td>
                <RatingCells institution={institution} />
              </tr>
            ))}
            {offers.length === 0 && (
              <tr>
                <td colSpan={8} className="empty">
                  No institution offers this tenure.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {missing.length > 0 && (
        <p className="missing">
          Not offered for {tenure} {tenure === 1 ? "month" : "months"}: {missing.map((i) => i.name).join(", ")}
        </p>
      )}
    </section>
  );
}

function BestView({ institutions, data }: { institutions: Institution[]; data: TrackerData }) {
  const rows = institutions
    .map((institution) => ({ institution, rate: bestOffer(institution) }))
    .sort((a, b) => (b.rate?.aer_pct ?? -1) - (a.rate?.aer_pct ?? -1));
  const top = rows[0]?.rate?.aer_pct ?? 1;
  const leaders = STANDARD_TENURES.map((m) => ({ months: m, offer: offersForTenure(institutions, m)[0] }));

  return (
    <section>
      <div className="leaders">
        {leaders.map(({ months, offer }) => (
          <div key={months} className="leader">
            <div className="leader-tenure">{months}m</div>
            <div className="leader-aer">{offer ? pct(offer.rate.aer_pct) : "—"}</div>
            <div className="leader-name">{offer?.institution.name ?? "No offers"}</div>
          </div>
        ))}
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th className="num">#</th>
              <th>Institution</th>
              <th className="num">Best AER</th>
              <th className="bar-col" />
              <th>Tenure</th>
              <th className="num">Nominal</th>
              <th>Offer</th>
              <th>Rating</th>
              <th>Outlook</th>
              <th>Rating date</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ institution, rate }, index) => {
              const ceiling = rate ? ceilingFor(data.ceiling, rate.tenure_months) : null;
              return (
                <tr key={institution.id}>
                  <td className="num rank">{rate ? index + 1 : ""}</td>
                  <td>
                    <InstitutionName institution={institution} />
                  </td>
                  <td className="num aer">{rate ? pct(rate.aer_pct) : "—"}</td>
                  <td className="bar-col">
                    {rate && <div className="bar" style={{ width: `${(rate.aer_pct / top) * 100}%` }} />}
                  </td>
                  <td>{rate ? tenureLabel(rate) : ""}</td>
                  <td className="num">{rate ? pct(rate.nominal_pct) : ""}</td>
                  <td className="note">
                    {rate ? rate.note || "Standard" : ""}
                    {ceiling && institution.type === "finance" && (
                      <span className="muted"> · ceiling {pct(ceiling.nominal)}</span>
                    )}
                  </td>
                  <RatingCells institution={institution} />
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function GridView({ institutions, data }: { institutions: Institution[]; data: TrackerData }) {
  const [sortBy, setSortBy] = useState(12);
  const cell = (i: Institution, m: number): Rate | null => bestOffer(i, m);
  const rows = [...institutions].sort((a, b) => (cell(b, sortBy)?.aer_pct ?? -1) - (cell(a, sortBy)?.aer_pct ?? -1));
  const best = Object.fromEntries(
    STANDARD_TENURES.map((m) => [m, Math.max(...institutions.map((i) => cell(i, m)?.aer_pct ?? 0))]),
  );

  return (
    <section>
      <div className="table-wrap">
        <table className="grid">
          <thead>
            <tr>
              <th>Institution</th>
              {STANDARD_TENURES.map((m) => (
                <th key={m} className="num">
                  <button className={sortBy === m ? "sort active" : "sort"} onClick={() => setSortBy(m)}>
                    {m}m {sortBy === m ? "↓" : ""}
                  </button>
                </th>
              ))}
              <th>Rating</th>
            </tr>
          </thead>
          <tbody>
            {data.ceiling && (
              <tr className="ceiling">
                <td>CBSL ceiling (finance companies)</td>
                {STANDARD_TENURES.map((m) => {
                  const c = ceilingFor(data.ceiling, m);
                  return (
                    <td key={m} className="num">
                      {c ? (
                        <>
                          <div>{pct(c.aer)}</div>
                          <div className="nominal">{pct(c.nominal)}</div>
                        </>
                      ) : (
                        ""
                      )}
                    </td>
                  );
                })}
                <td />
              </tr>
            )}
            {rows.map((institution) => (
              <tr key={institution.id}>
                <td>
                  <InstitutionName institution={institution} />
                </td>
                {STANDARD_TENURES.map((m) => {
                  const rate = cell(institution, m);
                  return (
                    <td key={m} className={rate && rate.aer_pct === best[m] ? "num top" : "num"}>
                      {rate && (
                        <>
                          <div className="aer">
                            {pct(rate.aer_pct)}
                            {rate.note ? "*" : ""}
                          </div>
                          <div className="nominal">{pct(rate.nominal_pct)}</div>
                        </>
                      )}
                    </td>
                  );
                })}
                <td className="note">
                  {institution.ratings.map((r) => r.rating).join(" / ") || <span className="muted">—</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function InstitutionName({ institution }: { institution: Institution }) {
  return (
    <div className="inst">
      <a href={institution.source_url} target="_blank" rel="noreferrer">
        {institution.name}
      </a>
      <span className={`tag ${institution.type}`}>{institution.type === "bank" ? "Bank" : "Finance"}</span>
      {institution.status === "stale" && (
        <span className="tag stale" title={institution.error}>
          Stale · {shortDate(institution.last_success)}
        </span>
      )}
      {institution.status === "no_data" && (
        <span className="tag stale" title={institution.error}>
          No data
        </span>
      )}
    </div>
  );
}

function RatingCells({ institution }: { institution: Institution }) {
  const ratings = institution.ratings;
  if (ratings.length === 0) {
    return (
      <td colSpan={3} className="muted">
        Not available
      </td>
    );
  }
  return (
    <>
      <td>
        {ratings.map((r) => (
          <div key={r.agency} className="rating">
            <a href={r.source_url} target="_blank" rel="noreferrer" title={r.source}>
              {r.rating}
            </a>
            <span className="muted"> {r.agency === "Lanka Rating Agency" ? "LRA" : "Fitch"}</span>
            {r.stale && <span className="tag stale">Stale</span>}
          </div>
        ))}
      </td>
      <td>
        {ratings.map((r) => (
          <div key={r.agency}>{r.outlook || <span className="muted">—</span>}</div>
        ))}
      </td>
      <td>
        {ratings.map((r) => (
          <div key={r.agency}>{shortDate(r.date) || <span className="muted">—</span>}</div>
        ))}
      </td>
    </>
  );
}
