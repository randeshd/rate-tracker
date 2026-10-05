/** The percent mark. `inverse` is the white tile used on the dark header. */
export default function Logo({ size = 44, inverse = false }: { size?: number; inverse?: boolean }) {
  const tile = inverse ? "#FFFFFF" : "#0E0E10";
  const glyph = inverse ? "#0E0E10" : "#FFFFFF";
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
      <rect width="64" height="64" rx="18" fill={tile} />
      <line x1="42" y1="18" x2="22" y2="46" stroke={glyph} strokeWidth="6" strokeLinecap="round" />
      <circle cx="22" cy="22" r="6" fill="none" stroke={glyph} strokeWidth="5" />
      <circle cx="43" cy="43" r="8" fill={inverse ? "#9CC00A" : "#D9F46B"} />
    </svg>
  );
}
