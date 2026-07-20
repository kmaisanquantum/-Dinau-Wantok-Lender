import { useEffect, useState } from "react";
import StatCard from "./StatCard.jsx";
import RiskFlagList from "./RiskFlagList.jsx";
import CollateralVault from "./CollateralVault.jsx";
import { fetchDashboardSummary } from "../lib/api.js";

/**
 * Lender/Merchant Dashboard — laid out for a counter-top tablet or
 * phone at a street lending desk: the four numbers that matter most
 * sit above the fold in one row, everything below is scannable
 * without scrolling on a 7" screen.
 */
export default function Dashboard() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchDashboardSummary().then(setData);
  }, []);

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center text-ledger-ink/50 font-display text-lg">
        Loading ledger…
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-ledger-paper px-4 py-6 sm:px-8 sm:py-8">
      <header className="mb-6">
        <div className="text-xs uppercase tracking-widest text-bilum-teal font-medium">
          Wantok Lender
        </div>
        <h1 className="font-display text-3xl sm:text-4xl font-semibold text-kina-deep">
          {data.tenantName} — Ledger Overview
        </h1>
      </header>

      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          label="Total Capital Out"
          value={`K${data.totalCapitalOut.toLocaleString()}`}
          sublabel={`Across ${data.activeLoanCount} active loans`}
          tone="ink"
          tabText="Live"
        />
        <StatCard
          label="Expected Fortnightly Repayments"
          value={`K${data.expectedFortnightlyRepayments.toLocaleString()}`}
          sublabel="Aligned to next pay cycle"
          tone="gold"
        />
        <StatCard
          label="At-Risk Accounts"
          value={data.atRiskCount}
          sublabel={`${data.overdueCount} overdue · ${data.defaultedCount} defaulted`}
          tone="risk"
        />
        <StatCard
          label="Collateral In Vault"
          value={data.collateralInVaultCount}
          sublabel={`Est. value K${data.collateralValueEstimate.toLocaleString()}`}
          tone="teal"
        />
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <RiskFlagList accounts={data.riskAccounts} />
        <CollateralVault items={data.collateralItems} />
      </section>
    </div>
  );
}
