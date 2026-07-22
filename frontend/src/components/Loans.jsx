import { useState, useEffect } from "react";
import { listLoans, listBorrowers, createLoan, recordRepayment } from "../lib/api";

export default function Loans() {
  const [loans, setLoans] = useState([]);
  const [borrowers, setBorrowers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Issue Loan Form State
  const [selectedBorrowerId, setSelectedBorrowerId] = useState("");
  const [principal, setPrincipal] = useState("");
  const [interestBp, setInterestBp] = useState("1000"); // 10% default
  const [compoundingPeriod, setCompoundingPeriod] = useState("fortnightly");
  const [termPeriods, setTermPeriods] = useState("");

  // Public Servant payroll check state
  const [grossPay, setGrossPay] = useState("");
  const [totalDeductions, setTotalDeductions] = useState("");

  // Repayment State
  const [repaymentLoanId, setRepaymentLoanId] = useState(null);
  const [repaymentAmount, setRepaymentAmount] = useState("");
  const [repaymentNotes, setRepaymentNotes] = useState("");
  const [repaymentError, setRepaymentError] = useState("");

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [loansData, borrowersData] = await Promise.all([
        listLoans(),
        listBorrowers(),
      ]);
      setLoans(loansData);
      setBorrowers(borrowersData);
    } catch (err) {
      setError("Failed to load loans or borrowers data.");
    } finally {
      setLoading(false);
    }
  };

  const handleIssueLoan = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!selectedBorrowerId || !principal || !termPeriods) {
      setError("Please fill out all required fields.");
      return;
    }

    const borrower = borrowers.find((b) => b.id === selectedBorrowerId);
    if (!borrower) return;

    try {
      const payload = {
        borrower_id: selectedBorrowerId,
        principal_amount: parseFloat(principal),
        interest_rate_bp: parseInt(interestBp),
        compounding_period: compoundingPeriod,
        term_periods: parseInt(termPeriods),
      };

      if (borrower.is_public_servant) {
        if (!grossPay || !totalDeductions) {
          setError("Gross pay and total deductions are required for Alesco public servant payroll checks.");
          return;
        }
        payload.gross_pay = parseFloat(grossPay);
        payload.total_deductions = parseFloat(totalDeductions);
      }

      await createLoan(payload);
      setSuccess("Loan successfully disbursed and active!");

      // Reset form
      setSelectedBorrowerId("");
      setPrincipal("");
      setInterestBp("1000");
      setCompoundingPeriod("fortnightly");
      setTermPeriods("");
      setGrossPay("");
      setTotalDeductions("");

      // Refresh
      fetchData();
    } catch (err) {
      setError(err.message || "Failed to issue loan.");
    }
  };

  const handleRecordRepaymentSubmit = async (e) => {
    e.preventDefault();
    setRepaymentError("");

    if (!repaymentAmount) {
      setRepaymentError("Amount is required.");
      return;
    }

    try {
      await recordRepayment(repaymentLoanId, repaymentAmount, repaymentNotes);
      setRepaymentLoanId(null);
      setRepaymentAmount("");
      setRepaymentNotes("");

      // Refresh
      fetchData();
    } catch (err) {
      setRepaymentError(err.message || "Failed to record repayment.");
    }
  };

  const selectedBorrower = borrowers.find((b) => b.id === selectedBorrowerId);

  return (
    <div className="space-y-6 font-sans">
      <header className="mb-6">
        <div className="text-xs uppercase tracking-widest text-bilum-teal font-medium">
          Ledger Console
        </div>
        <h1 className="font-display text-3xl font-semibold text-kina-deep">
          Loans & Disbursements
        </h1>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Issue Loan Form */}
        <div className="bg-white/70 border border-ledger-rule rounded-sm p-6 h-fit shadow-sm">
          <h2 className="font-display text-xl uppercase tracking-wide text-kina-deep mb-4">
            Issue New Loan
          </h2>

          <form onSubmit={handleIssueLoan} className="space-y-4">
            {error && (
              <div className="rounded-sm bg-risk-high/10 border border-risk-high p-3 text-xs text-risk-high font-medium whitespace-pre-wrap">
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
                Select Borrower
              </label>
              <select
                required
                value={selectedBorrowerId}
                onChange={(e) => setSelectedBorrowerId(e.target.value)}
                className="w-full px-3 py-1.5 border border-ledger-rule rounded-sm text-sm bg-ledger-paper/50 focus:ring-bilum-teal focus:border-bilum-teal"
              >
                <option value="">-- Choose Borrower --</option>
                {borrowers.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.full_name} ({b.is_public_servant ? "Public Servant" : "Standard"})
                  </option>
                ))}
              </select>
            </div>

            {selectedBorrower && selectedBorrower.is_public_servant && (
              <div className="bg-bilum-teal/5 border border-bilum-teal/20 p-4 rounded-sm space-y-3">
                <h3 className="text-xs font-display uppercase tracking-wider text-bilum-teal font-semibold">
                  PNG Alesco Compliance Input
                </h3>
                <p className="text-[11px] text-ledger-ink/60">
                  Required to verify the borrower's total salary deduction does not breach the 50% Net-Pay retention ceiling.
                </p>

                <div>
                  <label className="block text-[11px] font-display uppercase tracking-wider text-ledger-ink/70 mb-1">
                    Fortnightly Gross Pay (Kina)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={grossPay}
                    onChange={(e) => setGrossPay(e.target.value)}
                    placeholder="e.g. 1500.00"
                    className="w-full px-3 py-1.5 border border-ledger-rule rounded-sm text-sm bg-white focus:ring-bilum-teal focus:border-bilum-teal"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-display uppercase tracking-wider text-ledger-ink/70 mb-1">
                    Fortnightly Current Deductions (Kina)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={totalDeductions}
                    onChange={(e) => setTotalDeductions(e.target.value)}
                    placeholder="e.g. 450.00"
                    className="w-full px-3 py-1.5 border border-ledger-rule rounded-sm text-sm bg-white focus:ring-bilum-teal focus:border-bilum-teal"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-display uppercase tracking-wider text-ledger-ink/70 mb-1">
                Principal Amount (Kina)
              </label>
              <input
                type="number"
                step="0.01"
                required
                value={principal}
                onChange={(e) => setPrincipal(e.target.value)}
                placeholder="e.g. 5000"
                className="w-full px-3 py-1.5 border border-ledger-rule rounded-sm text-sm bg-ledger-paper/50 focus:ring-bilum-teal focus:border-bilum-teal"
              />
            </div>

            <div>
              <label className="block text-xs font-display uppercase tracking-wider text-ledger-ink/70 mb-1">
                Interest Rate (Basis Points / period)
              </label>
              <input
                type="number"
                required
                value={interestBp}
                onChange={(e) => setInterestBp(e.target.value)}
                placeholder="e.g. 1000 for 10%"
                className="w-full px-3 py-1.5 border border-ledger-rule rounded-sm text-sm bg-ledger-paper/50 focus:ring-bilum-teal focus:border-bilum-teal"
              />
              <span className="text-[10px] text-ledger-ink/50 block mt-0.5">
                Note: 100 bp = 1.00% interest per repayment period.
              </span>
            </div>

            <div>
              <label className="block text-xs font-display uppercase tracking-wider text-ledger-ink/70 mb-1">
                Repayment & Compounding Period
              </label>
              <select
                value={compoundingPeriod}
                onChange={(e) => setCompoundingPeriod(e.target.value)}
                className="w-full px-3 py-1.5 border border-ledger-rule rounded-sm text-sm bg-ledger-paper/50 focus:ring-bilum-teal focus:border-bilum-teal"
              >
                <option value="weekly">Weekly</option>
                <option value="fortnightly">Fortnightly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-display uppercase tracking-wider text-ledger-ink/70 mb-1">
                Term Periods (Count)
              </label>
              <input
                type="number"
                required
                value={termPeriods}
                onChange={(e) => setTermPeriods(e.target.value)}
                placeholder="e.g. 10 periods"
                className="w-full px-3 py-1.5 border border-ledger-rule rounded-sm text-sm bg-ledger-paper/50 focus:ring-bilum-teal focus:border-bilum-teal"
              />
            </div>

            <button
              type="submit"
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-sm shadow-sm text-sm font-display uppercase tracking-wider font-semibold text-ledger-paper bg-kina-deep hover:bg-kina-deep/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-kina-gold"
            >
              Issue & Disburse Loan
            </button>
          </form>
        </div>

        {/* Right Columns: Active/Persisted Loans List */}
        <div className="lg:col-span-2 bg-white/60 border border-ledger-rule rounded-sm p-6 shadow-sm">
          <h2 className="font-display text-xl uppercase tracking-wide text-kina-deep mb-4">
            Active Loan Ledger ({loans.length})
          </h2>

          {loading ? (
            <div className="text-center py-8 text-ledger-ink/50">Loading loans ledger…</div>
          ) : loans.length === 0 ? (
            <div className="text-center py-8 text-ledger-ink/50 border border-dashed border-ledger-rule rounded-sm">
              No active loans disbursed yet.
            </div>
          ) : (
            <div className="space-y-4">
              {loans.map((l) => (
                <div
                  key={l.id}
                  className="bg-white border border-ledger-rule rounded-sm p-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 hover:shadow-sm transition-all"
                >
                  <div>
                    <h3 className="font-display text-lg font-semibold text-kina-deep">
                      {l.borrower_name}
                    </h3>
                    <div className="text-xs text-ledger-ink/60 mt-1 space-y-0.5">
                      <div>
                        Principal: <span className="font-semibold text-ledger-ink">K{l.principal_amount.toLocaleString()}</span> @ {l.interest_rate_bp / 100}% per {l.compounding_period}
                      </div>
                      <div>
                        Term: {l.term_periods} {l.compounding_period} periods
                      </div>
                      {l.due_at && (
                        <div>
                          Due Date: {new Date(l.due_at).toLocaleDateString()}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-col sm:items-end gap-2 w-full sm:w-auto">
                    <div className="text-sm">
                      Outstanding: <span className="font-bold text-lg text-kina-gold">K{l.outstanding_balance.toLocaleString()}</span>
                    </div>

                    <div className="flex gap-2">
                      <span className={`text-[10px] px-2 py-0.5 rounded-sm font-semibold uppercase tracking-wider self-center ${
                        l.status === "active"
                          ? "bg-risk-none/10 text-risk-none"
                          : l.status === "overdue"
                          ? "bg-risk-watch/10 text-risk-watch"
                          : l.status === "defaulted"
                          ? "bg-risk-high/10 text-risk-high"
                          : "bg-ledger-ink/10 text-ledger-ink/70"
                      }`}>
                        {l.status}
                      </span>

                      {l.status !== "closed" && l.status !== "written_off" && (
                        <button
                          onClick={() => setRepaymentLoanId(l.id)}
                          className="bg-kina-deep text-ledger-paper text-xs uppercase font-display tracking-wider font-semibold px-2.5 py-1 rounded-sm shadow hover:bg-kina-deep/90"
                        >
                          💸 Repay
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Record Repayment Modal/Overlay */}
      {repaymentLoanId && (
        <div className="fixed inset-0 bg-ledger-ink/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white border border-ledger-rule rounded-sm shadow-xl max-w-md w-full p-6 animate-fade-in">
            <h3 className="font-display text-xl uppercase tracking-wider text-kina-deep mb-3">
              Record Repayment
            </h3>

            <form onSubmit={handleRecordRepaymentSubmit} className="space-y-4">
              {repaymentError && (
                <div className="rounded-sm bg-risk-high/10 border border-risk-high p-3 text-xs text-risk-high font-medium">
                  ⚠️ {repaymentError}
                </div>
              )}

              <div>
                <label className="block text-xs font-display uppercase tracking-wider text-ledger-ink/70 mb-1">
                  Repayment Amount (Kina)
                </label>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={repaymentAmount}
                  onChange={(e) => setRepaymentAmount(e.target.value)}
                  placeholder="e.g. 550.00"
                  className="w-full px-3 py-1.5 border border-ledger-rule rounded-sm text-sm bg-ledger-paper/50 focus:ring-bilum-teal focus:border-bilum-teal"
                />
              </div>

              <div>
                <label className="block text-xs font-display uppercase tracking-wider text-ledger-ink/70 mb-1">
                  Transaction Notes (Optional)
                </label>
                <textarea
                  value={repaymentNotes}
                  onChange={(e) => setRepaymentNotes(e.target.value)}
                  placeholder="e.g. Cash pay-in by borrower"
                  className="w-full px-3 py-1.5 border border-ledger-rule rounded-sm text-sm bg-ledger-paper/50 focus:ring-bilum-teal focus:border-bilum-teal h-20 resize-none"
                />
              </div>

              <div className="flex gap-2 justify-end pt-2">
                <button
                  type="button"
                  onClick={() => setRepaymentLoanId(null)}
                  className="bg-ledger-paper border border-ledger-rule text-ledger-ink/70 px-4 py-1.5 rounded-sm text-xs font-display uppercase tracking-wider font-semibold hover:bg-ledger-paper/80"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-kina-deep text-ledger-paper px-4 py-1.5 rounded-sm text-xs font-display uppercase tracking-wider font-semibold hover:bg-kina-deep/95"
                >
                  Confirm Repayment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
