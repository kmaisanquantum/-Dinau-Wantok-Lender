import { useState, useEffect } from "react";
import { listCollateral, listLoans, createCollateral, updateCollateralStatus } from "../lib/api";

const CATEGORIES = {
  phone: "📱 Phone",
  laptop: "💻 Laptop",
  tool: "🔧 Tool",
  jewelry: "💍 Jewelry",
  document: "📄 Document",
  other: "📦 Other",
};

const STATUS_LABELS = {
  in_vault: "In Vault",
  returned: "Returned",
  forfeited: "Forfeited",
  sold: "Sold",
  disputed: "Disputed",
};

export default function Collateral() {
  const [collateral, setCollateral] = useState([]);
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Form State
  const [selectedLoanId, setSelectedLoanId] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("other");
  const [value, setValue] = useState("");
  const [location, setLocation] = useState("");
  const [custodyStatus, setCustodyStatus] = useState("in_vault");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [collateralData, loansData] = await Promise.all([
        listCollateral(),
        listLoans(),
      ]);
      setCollateral(collateralData);
      setLoans(loansData);
    } catch (err) {
      setError("Failed to load collateral logs or active loans.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!selectedLoanId || !description || !value || !location) {
      setError("Please fill out all required fields.");
      return;
    }

    try {
      const payload = {
        loan_id: selectedLoanId,
        item_description: description,
        item_category: category,
        estimated_value: parseFloat(value),
        storage_location: location,
        custody_status: custodyStatus,
      };

      await createCollateral(payload);
      setSuccess("Collateral record successfully added and logged!");

      // Reset form
      setSelectedLoanId("");
      setDescription("");
      setCategory("other");
      setValue("");
      setLocation("");
      setCustodyStatus("in_vault");

      // Refresh
      fetchData();
    } catch (err) {
      setError(err.message || "Failed to log collateral.");
    }
  };

  const handleUpdateStatus = async (id, newStatus) => {
    try {
      setError("");
      await updateCollateralStatus(id, newStatus);
      fetchData();
    } catch (err) {
      setError(err.message || "Failed to update custody status.");
    }
  };

  return (
    <div className="space-y-6 font-sans">
      <header className="mb-6">
        <div className="text-xs uppercase tracking-widest text-bilum-teal font-medium">
          Vault Control
        </div>
        <h1 className="font-display text-3xl font-semibold text-kina-deep">
          Collateral Vault Ledger
        </h1>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Log New Collateral Form */}
        <div className="bg-white/70 border border-ledger-rule rounded-sm p-6 h-fit shadow-sm">
          <h2 className="font-display text-xl uppercase tracking-wide text-kina-deep mb-4">
            Log Collateral Item
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="rounded-sm bg-risk-high/10 border border-risk-high p-3 text-xs text-risk-high font-medium">
                ⚠️ {error}
              </div>
            )}
            {success && (
              <div className="rounded-sm bg-risk-none/10 border border-risk-none p-3 text-xs text-risk-none font-medium">
                ✅ {success}
              </div>
            )}

            <div>
              <label className="block text-xs font-display uppercase tracking-wider text-ledger-ink/70 mb-1">
                Select Active Loan
              </label>
              <select
                required
                value={selectedLoanId}
                onChange={(e) => setSelectedLoanId(e.target.value)}
                className="w-full px-3 py-1.5 border border-ledger-rule rounded-sm text-sm bg-ledger-paper/50 focus:ring-bilum-teal focus:border-bilum-teal"
              >
                <option value="">-- Choose Loan --</option>
                {loans.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.borrower_name} (K{l.outstanding_balance.toLocaleString()} outstanding)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-display uppercase tracking-wider text-ledger-ink/70 mb-1">
                Item Description
              </label>
              <input
                type="text"
                required
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g. Samsung A14, IMEI ends 4471"
                className="w-full px-3 py-1.5 border border-ledger-rule rounded-sm text-sm bg-ledger-paper/50 focus:ring-bilum-teal focus:border-bilum-teal"
              />
            </div>

            <div>
              <label className="block text-xs font-display uppercase tracking-wider text-ledger-ink/70 mb-1">
                Item Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-1.5 border border-ledger-rule rounded-sm text-sm bg-ledger-paper/50 focus:ring-bilum-teal focus:border-bilum-teal"
              >
                <option value="phone">📱 Phone</option>
                <option value="laptop">💻 Laptop</option>
                <option value="tool">🔧 Tool</option>
                <option value="jewelry">💍 Jewelry</option>
                <option value="document">📄 Document</option>
                <option value="other">📦 Other</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-display uppercase tracking-wider text-ledger-ink/70 mb-1">
                Estimated Value (Kina)
              </label>
              <input
                type="number"
                step="0.01"
                required
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder="e.g. 1500"
                className="w-full px-3 py-1.5 border border-ledger-rule rounded-sm text-sm bg-ledger-paper/50 focus:ring-bilum-teal focus:border-bilum-teal"
              />
            </div>

            <div>
              <label className="block text-xs font-display uppercase tracking-wider text-ledger-ink/70 mb-1">
                Storage Location Code
              </label>
              <input
                type="text"
                required
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. Vault A-3"
                className="w-full px-3 py-1.5 border border-ledger-rule rounded-sm text-sm bg-ledger-paper/50 focus:ring-bilum-teal focus:border-bilum-teal"
              />
            </div>

            <div>
              <label className="block text-xs font-display uppercase tracking-wider text-ledger-ink/70 mb-1">
                Initial Custody Status
              </label>
              <select
                value={custodyStatus}
                onChange={(e) => setCustodyStatus(e.target.value)}
                className="w-full px-3 py-1.5 border border-ledger-rule rounded-sm text-sm bg-ledger-paper/50 focus:ring-bilum-teal focus:border-bilum-teal"
              >
                <option value="in_vault">In Vault (Held securely)</option>
                <option value="returned">Returned to owner</option>
                <option value="forfeited">Forfeited</option>
                <option value="sold">Sold to recover balance</option>
                <option value="disputed">Disputed</option>
              </select>
            </div>

            <button
              type="submit"
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-sm shadow-sm text-sm font-display uppercase tracking-wider font-semibold text-ledger-paper bg-bilum-teal hover:bg-bilum-teal/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-bilum-teal"
            >
              Log Collateral Item
            </button>
          </form>
        </div>

        {/* Right Columns: Collateral logs management view */}
        <div className="lg:col-span-2 bg-white/60 border border-ledger-rule rounded-sm p-6 shadow-sm">
          <h2 className="font-display text-xl uppercase tracking-wide text-kina-deep mb-4">
            Items Logged in Vault ({collateral.length})
          </h2>

          {loading ? (
            <div className="text-center py-8 text-ledger-ink/50">Loading vault items…</div>
          ) : collateral.length === 0 ? (
            <div className="text-center py-8 text-ledger-ink/50 border border-dashed border-ledger-rule rounded-sm">
              No collateral logged in the vault.
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {collateral.map((item) => (
                <div
                  key={item.id}
                  className="bg-white border border-ledger-rule rounded-sm p-4 flex flex-col justify-between hover:shadow-sm transition-all"
                >
                  <div>
                    <div className="flex justify-between items-start gap-2">
                      <h3 className="font-medium text-sm text-kina-deep truncate">
                        {item.item_description}
                      </h3>
                      <span className="text-xs shrink-0 bg-ledger-paper px-2 py-0.5 rounded border border-ledger-rule">
                        {CATEGORIES[item.item_category] || "📦 Other"}
                      </span>
                    </div>

                    <div className="text-xs text-ledger-ink/60 mt-2 space-y-1">
                      <div>Location: <span className="font-semibold">{item.storage_location}</span></div>
                      <div>Est. Value: <span className="font-semibold text-bilum-teal">K{item.estimated_value.toLocaleString()}</span></div>
                      <div className="flex items-center gap-1.5 mt-2">
                        <span className="font-medium">Status:</span>
                        <span className={`text-[10px] px-2 py-0.5 rounded-sm font-bold uppercase tracking-wider ${
                          item.custody_status === "in_vault"
                            ? "bg-bilum-teal/10 text-bilum-teal"
                            : item.custody_status === "returned"
                            ? "bg-risk-none/10 text-risk-none"
                            : item.custody_status === "disputed"
                            ? "bg-risk-watch/10 text-risk-watch"
                            : "bg-risk-high/10 text-risk-high"
                        }`}>
                          {STATUS_LABELS[item.custody_status] || item.custody_status}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-ledger-rule flex gap-1.5 justify-end overflow-x-auto">
                    {item.custody_status !== "returned" && (
                      <button
                        onClick={() => handleUpdateStatus(item.id, "returned")}
                        className="bg-risk-none text-white text-[10px] uppercase font-display tracking-wider font-semibold px-2 py-1 rounded-sm shadow hover:bg-risk-none/90 shrink-0"
                      >
                        ↩️ Return
                      </button>
                    )}
                    {item.custody_status !== "in_vault" && (
                      <button
                        onClick={() => handleUpdateStatus(item.id, "in_vault")}
                        className="bg-bilum-teal text-white text-[10px] uppercase font-display tracking-wider font-semibold px-2 py-1 rounded-sm shadow hover:bg-bilum-teal/90 shrink-0"
                      >
                        📥 Vault
                      </button>
                    )}
                    {item.custody_status !== "forfeited" && (
                      <button
                        onClick={() => handleUpdateStatus(item.id, "forfeited")}
                        className="bg-risk-high text-white text-[10px] uppercase font-display tracking-wider font-semibold px-2 py-1 rounded-sm shadow hover:bg-risk-high/90 shrink-0"
                      >
                        ⚠️ Forfeit
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
