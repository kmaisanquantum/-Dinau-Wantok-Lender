const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

/**
 * Pulls the merchant dashboard summary. Real deployments should add a
 * `/api/v1/dashboard/summary` aggregation endpoint on the backend
 * (mirroring credit_check/sync/payslip routers) — this client falls
 * back to representative mock data so the UI is reviewable standalone
 * before that endpoint exists.
 */
export async function fetchDashboardSummary() {
  try {
    const token = localStorage.getItem("wantok_token");
    const res = await fetch(`${API_BASE}/api/v1/dashboard/summary`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new Error("summary endpoint unavailable");
    return await res.json();
  } catch {
    return mockSummary();
  }
}

function mockSummary() {
  return {
    tenantName: "Mt. Hagen Trust Finance",
    totalCapitalOut: 184250,
    activeLoanCount: 96,
    expectedFortnightlyRepayments: 21400,
    atRiskCount: 3,
    overdueCount: 2,
    defaultedCount: 1,
    collateralInVaultCount: 41,
    collateralValueEstimate: 62300,
    riskAccounts: [
      { id: "1", borrowerLabel: "Borrower •••482", riskLevel: "high", daysOverdue: 34, outstanding: 1250 },
      { id: "2", borrowerLabel: "Borrower •••117", riskLevel: "watch", daysOverdue: 9, outstanding: 480 },
      { id: "3", borrowerLabel: "Borrower •••905", riskLevel: "watch", daysOverdue: 4, outstanding: 220 },
    ],
    collateralItems: [
      { id: "a", description: "Samsung A14, IMEI •••4471", category: "phone", storageLocation: "Vault A-3", status: "in_vault" },
      { id: "b", description: "HP 240 G8 laptop", category: "laptop", storageLocation: "Vault A-1", status: "in_vault" },
      { id: "c", description: "Stihl chainsaw", category: "tool", storageLocation: "Vault B-2", status: "disputed" },
      { id: "d", description: "Gold chain, 18ct", category: "jewelry", storageLocation: "Safe 1", status: "returned" },
    ],
  };
}
