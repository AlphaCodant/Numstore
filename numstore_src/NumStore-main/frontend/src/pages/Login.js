import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Envelope, Lock, Spinner, ArrowRight } from "@phosphor-icons/react";
import { useAuth } from "../context/AuthContext";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { toast } from "sonner";

export default function Login() {
  const navigate = useNavigate();
  const { login, register } = useAuth();
  
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!email || !password) {
      toast.error("Veuillez remplir tous les champs");
      return;
    }

    if (password.length < 6) {
      toast.error("Le mot de passe doit contenir au moins 6 caractères");
      return;
    }

    setLoading(true);
    try {
      if (isLogin) {
        await login(email, password);
        toast.success("Connexion réussie!");
      } else {
        await register(email, password);
        toast.success("Compte créé avec succès!");
      }
      navigate("/");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Erreur d'authentification");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#FAFAFA] flex items-center justify-center px-4" data-testid="login-page">
      <div className="w-full max-w-md">
        <div className="bg-white border border-[#E4E4E7] p-8">
          <h1
            className="text-2xl font-black text-[#0A0A0A] mb-2 text-center"
            style={{ fontFamily: 'Cabinet Grotesk' }}
          >
            {isLogin ? "Connexion" : "Créer un compte"}
          </h1>
          <p className="text-[#52525B] text-center mb-8">
            {isLogin
              ? "Accédez à vos téléchargements"
              : "Rejoignez NumStore dès maintenant"}
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="relative">
              <Envelope weight="regular" className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#52525B]" />
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="votre@email.com"
                className="h-12 pl-10"
                data-testid="login-email"
              />
            </div>

            <div className="relative">
              <Lock weight="regular" className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#52525B]" />
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Mot de passe"
                className="h-12 pl-10"
                data-testid="login-password"
              />
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full h-12 bg-[#0055FF] hover:bg-[#0040CC] text-white font-medium"
              data-testid="login-submit"
            >
              {loading ? (
                <Spinner className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  {isLogin ? "Se connecter" : "Créer mon compte"}
                  <ArrowRight weight="bold" className="w-5 h-5 ml-2" />
                </>
              )}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={() => setIsLogin(!isLogin)}
              className="text-sm text-[#52525B] hover:text-[#0055FF] transition-colors"
              data-testid="toggle-auth-mode"
            >
              {isLogin
                ? "Pas de compte? Inscrivez-vous"
                : "Déjà un compte? Connectez-vous"}
            </button>
          </div>
        </div>

        <p className="text-center text-xs text-[#52525B] mt-4">
          En continuant, vous acceptez nos conditions d'utilisation.
        </p>
      </div>
    </main>
  );
}
