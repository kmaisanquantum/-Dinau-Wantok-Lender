const RISK_STYLES = {
  high: { dot: "bg-risk-high", text: "text-risk-high", label: "High Risk" },
  watch: { dot: "bg-risk-watch", text: "text-risk-watch", label: "Watch" },
  none: { dot: "bg-risk-none", text: "text-risk-none", label: "Clear" },
};

export default function RiskFlagList({ accounts }) {
  return (
    <div className="bg-white/60 border border-ledger-rule rounded-sm">
      <div className="px-4 py-3 border-b border-ledger-rule flex items-baseline justify-between">
        <h2 className="font-display text-xl uppercase tracking-wide text-kina-deep">
          At-Risk Accounts
        </h2>
        <span className="text-xs text-ledger-ink/50">{accounts.length} flagged</span>
      </div>
      <ul className="divide-y divide-ledger-rule">
        {accounts.map((acc) => {
          const style = RISK_STYLES[acc.riskLevel] ?? RISK_STYLES.none;
          return (
            <li key={acc.id} className="flex items-center gap-3 px-4 py-3">
              <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${style.dot}`} />
              <div className="flex-1 min-w-0">
                <div className="font-medium text-sm truncate">{acc.borrowerLabel}</div>
                <div className="text-xs text-ledger-ink/60">
                  Overdue {acc.daysOverdue}d · K{acc.outstanding.toLocaleString()}
                </div>
              </div>
              <span className={`text-xs font-display uppercase tracking-wide ${style.text}`}>
                {style.label}
              </span>
            </li>
          );
        })}
        {accounts.length === 0 && (
          <li className="px-4 py-6 text-center text-sm text-ledger-ink/50">
            No accounts currently flagged.
          </li>
        )}
      </ul>
    </div>
  );
}
