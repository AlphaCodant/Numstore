import { useState, useEffect } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import axios from "axios";
import { CheckCircle, Download, Spinner, XCircle, Lock } from "@phosphor-icons/react";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Success() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user, setPassword } = useAuth();
  const { clearCart } = useCart();
  
  const sessionId = searchParams.get("session_id");
  
  const [status, setStatus] = useState("loading");
  const [order, setOrder] = useState(null);
  const [newPassword, setNewPassword] = useState("");
  const [settingPassword, setSettingPassword] = useState(false);

  useEffect(() => {
    if (sessionId) {
      pollPaymentStatus();
    } else {
      setStatus("error");
    }
  }, [sessionId]);

  const pollPaymentStatus = async (attempts = 0) => {
    const maxAttempts = 10;
    const pollInterval = 2000;

    if (attempts >= maxAttempts) {
      setStatus("timeout");
      return;
    }

    try {
      const res = await axios.get(`${API}/checkout/status/${sessionId}`);
      
      if (res.data.payment_status === "paid") {
        setStatus("success");
        clearCart();
        
        // Get order details
        const ordersRes = await axios.get(`${API}/admin/orders`);
        const foundOrder = ordersRes.data.find(o => o.session_id === sessionId);
        if (foundOrder) {
          setOrder(foundOrder);
        }
      } else if (res.data.status === "expired") {
        setStatus("expired");
      } else {
        setTimeout(() => pollPaymentStatus(attempts + 1), pollInterval);
      }
    } catch (err) {
      if (attempts < maxAttempts - 1) {
        setTimeout(() => pollPaymentStatus(attempts + 1), pollInterval);
      } else {
        setStatus("error");
      }
    }
  };

  const handleSetPassword = async () => {
    if (!newPassword || newPassword.length < 6) {
      toast.error("Le mot de passe doit contenir au moins 6 caractères");
      return;
    }

    if (!order?.user_email) {
      toast.error("Email non trouvé");
      return;
    }

    setSettingPassword(true);
    try {
      await setPassword(order.user_email, newPassword);
      toast.success("Mot de passe défini! Vous pouvez maintenant accéder à vos téléchargements.");
      navigate("/my-downloads");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Erreur lors de la définition du mot de passe");
    } finally {
      setSettingPassword(false);
    }
  };

  if (status === "loading") {
    return (
      <main className="min-h-screen bg-white flex items-center justify-center" data-testid="success-loading">
        <div className="text-center">
          <Spinner className="w-16 h-16 text-[#0055FF] animate-spin mx-auto mb-6" />
          <h1 className="text-2xl font-bold text-[#0A0A0A] mb-2" style={{ fontFamily: 'Cabinet Grotesk' }}>
            Vérification du paiement...
          </h1>
          <p className="text-[#52525B]">Veuillez patienter quelques instants.</p>
        </div>
      </main>
    );
  }

  if (status === "error" || status === "expired" || status === "timeout") {
    return (
      <main className="min-h-screen bg-white flex items-center justify-center" data-testid="success-error">
        <div className="text-center max-w-md mx-auto px-4">
          <XCircle weight="fill" className="w-20 h-20 text-[#FF3B30] mx-auto mb-6" />
          <h1 className="text-2xl font-bold text-[#0A0A0A] mb-2" style={{ fontFamily: 'Cabinet Grotesk' }}>
            {status === "timeout" ? "Délai d'attente dépassé" : "Paiement échoué"}
          </h1>
          <p className="text-[#52525B] mb-8">
            {status === "timeout" 
              ? "La vérification du paiement a pris trop de temps. Vérifiez votre email pour confirmation."
              : "Une erreur s'est produite lors du paiement. Veuillez réessayer."}
          </p>
          <Link
            to="/checkout"
            className="inline-flex items-center px-6 py-3 bg-[#0055FF] text-white font-medium hover:bg-[#0040CC] transition-all"
          >
            Réessayer
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#FAFAFA]" data-testid="success-page">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="bg-white border border-[#E4E4E7] p-8 text-center">
          <CheckCircle weight="fill" className="w-20 h-20 text-[#34C759] mx-auto mb-6" />
          
          <h1 className="text-3xl font-black text-[#0A0A0A] mb-2" style={{ fontFamily: 'Cabinet Grotesk' }}>
            Paiement réussi!
          </h1>
          <p className="text-[#52525B] mb-8">
            Merci pour votre achat. Vos produits sont prêts à être téléchargés.
          </p>

          {order && (
            <div className="border border-[#E4E4E7] p-4 mb-8 text-left">
              <p className="text-sm text-[#52525B] mb-2">Commande #{order.id?.slice(0, 8)}</p>
              <div className="space-y-2">
                {order.items?.map((item, idx) => (
                  <div key={idx} className="flex justify-between text-sm">
                    <span>{item.name} x{item.quantity}</span>
                    <span className="font-medium">${item.total?.toFixed(2)}</span>
                  </div>
                ))}
              </div>
              <div className="border-t border-[#E4E4E7] mt-3 pt-3 flex justify-between font-semibold">
                <span>Total payé</span>
                <span className="text-[#0055FF]">${order.total?.toFixed(2)}</span>
              </div>
            </div>
          )}

          {/* Set password section */}
          {!user && order && (
            <div className="border border-[#E4E4E7] p-6 mb-8 text-left">
              <div className="flex items-center gap-3 mb-4">
                <Lock weight="duotone" className="w-6 h-6 text-[#0055FF]" />
                <h2 className="font-semibold text-[#0A0A0A]" style={{ fontFamily: 'Cabinet Grotesk' }}>
                  Créez votre compte
                </h2>
              </div>
              <p className="text-sm text-[#52525B] mb-4">
                Définissez un mot de passe pour accéder à vos téléchargements à tout moment.
              </p>
              <div className="flex gap-2">
                <Input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Votre mot de passe (min. 6 caractères)"
                  className="h-12"
                  data-testid="set-password-input"
                />
                <Button
                  onClick={handleSetPassword}
                  disabled={settingPassword}
                  className="h-12 px-6 bg-[#0055FF] hover:bg-[#0040CC]"
                  data-testid="set-password-button"
                >
                  {settingPassword ? <Spinner className="w-5 h-5 animate-spin" /> : "Créer"}
                </Button>
              </div>
            </div>
          )}

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            {user ? (
              <Link
                to="/my-downloads"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-[#0055FF] text-white font-medium hover:bg-[#0040CC] transition-all"
                data-testid="go-to-downloads"
              >
                <Download weight="bold" className="w-5 h-5" />
                Mes téléchargements
              </Link>
            ) : null}
            <Link
              to="/"
              className="inline-flex items-center justify-center px-6 py-3 border border-[#E4E4E7] text-[#0A0A0A] font-medium hover:bg-[#F4F4F5] transition-all"
            >
              Continuer les achats
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
