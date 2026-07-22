import { useState, useEffect } from "react";
import { listBorrowers, createBorrower } from "../lib/api";

export default function Borrowers() {
  const [borrowers, setBorrowers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Form State
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [nationalId, setNationalId] = useState("");
  const [address, setAddress] = useState("");
  const [employer, setEmployer] = useState("");
  const [isPublicServant, setIsPublicServant] = useState(false);
  const [alescoFileNumber, setAlescoFileNumber] = useState("");
  const [riskFlag, setRiskFlag] = useState("none");

  useEffect(() => {
    fetchBorrowers();
  }, []);

  const fetchBorrowers = async () => {
    try {
      setLoading(true);
      const data = await listBorrowers();
      setBorrowers(data);
    } catch (err) {
      setError("Failed to load borrowers list.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!fullName || !phone) {
      setError("Full Name and Phone Number are required.");
      return;
    }

    try {
      const payload = {
        full_name: fullName,
        phone,
        national_id: nationalId || null,
        address: address || null,
        employer: employer || null,
        is_public_servant: isPublicServant,
        alesco_file_number: isPublicServant ? alescoFileNumber : null,
        risk_flag: riskFlag,
      };

      await createBorrower(payload);
      setSuccess("Borrower successfully registered!");

      // Reset form
      setFullName("");
      setPhone("");
      setNationalId("");
      setAddress("");
      setEmployer("");
      setIsPublicServant(false);
      setAlescoFileNumber("");
      setRiskFlag("none");

      // Refresh list
      fetchBorrowers();
    } catch (err) {
      setError(err.message || "Failed to create borrower.");
    }
  };

  return (
    <div className="space-y-6 font-sans">
      <header className="mb-6">
        <div className="text-xs uppercase tracking-widest text-bilum-teal font-medium">
          Management Console
        </div>
        <h1 className="font-display text-3xl font-semibold text-kina-deep">
          Borrowers Ledger
        </h1>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Register New Borrower Form */}
        <div className="bg-white/70 border border-ledger-rule rounded-sm p-6 h-fit shadow-sm">
          <h2 className="font-display text-xl uppercase tracking-wide text-kina-deep mb-4">
            Register Borrower
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
                Full Name (Plaintext)
              </label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. John Kopi"
                className="w-full px-3 py-1.5 border border-ledger-rule rounded-sm text-sm bg-ledger-paper/50 focus:ring-bilum-teal focus:border-bilum-teal"
              />
            </div>

            <div>
              <label className="block text-xs font-display uppercase tracking-wider text-ledger-ink/70 mb-1">
                Phone Number
              </label>
              <input
                type="text"
                required
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="e.g. +675 7123 4567"
                className="w-full px-3 py-1.5 border border-ledger-rule rounded-sm text-sm bg-ledger-paper/50 focus:ring-bilum-teal focus:border-bilum-teal"
              />
            </div>

            <div>
              <label className="block text-xs font-display uppercase tracking-wider text-ledger-ink/70 mb-1">
                National ID Number (Optional)
              </label>
              <input
                type="text"
                value={nationalId}
                onChange={(e) => setNationalId(e.target.value)}
                placeholder="e.g. NID-441-229"
                className="w-full px-3 py-1.5 border border-ledger-rule rounded-sm text-sm bg-ledger-paper/50 focus:ring-bilum-teal focus:border-bilum-teal"
              />
            </div>

            <div>
              <label className="block text-xs font-display uppercase tracking-wider text-ledger-ink/70 mb-1">
                Residential Address (Optional)
              </label>
              <input
                type="text"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="e.g. Mt Hagen counter, Western Highlands"
                className="w-full px-3 py-1.5 border border-ledger-rule rounded-sm text-sm bg-ledger-paper/50 focus:ring-bilum-teal focus:border-bilum-teal"
              />
            </div>

            <div>
              <label className="block text-xs font-display uppercase tracking-wider text-ledger-ink/70 mb-1">
                Employer Name (Optional)
              </label>
              <input
                type="text"
                value={employer}
                onChange={(e) => setEmployer(e.target.value)}
                placeholder="e.g. Treasury Dept"
                className="w-full px-3 py-1.5 border border-ledger-rule rounded-sm text-sm bg-ledger-paper/50 focus:ring-bilum-teal focus:border-bilum-teal"
              />
            </div>

            <div className="flex items-center gap-2 py-1">
              <input
                type="checkbox"
                id="isPublicServant"
                checked={isPublicServant}
                onChange={(e) => setIsPublicServant(e.target.checked)}
                className="h-4 w-4 rounded border-ledger-rule text-bilum-teal focus:ring-bilum-teal"
              />
              <label htmlFor="isPublicServant" className="text-xs font-display uppercase tracking-wider text-ledger-ink/80 select-none">
                PNG Public Servant (Alesco Payroll)
              </label>
            </div>

            {isPublicServant && (
              <div className="bg-bilum-teal/5 border border-bilum-teal/20 p-3 rounded-sm space-y-2">
                <label className="block text-xs font-display uppercase tracking-wider text-ledger-ink/70 mb-1">
                  Alesco File Number
                </label>
                <input
                  type="text"
                  required={isPublicServant}
                  value={alescoFileNumber}
                  onChange={(e) => setAlescoFileNumber(e.target.value)}
                  placeholder="e.g. EMP-98124"
                  className="w-full px-3 py-1.5 border border-ledger-rule rounded-sm text-sm bg-white focus:ring-bilum-teal focus:border-bilum-teal"
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-display uppercase tracking-wider text-ledger-ink/70 mb-1">
                Risk Classification Flag
              </label>
              <select
                value={riskFlag}
                onChange={(e) => setRiskFlag(e.target.value)}
                className="w-full px-3 py-1.5 border border-ledger-rule rounded-sm text-sm bg-ledger-paper/50 focus:ring-bilum-teal focus:border-bilum-teal"
              >
                <option value="none">Clear (No known risk)</option>
                <option value="watch">Watch (Mild concern)</option>
                <option value="high">High Risk (Severe concern)</option>
              </select>
            </div>

            <button
              type="submit"
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-sm shadow-sm text-sm font-display uppercase tracking-wider font-semibold text-ledger-paper bg-bilum-teal hover:bg-bilum-teal/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-bilum-teal"
            >
              Register Borrower
            </button>
          </form>
        </div>

        {/* Right Columns: Registered Borrowers List */}
        <div className="lg:col-span-2 bg-white/60 border border-ledger-rule rounded-sm p-6 shadow-sm">
          <h2 className="font-display text-xl uppercase tracking-wide text-kina-deep mb-4">
            Registered Borrowers ({borrowers.length})
          </h2>

          {loading ? (
            <div className="text-center py-8 text-ledger-ink/50">Loading borrowers list…</div>
          ) : borrowers.length === 0 ? (
            <div className="text-center py-8 text-ledger-ink/50 border border-dashed border-ledger-rule rounded-sm">
              No borrowers registered under your tenant account yet.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-ledger-rule">
                <thead>
                  <tr className="text-left text-xs font-display uppercase tracking-wider text-ledger-ink/50">
                    <th className="pb-3">Name</th>
                    <th className="pb-3">Hashed Phone</th>
                    <th className="pb-3">Type</th>
                    <th className="pb-3">Risk Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ledger-rule text-sm">
                  {borrowers.map((b) => (
                    <tr key={b.id} className="hover:bg-ledger-paper/40">
                      <td className="py-3 font-medium text-kina-deep">
                        {b.full_name}
                        {b.is_public_servant && (
                          <div className="text-[10px] text-bilum-teal uppercase font-semibold tracking-wider">
                            Alesco File: {b.alesco_file_number}
                          </div>
                        )}
                        {(b.address || b.employer) && (
                          <div className="text-xs text-ledger-ink/50 mt-0.5">
                            {b.employer && `Employer: ${b.employer}`}
                            {b.address && b.employer && " · "}
                            {b.address && `Location: ${b.address}`}
                          </div>
                        )}
                      </td>
                      <td className="py-3 text-xs font-mono text-ledger-ink/60 select-all">
                        {b.phone_hash.substring(0, 16)}…
                      </td>
                      <td className="py-3">
                        <span className={`text-xs px-2 py-0.5 rounded-sm font-semibold uppercase tracking-wide ${
                          b.is_public_servant
                            ? "bg-bilum-teal/10 text-bilum-teal"
                            : "bg-ledger-ink/10 text-ledger-ink/80"
                        }`}>
                          {b.is_public_servant ? "Public Servant" : "Standard"}
                        </span>
                      </td>
                      <td className="py-3">
                        <span className={`text-xs font-display uppercase tracking-wide font-semibold ${
                          b.risk_flag === "high"
                            ? "text-risk-high"
                            : b.risk_flag === "watch"
                            ? "text-risk-watch"
                            : "text-risk-none"
                        }`}>
                          {b.risk_flag === "high" ? "🚨 High Risk" : b.risk_flag === "watch" ? "⚠️ Watch" : "✅ Clear"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
