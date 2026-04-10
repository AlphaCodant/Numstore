import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";
import { DollarSign, ShoppingBag, Package, ArrowRight, Loader2, LogOut, User, Clock } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const formatPrice = (amount, currency = "XOF") => {
  if (currency === "XOF" || !currency) return `${amount.toLocaleString("fr-FR")} FCFA`;
  return `$${amount.toFixed(2)}`;
};

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!localStorage.getItem("admin_auth")) { navigate("/admin"); return; }
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try { const res = await axios.get(`${API}/admin/stats`); setStats(res.data); }
    catch (err) { console.error("Error fetching stats:", err); }
    finally { setLoading(false); }
  };

  if (loading) {
    return <main className="min-h-screen bg-noir flex items-center justify-center"><Loader2 className="w-8 h-8 text-champagne animate-spin" /></main>;
  }

  return (
    <main className="min-h-screen bg-noir" data-testid="admin-dashboard">
      <div className="max-w-6xl mx-auto px-6 lg:px-12 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-heading font-semibold text-white">Tableau de bord</h1>
            <p className="text-zinc-500 text-sm">Vue d'ensemble des ventes</p>
          </div>
          <button onClick={() => { localStorage.removeItem("admin_auth"); navigate("/admin"); }}
            className="flex items-center gap-2 px-4 py-2 text-zinc-500 hover:text-red-400 transition-colors text-sm" data-testid="logout-btn">
            <LogOut className="w-4 h-4" strokeWidth={1.5} /> Deconnexion
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          {[
            { icon: DollarSign, label: "Revenus (FCFA)", value: formatPrice(stats?.total_revenue_xof || 0, "XOF"), color: "text-champagne" },
            { icon: ShoppingBag, label: "Ventes", value: stats?.total_sales || 0, color: "text-emerald-400" },
            { icon: Package, label: "Produits", value: stats?.products_count || 0, color: "text-zinc-300" },
            { icon: Clock, label: "Portfolios en attente", value: stats?.portfolio_pending || 0, color: "text-amber-400" },
          ].map((s, i) => (
            <div key={i} className="bg-surface border border-white/5 p-6" data-testid={`stat-${i}`}>
              <s.icon className={`w-8 h-8 ${s.color} mb-4`} strokeWidth={1.5} />
              <p className="text-xs text-zinc-500 mb-1 uppercase tracking-wider">{s.label}</p>
              <p className={`text-2xl font-heading font-bold ${s.color}`}>{s.value}</p>
            </div>
          ))}
        </div>

        {/* Quick actions */}
        <div className="grid md:grid-cols-3 gap-4 mb-8">
          {[
            { to: "/admin/products", icon: Package, label: "Produits & Services", sub: "Gerer le catalogue", color: "text-champagne" },
            { to: "/admin/portfolios", icon: User, label: "Demandes Portfolio", sub: "Gerer les soumissions", color: "text-amber-400" },
          ].map((a, i) => (
            <Link key={i} to={a.to} className="flex items-center gap-4 bg-surface border border-white/5 p-6 hover:border-champagne/20 transition-all" data-testid={`link-${i}`}>
              <a.icon className={`w-8 h-8 ${a.color}`} strokeWidth={1.5} />
              <div className="flex-1">
                <p className="font-semibold text-white text-sm">{a.label}</p>
                <p className="text-xs text-zinc-500">{a.sub}</p>
              </div>
              <ArrowRight className="w-4 h-4 text-zinc-600" strokeWidth={1.5} />
            </Link>
          ))}
          <a href="/" target="_blank" className="flex items-center gap-4 bg-surface border border-white/5 p-6 hover:border-champagne/20 transition-all">
            <ShoppingBag className="w-8 h-8 text-emerald-400" strokeWidth={1.5} />
            <div className="flex-1"><p className="font-semibold text-white text-sm">Voir la boutique</p><p className="text-xs text-zinc-500">Ouvrir le site</p></div>
            <ArrowRight className="w-4 h-4 text-zinc-600" strokeWidth={1.5} />
          </a>
        </div>

        {/* Recent transactions */}
        <div className="bg-surface border border-white/5">
          <div className="p-4 border-b border-white/5">
            <h2 className="font-heading text-lg font-semibold text-white">Transactions recentes</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full" data-testid="transactions-table">
              <thead>
                <tr className="border-b border-white/5">
                  <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wider">Email</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wider">Type</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wider">Montant</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-zinc-500 uppercase tracking-wider">Date</th>
                </tr>
              </thead>
              <tbody>
                {!stats?.recent_transactions?.length ? (
                  <tr><td colSpan={4} className="text-center text-zinc-600 py-8">Aucune transaction</td></tr>
                ) : (
                  stats.recent_transactions.map((t, idx) => (
                    <tr key={idx} className="border-b border-white/5 hover:bg-white/[0.02]">
                      <td className="px-4 py-3 text-sm text-zinc-300">{t.email}</td>
                      <td className="px-4 py-3 text-sm">
                        <span className={`px-2 py-0.5 text-xs font-medium ${t.is_service ? "bg-amber-500/10 text-amber-400" : "bg-champagne/10 text-champagne"}`}>
                          {t.is_service ? "Portfolio" : "Produit"}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm font-medium text-champagne">{formatPrice(t.amount, t.currency)}</td>
                      <td className="px-4 py-3 text-sm text-zinc-500">{new Date(t.created_at).toLocaleDateString("fr-FR")}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>
  );
}
