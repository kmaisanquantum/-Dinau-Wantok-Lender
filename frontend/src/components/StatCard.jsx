/**
 * StatCard — the dashboard's signature element.
 * Styled as a stamped ledger-book entry: a heavy rule above the number,
 * a small "stamped" corner tab carrying the trend, and condensed
 * numerals sized for a fast glance across a counter in bright light.
 */
export default function StatCard({ label, value, sublabel, tone = "ink", tabText }) {
  const toneClasses = {
    ink: "text-ledger-ink",
    gold: "text-kina-gold",
    teal: "text-bilum-teal",
    risk: "text-risk-high",
  };

  return (
    <div className="relative bg-white/60 border border-ledger-rule rounded-sm px-5 pt-6 pb-4 shadow-sm">
      {tabText && (
        <span className="absolute -top-3 left-4 bg-kina-deep text-ledger-paper text-[11px] font-display uppercase tracking-wider px-2 py-0.5 rounded-sm shadow">
          {tabText}
        </span>
      )}
      <div className="text-xs uppercase tracking-wider text-ledger-ink/60 font-medium mb-1">
        {label}
      </div>
      <div className={`font-display text-4xl font-semibold leading-none ${toneClasses[tone]}`}>
        {value}
      </div>
      {sublabel && (
        <div className="mt-2 text-xs text-ledger-ink/50 border-t border-ledger-rule pt-2">
          {sublabel}
        </div>
      )}
    </div>
  );
}
