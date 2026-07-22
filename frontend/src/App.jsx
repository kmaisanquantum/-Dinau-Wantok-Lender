import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation, useNavigate } from "react-router-dom";
import Dashboard from "./components/Dashboard.jsx";
import Borrowers from "./components/Borrowers.jsx";
import Loans from "./components/Loans.jsx";
import Collateral from "./components/Collateral.jsx";
import Login from "./components/Login.jsx";

function AppShell({ children, onLogout }) {
  const location = useLocation();
  const currentPath = location.pathname;

  const links = [
    { path: "/", label: "📊 Dashboard" },
    { path: "/borrowers", label: "👥 Borrowers" },
    { path: "/loans", label: "💸 Loans" },
    { path: "/collateral", label: "🔒 Collateral" },
  ];

  return (
    <div className="min-h-screen bg-ledger-paper flex flex-col md:flex-row font-sans text-ledger-ink">
      {/* Sidebar navigation */}
      <aside className="w-full md:w-64 bg-kina-deep text-ledger-paper flex flex-col border-b md:border-b-0 md:border-r border-ledger-rule shadow-sm">
        <div className="p-6 border-b border-ledger-rule/20 text-center md:text-left">
          <h2 className="font-display text-xl font-bold uppercase tracking-wider text-kina-gold">
            Wantok Lender
          </h2>
          <p className="text-[10px] text-ledger-paper/60 uppercase tracking-widest mt-0.5">
            Micro-Finance Ledger
          </p>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {links.map((link) => {
            const isActive = currentPath === link.path;
            return (
              <Link
                key={link.path}
                to={link.path}
                className={`flex items-center px-4 py-2 text-sm font-medium font-display uppercase tracking-wider rounded-sm transition-all ${
                  isActive
                    ? "bg-kina-gold text-kina-deep font-bold shadow-sm"
                    : "text-ledger-paper/85 hover:bg-white/10"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-ledger-rule/20">
          <button
            onClick={onLogout}
            className="w-full flex items-center justify-center px-4 py-2 text-sm font-medium font-display uppercase tracking-wider text-risk-high hover:bg-risk-high/10 rounded-sm border border-risk-high/30 transition-all"
          >
            🚪 Log Out
          </button>
        </div>
      </aside>

      {/* Main content display */}
      <main className="flex-1 p-6 md:p-10 max-w-7xl mx-auto w-full">
        {children}
      </main>
    </div>
  );
}

function AuthenticatedRoutes({ onLogout }) {
  const navigate = useNavigate();

  useEffect(() => {
    const handleUnauthorized = () => {
      navigate("/login");
    };
    window.addEventListener("unauthorized", handleUnauthorized);
    return () => {
      window.removeEventListener("unauthorized", handleUnauthorized);
    };
  }, [navigate]);

  return (
    <AppShell onLogout={onLogout}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/borrowers" element={<Borrowers />} />
        <Route path="/loans" element={<Loans />} />
        <Route path="/collateral" element={<Collateral />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem("wantok_token"));

  useEffect(() => {
    const handleUnauthorized = () => {
      setIsAuthenticated(false);
    };
    window.addEventListener("unauthorized", handleUnauthorized);
    return () => {
      window.removeEventListener("unauthorized", handleUnauthorized);
    };
  }, []);

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem("wantok_token");
    setIsAuthenticated(false);
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={
            isAuthenticated ? (
              <Navigate to="/" replace />
            ) : (
              <Login onLoginSuccess={handleLoginSuccess} />
            )
          }
        />
        <Route
          path="/*"
          element={
            isAuthenticated ? (
              <AuthenticatedRoutes onLogout={handleLogout} />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
