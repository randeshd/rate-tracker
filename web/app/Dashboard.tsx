"use client";

import { type ReactNode, useState, useSyncExternalStore } from "react";
import type { Institution, Rate, TrackerData } from "@/lib/types";
import {
  STANDARD_TENURES,
  type Offer,
  bestOffer,
  ceilingFor,
  institutionsAboveCeiling,
  monthsLabel,
  offersForTenure,
  otherTenures,
  pct,
  shortDate,
  tenureLabel,
  topOffer,
} from "@/lib/rates";
import Logo from "./Logo";

const DIRECTIONS_URL =
  "https://www.cbsl.gov.lk/en/laws/directions-circulars-guidelines-for-non-banks";

// Keep in step with the phone breakpoint in globals.css
const PHONE_QUERY = "(max-width: 760px)";

type View = "tenure" | "grid" | "best";
type TypeFilter = "all" | "bank" | "finance";

const VIEWS: { id: View; label: string; icon: ReactNode }[] = [
  {
    id: "tenure",
    label: "By tenure",
    icon: (
      <>
        <rect x="3" y="5" width="18" height="16" rx="4" />
        <path d="M8 3v4M16 3v4M3 11h18" />
      </>
    ),
  },
  {
    id: "grid",
    label: "All tenures",
    icon: (
      <>
        <rect x="3" y="3" width="7.5" height="7.5" rx="2" />
        <rect x="13.5" y="3" width="7.5" height="7.5" rx="2" />
        <rect x="3" y="13.5" width="7.5" height="7.5" rx="2" />
        <rect x="13.5" y="13.5" width="7.5" height="7.5" rx="2" />
      </>
    ),
  },
  {
    id: "best",
    label: "Best AER",
    icon: (
      <path d="M12 3l2.7 5.6 6.1.8-4.5 4.3 1.1 6.1L12 16.9l-5.4 2.9 1.1-6.1L3.2 9.4l6.1-.8L12 3z" />
    ),
  },
];

const TYPES: { id: TypeFilter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "bank", label: "Banks" },
  { id: "finance", label: "Finance companies" },
];

function useIsPhone(): boolean {
  return useSyncExternalStore(
    (onChange) => {
      const query = window.matchMedia(PHONE_QUERY);
      query.addEventListener("change", onChange);
      return () => query.removeEventListener("change", onChange);
    },
    () => window.matchMedia(PHONE_QUERY).matches,
    () => false,
  );
}

export default function Dashboard({ data }: { data: TrackerData }) {
  const [view, setView] = useState<View>("tenure");
  const [tenure, setTenure] = useState(12);
  const [sortBy, setSortBy] = useState(12);
  const [type, setType] = useState<TypeFilter>("all");

  const institutions = data.institutions.filter(
    (i) => type === "all" || i.type === type,
  );
  const others = otherTenures(data.institutions);
  const best = view === "best";
  const grid = view === "grid";

  const rows: Offer[] = best
    ? institutions
        .flatMap((institution) => {
          const rate = bestOffer(institution);
          return rate ? [{ institution, rate }] : [];
        })
        .sort((a, b) => b.rate.aer_pct - a.rate.aer_pct)
    : offersForTenure(institutions, tenure);

  // The tenure the summary figures describe; undefined means any tenure
  const scope = best ? undefined : grid ? sortBy : tenure;
  const byType = (t: Institution["type"]) =>
    data.institutions.filter((i) => i.type === t);
  // Best overall (card on desktop, header figure on phones): fixed, whatever
  // view, tenure or type is selected
  const highest = topOffer(data.institutions);

  const newDirections = data.ceiling?.unreviewed_directions ?? [];
  const aboveCeiling = institutionsAboveCeiling(
    data.institutions,
    data.ceiling,
  );
  const ceilingDoubt = newDirections.length > 0 || aboveCeiling.length > 0;

  return (
    <div className="page">
      <div className="top">
        <header className="hero">
          <div className="brand-row">
            <div className="brand">
              <Logo inverse />
              <span>Rate Tracker</span>
            </div>
            <span className="updated">
              <span className="wide">Updated </span>
              {shortDate(data.updatedAt) || "—"}
            </span>
          </div>
          <h1 className="headline">
            Find where your fixed deposit <em>earns the most.</em>
          </h1>
          <div className="hero-best">
            <div className="hero-best-label">Highest AER on offer</div>
            <div className="hero-best-value">
              {highest ? pct(highest.rate.aer_pct) : "–"}
            </div>
            <div className="hero-best-name">
              {highest ? (
                <>
                  {highest.institution.name}{" "}
                  <span>
                    · {tenureLabel(highest.rate)} ·{" "}
                    {pct(highest.rate.nominal_pct)} p.a. nominal
                  </span>
                </>
              ) : (
                "No offers"
              )}
            </div>
          </div>
        </header>

        <section className="summary" aria-label="Top rates">
          <div className="summary-label">
            Top rates · {scope ? monthsLabel(scope) : "any tenure"}
          </div>
          <div className="cards">
            <SummaryCard
              label="Best overall · any tenure"
              tone="lime overall"
              offer={highest}
            />
            <SummaryCard
              label="Best bank"
              tone="lavender"
              offer={topOffer(byType("bank"), scope)}
            />
            <SummaryCard
              label="Best finance company"
              tone="pink"
              offer={topOffer(byType("finance"), scope)}
            />
          </div>
        </section>
      </div>

      <main className="content">
        {ceilingDoubt && (
          <p className="warning">
            <svg
              width="22"
              height="22"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M12 3 2 20h20L12 3z" />
              <path d="M12 10v5" />
              <path d="M12 17.5v.5" />
            </svg>
            <span>
              The CBSL ceiling may be out of date.{" "}
              {newDirections.length > 0 ? (
                <>
                  CBSL has published{" "}
                  <a
                    href={newDirections[0].url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    a new direction on deposit rates
                  </a>
                  . Open it, then ask Claude to update the ceiling margins with
                  the table in that document.
                </>
              ) : (
                <>
                  {aboveCeiling.map((i) => i.name).join(", ")}{" "}
                  {aboveCeiling.length === 1 ? "is" : "are"} advertising above
                  it. Check{" "}
                  <a href={DIRECTIONS_URL} target="_blank" rel="noreferrer">
                    CBSL&apos;s directions
                  </a>{" "}
                  for a new one on maximum deposit rates, then ask Claude to
                  update the ceiling margins.
                </>
              )}
            </span>
          </p>
        )}

        <div className="controls">
          <div className="views">
            {VIEWS.map((v) => (
              <button
                key={v.id}
                className={view === v.id ? "active" : ""}
                aria-pressed={view === v.id}
                onClick={() => setView(v.id)}
              >
                {v.label}
              </button>
            ))}
          </div>
          <div className="types">
            {TYPES.map((t) => (
              <button
                key={t.id}
                className={type === t.id ? "active" : ""}
                aria-pressed={type === t.id}
                onClick={() => setType(t.id)}
              >
                {t.label}
              </button>
            ))}
          </div>
          {view === "tenure" && (
            <div className="pills">
              {STANDARD_TENURES.map((m) => (
                <button
                  key={m}
                  className={tenure === m ? "pill active" : "pill"}
                  aria-pressed={tenure === m}
                  onClick={() => setTenure(m)}
                >
                  {monthsLabel(m)}
                </button>
              ))}
              <select
                aria-label="Other tenures"
                className={others.includes(tenure) ? "pill active" : "pill"}
                value={others.includes(tenure) ? tenure : ""}
                onChange={(e) =>
                  e.target.value && setTenure(Number(e.target.value))
                }
              >
                <option value="">Other</option>
                {others.map((m) => (
                  <option key={m} value={m}>
                    {monthsLabel(m)}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {grid ? (
          <Grid
            institutions={institutions}
            data={data}
            sortBy={sortBy}
            setSortBy={setSortBy}
          />
        ) : (
          <div className="scroll">
            <div className={best ? "list with-tenure" : "list"}>
              <div className="list-head" aria-hidden="true">
                <span />
                <span>Institution</span>
                {best && <span>Tenure</span>}
                <span className="num">Nominal</span>
                <span className="num">AER</span>
                <span className="rating">
                  <span>Rating</span>
                  <span>Outlook</span>
                  <span>Rated</span>
                </span>
              </div>
              <ol>
                {rows.map(({ institution, rate }, index) => (
                  <li
                    key={`${institution.id}-${rate.tenure_months}-${rate.note}`}
                    className={index === 0 ? "row first" : "row"}
                  >
                    <span className="rank">{index + 1}</span>
                    <div className="main">
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
                      {(best || rate.note) && (
                        <div className="note">
                          {best && (
                            <span className="narrow">
                              {tenureLabel(rate)}
                              {rate.note && " · "}
                            </span>
                          )}
                          {rate.note}
                        </div>
                      )}
                    </div>
                    {best && (
                      <span className="tenure">{tenureLabel(rate)}</span>
                    )}
                    <span className="nominal num">
                      {pct(rate.nominal_pct)}
                      <span className="narrow"> nominal</span>
                    </span>
                    <span className="aer num">
                      <span>{pct(rate.aer_pct)}</span>
                    </span>
                    <Ratings institution={institution} />
                  </li>
                ))}
              </ol>
              {rows.length === 0 && <p className="empty">No offers</p>}
            </div>
          </div>
        )}
      </main>

      <nav className="tabbar" aria-label="Views">
        {VIEWS.map((v) => (
          <button
            key={v.id}
            className={view === v.id ? "active" : ""}
            aria-label={v.label}
            aria-pressed={view === v.id}
            onClick={() => setView(v.id)}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              {v.icon}
            </svg>
            {view === v.id && <span>{v.label}</span>}
          </button>
        ))}
      </nav>
    </div>
  );
}

function SummaryCard({
  label,
  tone,
  offer,
}: {
  label: string;
  tone: string;
  offer: Offer | null;
}) {
  const [nominal, setNominal] = useState(false);
  if (!offer) {
    return (
      <div className={`card ${tone}`}>
        <span className="card-label">{label}</span>
        <span className="card-figure">
          <span className="card-value">–</span>
        </span>
        <span className="card-name">No offers</span>
      </div>
    );
  }
  const { institution, rate } = offer;
  return (
    <button
      className={`card ${tone}`}
      aria-pressed={nominal}
      onClick={() => setNominal(!nominal)}
    >
      <span className="card-label">{label}</span>
      <span className="card-figure">
        <span className="card-value">
          {pct(nominal ? rate.nominal_pct : rate.aer_pct)}
        </span>
        <span className="tag">{nominal ? "p.a. nominal" : "AER"}</span>
      </span>
      <span className="card-name">{institution.name}</span>
      <span className="card-sub">
        {tenureLabel(rate)}
        {rate.note && <span className="wide"> · {rate.note}</span>}
      </span>
      <span className="card-hint">
        {nominal ? "Show AER" : "Show nominal rate p.a."}
      </span>
    </button>
  );
}

function Ratings({ institution }: { institution: Institution }) {
  if (institution.ratings.length === 0) {
    return (
      <div className="ratings">
        <div className="rating">
          <span>
            <span className="wide">–</span>
            <span className="narrow">No rating</span>
          </span>
          <span className="blank">–</span>
          <span className="blank">–</span>
        </div>
      </div>
    );
  }
  return (
    <div className="ratings">
      {institution.ratings.map((r) => (
        <div className="rating" key={r.agency}>
          <span>
            <strong>{r.rating}</strong>{" "}
            <small>
              {r.agency === "Lanka Rating Agency" ? "LRA" : "Fitch"}
            </small>
          </span>
          <span className={r.outlook ? "" : "blank"}>{r.outlook || "–"}</span>
          <span className={r.date ? "date" : "date blank"}>
            {shortDate(r.date) || "–"}
          </span>
        </div>
      ))}
    </div>
  );
}

function Grid({
  institutions,
  data,
  sortBy,
  setSortBy,
}: {
  institutions: Institution[];
  data: TrackerData;
  sortBy: number;
  setSortBy: (months: number) => void;
}) {
  const isPhone = useIsPhone();
  // On phones a cell shows only the AER; tapping it reveals the nominal rate
  const [selected, setSelected] = useState<{
    id: string;
    months: number;
  } | null>(null);
  const aer = (i: Institution, m: number) => bestOffer(i, m)?.aer_pct ?? -1;
  const rows = [...institutions].sort(
    (a, b) => aer(b, sortBy) - aer(a, sortBy),
  );
  const top = Object.fromEntries(
    STANDARD_TENURES.map((m) => [m, Math.max(...rows.map((i) => aer(i, m)))]),
  );

  const cell = (rate: Rate | null, m: number) => (
    <>
      <span className="cell-tenure">{m}m</span>
      <span className="cell-aer">
        {rate ? (
          <>
            {rate.aer_pct.toFixed(2)}
            <span className="wide">%</span>
          </>
        ) : (
          "–"
        )}
      </span>
      <span className="cell-nominal">{rate && pct(rate.nominal_pct)}</span>
    </>
  );

  return (
    <div className="scroll">
      <div className="grid">
        <div className="grid-head">
          <span className="wide">Institution</span>
          <span className="narrow">Sort by tenure</span>
          <div className="cells">
            {STANDARD_TENURES.map((m) => (
              <button
                key={m}
                className={sortBy === m ? "active" : ""}
                aria-pressed={sortBy === m}
                onClick={() => setSortBy(m)}
              >
                {m}m{sortBy === m && <span className="wide"> ↓</span>}
              </button>
            ))}
          </div>
        </div>
        <div className="grid-row ceiling-row">
          <div className="grid-name">
            CBSL ceiling{" "}
            <span>
              <span className="wide">(</span>finance companies, nominal
              <span className="narrow"> p.a.</span>
              <span className="wide">)</span>
            </span>
          </div>
          <div className="cells">
            {STANDARD_TENURES.map((m) => {
              const c = ceilingFor(data.ceiling, m);
              return (
                <div key={m} className="cell">
                  <span className="cell-tenure">{m}m</span>
                  <span className="cell-aer">
                    {c ? (
                      <>
                        {c.nominal.toFixed(2)}
                        <span className="wide">%</span>
                      </>
                    ) : (
                      "–"
                    )}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
        {rows.map((institution) => {
          const open = selected?.id === institution.id ? selected : null;
          const openRate = open && bestOffer(institution, open.months);
          return (
            <div className="grid-row" key={institution.id}>
              <a
                className="name grid-name"
                href={institution.source_url}
                target="_blank"
                rel="noreferrer"
              >
                {institution.name}
              </a>
              <div className="cells">
                {STANDARD_TENURES.map((m) => {
                  const rate = bestOffer(institution, m);
                  const isTop = rate !== null && rate.aer_pct === top[m];
                  const isOpen = open?.months === m;
                  const className = `cell${isTop ? " best" : ""}${isOpen ? " open" : ""}`;
                  return isPhone ? (
                    <button
                      key={m}
                      className={className}
                      aria-pressed={isOpen}
                      onClick={() =>
                        setSelected(
                          isOpen ? null : { id: institution.id, months: m },
                        )
                      }
                    >
                      {cell(rate, m)}
                    </button>
                  ) : (
                    <div key={m} className={className}>
                      {cell(rate, m)}
                    </div>
                  );
                })}
              </div>
              {isPhone && open && (
                <div className="detail">
                  <div>
                    <span>{monthsLabel(open.months)} · nominal rate p.a.</span>
                    <strong>
                      {openRate ? pct(openRate.nominal_pct) : "No offer"}
                    </strong>
                  </div>
                  {openRate && (
                    <div className="detail-sub">
                      <span>{openRate.note}</span>
                      <span>{pct(openRate.aer_pct)} AER</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
        <p className="grid-key">
          <span className="wide">
            Each cell shows AER, with the nominal rate below. Green marks the
            best AER for that tenure.
          </span>
          <span className="narrow">
            AER in % for each tenure. Tap a rate to see its nominal rate p.a.
            Green marks the best for that tenure.
          </span>
        </p>
      </div>
    </div>
  );
}
