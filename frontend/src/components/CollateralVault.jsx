const STATUS_STYLES = {
  in_vault: { text: "text-bilum-teal", label: "In Vault" },
  returned: { text: "text-risk-none", label: "Returned" },
  forfeited: { text: "text-risk-high", label: "Forfeited" },
  sold: { text: "text-ledger-ink/60", label: "Sold" },
  disputed: { text: "text-risk-watch", label: "Disputed" },
};

const CATEGORY_ICON = {
  phone: "📱",
  laptop: "💻",
  tool: "🔧",
  jewelry: "💍",
  document: "📄",
  other: "📦",
};

export default function CollateralVault({ items }) {
  return (
    <div className="bg-white/60 border border-ledger-rule rounded-sm">
      <div className="px-4 py-3 border-b border-ledger-rule flex items-baseline justify-between">
        <h2 className="font-display text-xl uppercase tracking-wide text-kina-deep">
          Collateral Vault
        </h2>
        <span className="text-xs text-ledger-ink/50">
          {items.filter((i) => i.status === "in_vault").length} items held
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-px bg-ledger-rule">
        {items.map((item) => {
          const style = STATUS_STYLES[item.status] ?? STATUS_STYLES.in_vault;
          return (
            <div key={item.id} className="bg-ledger-paper px-4 py-3 flex items-start gap-3">
              <span className="text-xl leading-none">{CATEGORY_ICON[item.category] ?? "📦"}</span>
              <div className="min-w-0 flex-1">
                <div className="text-sm font-medium truncate">{item.description}</div>
                <div className="text-xs text-ledger-ink/60">{item.storageLocation}</div>
              </div>
              <span className={`text-xs font-display uppercase tracking-wide shrink-0 ${style.text}`}>
                {style.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
