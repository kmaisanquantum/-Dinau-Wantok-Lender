import { useState } from "react";
import { login } from "../lib/api";

export default function Login({ onLoginSuccess }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(email, password);
      onLoginSuccess();
    } catch (err) {
      setError(err.message || "Invalid credentials. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-ledger-paper flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <span className="text-3xl">🔑</span>
        <h2 className="mt-4 text-center text-3xl font-display font-semibold text-kina-deep uppercase tracking-wider">
          Wantok Lender
        </h2>
        <p className="mt-2 text-center text-sm text-ledger-ink/60">
          Multi-tenant Street & MSME Ledger Ledger Access
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white/70 py-8 px-4 border border-ledger-rule rounded-sm shadow-sm sm:px-10">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="rounded-sm bg-risk-high/10 border border-risk-high p-3 text-sm text-risk-high font-medium">
                ⚠️ {error}
              </div>
            )}

            <div>
              <label
                htmlFor="email"
                className="block text-xs font-display uppercase tracking-wider text-ledger-ink/75 font-medium"
              >
                Tenant Email Address
              </label>
              <div className="mt-1">
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="e.g. seed@wantok.com"
                  className="appearance-none block w-full px-3 py-2 border border-ledger-rule rounded-sm shadow-sm placeholder-ledger-ink/30 focus:outline-none focus:ring-bilum-teal focus:border-bilum-teal sm:text-sm bg-ledger-paper/50"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-xs font-display uppercase tracking-wider text-ledger-ink/75 font-medium"
              >
                Access Password
              </label>
              <div className="mt-1">
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="appearance-none block w-full px-3 py-2 border border-ledger-rule rounded-sm shadow-sm placeholder-ledger-ink/30 focus:outline-none focus:ring-bilum-teal focus:border-bilum-teal sm:text-sm bg-ledger-paper/50"
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-sm shadow-sm text-sm font-display uppercase tracking-wider font-semibold text-ledger-paper bg-kina-deep hover:bg-kina-deep/95 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-kina-gold disabled:opacity-50"
              >
                {loading ? "Verifying Ledger..." : "Log In to Ledger"}
              </button>
            </div>
          </form>

          <div className="mt-6 border-t border-ledger-rule pt-4 text-center">
            <span className="text-xs text-ledger-ink/50">
              Seed login: <code className="bg-ledger-paper px-1 py-0.5 rounded">seed@wantok.com</code> / <code className="bg-ledger-paper px-1 py-0.5 rounded">password123</code>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
