import fs from "node:fs";
import path from "node:path";
import type { Institution, TrackerData } from "./types";

// Data files live at the repository root and are refreshed by GitHub Actions.
const DATA_DIR = path.join(process.cwd(), "..", "data");

function readJson<T>(name: string, fallback: T): T {
  try {
    return JSON.parse(fs.readFileSync(path.join(DATA_DIR, name), "utf8")) as T;
  } catch {
    return fallback;
  }
}

export function loadData(): TrackerData {
  const latest = readJson<{ updated_at?: string; institutions: Record<string, Omit<Institution, "ratings">> }>(
    "latest.json",
    { institutions: {} },
  );
  const ratings = readJson<{ updated_at?: string; institutions: Record<string, Institution["ratings"]> }>(
    "ratings.json",
    { institutions: {} },
  );
  return {
    updatedAt: latest.updated_at ?? "",
    ratingsUpdatedAt: ratings.updated_at ?? "",
    institutions: Object.values(latest.institutions).map((inst) => ({
      ...inst,
      ratings: ratings.institutions[inst.id] ?? [],
    })),
    ceiling: readJson("cbsl.json", null),
  };
}
