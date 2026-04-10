import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Lock, Loader2, ArrowRight } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AdminLogin() {
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!password) { toast.error("Veuillez entrer le mot de passe"); return; }
    setLoading(true);
    try {
      await axios.post(`${API}/admin/login`, { password });
      localStorage.setItem("admin_auth", "true");
      toast.success("Connexion reussie");
      navigate("/admin/dashboard");
    } catch { toast.error("Mot de passe incorrect"); }
    finally { setLoading(false); }
  };

  return (
    <main className="min-h-screen bg-noir flex items-center justify-center px-4" data-testid="admin-login">
      <div className="max-w-md w-full bg-surface border border-white/5 p-8">
        <div className="text-center mb-8">
          <Lock className="w-12 h-12 text-champagne mx-auto mb-4" strokeWidth={1.5} />
          <h1 className="text-2xl font-heading font-semibold text-white">Administration</h1>
          <p className="text-zinc-500 text-sm mt-2">Entrez le mot de passe administrateur</p>
        </div>
        <form onSubmit={handleLogin} className="space-y-4">
          <Input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Mot de passe"
            className="h-12 bg-noir border-white/10 text-white placeholder:text-zinc-600 focus:ring-champagne focus:border-champagne/30"
            data-testid="admin-password" />
          <Button type="submit" disabled={loading} className="w-full h-12 btn-gold" data-testid="admin-login-btn">
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <>Connexion <ArrowRight className="w-4 h-4 ml-2" strokeWidth={1.5} /></>}
          </Button>
        </form>
      </div>
    </main>
  );
}
