const API_BASE = import.meta.env.VITE_API_BASE || "";

/**
 * Shared authenticated fetch wrapper.
 * Automatically adds the JWT token from localStorage and handles 401 redirects.
 */
async function authFetch(endpoint, options = {}) {
  const token = localStorage.getItem("wantok_token");
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    localStorage.removeItem("wantok_token");
    window.dispatchEvent(new Event("unauthorized"));
  }

  return response;
}

export async function login(email, password) {
  const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Authentication failed");
  }

  const data = await res.json();
  localStorage.setItem("wantok_token", data.access_token);
  return data;
}

export async function fetchDashboardSummary() {
  try {
    const res = await authFetch("/api/v1/dashboard/summary");
    if (!res.ok) throw new Error("Dashboard summary endpoint unavailable");
    return await res.json();
  } catch (err) {
    console.error("Dashboard API error, falling back to mockSummary:", err);
    return mockSummary();
  }
}

export async function listBorrowers() {
  const res = await authFetch("/api/v1/borrowers");
  if (!res.ok) throw new Error("Failed to fetch borrowers");
  return await res.json();
}

export async function createBorrower(data) {
  const res = await authFetch("/api/v1/borrowers", {
    method: "POST",
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to create borrower");
  }
  return await res.json();
}

export async function listLoans() {
  const res = await authFetch("/api/v1/loans");
  if (!res.ok) throw new Error("Failed to fetch loans");
  return await res.json();
}

export async function createLoan(data) {
  const res = await authFetch("/api/v1/loans", {
    method: "POST",
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to issue loan");
  }
  return await res.json();
}

export async function recordRepayment(loanId, amount, notes) {
  const res = await authFetch(`/api/v1/loans/${loanId}/repayments`, {
    method: "POST",
    body: JSON.stringify({ amount: parseFloat(amount), notes }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to record repayment");
  }
  return await res.json();
}

export async function listCollateral() {
  const res = await authFetch("/api/v1/collateral");
  if (!res.ok) throw new Error("Failed to fetch collateral logs");
  return await res.json();
}

export async function createCollateral(data) {
  const res = await authFetch("/api/v1/collateral", {
    method: "POST",
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to log collateral");
  }
  return await res.json();
}

export async function updateCollateralStatus(id, custodyStatus) {
  const res = await authFetch(`/api/v1/collateral/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ custody_status: custodyStatus }),
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Failed to update collateral custody status");
  }
  return await res.json();
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
