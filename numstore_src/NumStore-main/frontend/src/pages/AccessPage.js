import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import axios from "axios";
import { KeyRound, Loader2, CheckCircle, Download, Clock, RefreshCw, Mail, XCircle, AlertTriangle } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const inputCls = "bg-noir border-white/10 text-white placeholder:text-zinc-600 focus:ring-champagne focus:border-champagne/30";

export default function AccessPage() {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get("session_id");
  const urlProductId = searchParams.get("product_id");

  const [view, setView] = useState("code");
  const [code, setCode] = useState("");
  const [email, setEmail] = useState("");
  const [productId] = useState(urlProductId || "");
  const [product, setProduct] = useState(null);
  const [expiresIn, setExpiresIn] = useState("");
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (sessionId) { setView("payment-check"); checkPaymentStatus(); }
  }, [sessionId]);

  const checkPaymentStatus = async (attempts = 0) => {
    if (attempts >= 10) { setView("code"); toast.info("Verifiez vos emails pour le code d'acces"); return; }
    try {
      const res = await axios.get(`${API}/payment/status/${sessionId}`);
      if (res.data.status === "paid" && res.data.email_sent) { setView("success"); toast.success("Code d'acces envoye par email!"); }
      else setTimeout(() => checkPaymentStatus(attempts + 1), 2000);
    } catch {
      if (attempts < 9) setTimeout(() => checkPaymentStatus(attempts + 1), 2000);
      else { setView("code"); toast.error("Erreur de verification. Verifiez vos emails."); }
    }
  };

  const verifyCode = async () => {
    if (!code.trim()) { toast.error("Veuillez entrer votre code"); return; }
    setProcessing(true); setError("");
    try {
      const res = await axios.post(`${API}/access/verify`, { code: code.toUpperCase() });
      setProduct(res.data.product); setExpiresIn(res.data.expires_in); setView("download");
    } catch (err) {
      setError(err.response?.data?.detail || "Code invalide");
      if (err.response?.status === 410) setView("expired");
    } finally { setProcessing(false); }
  };

  const resendCode = async () => {
    if (!email.trim()) { toast.error("Veuillez entrer votre email"); return; }
    setProcessing(true);
    try {
      const payload = { email }; if (productId) payload.product_id = productId;
      const res = await axios.post(`${API}/access/resend`, payload);
      toast.success(res.data.message || "Nouveau code envoye!"); setView("success");
    } catch (err) { toast.error(err.response?.data?.detail || "Erreur lors de l'envoi"); }
    finally { setProcessing(false); }
  };

  const cardCls = "max-w-md w-full bg-surface border border-white/5 p-8";

  if (view === "payment-check") {
    return (
      <main className="min-h-screen bg-noir flex items-center justify-center px-4" data-testid="payment-check">
        <div className={`${cardCls} text-center`}>
          <Loader2 className="w-12 h-12 text-champagne animate-spin mx-auto mb-6" />
          <h1 className="text-2xl font-heading font-semibold text-white mb-2">Verification du paiement...</h1>
          <p className="text-zinc-500">Votre code d'acces sera envoye par email.</p>
        </div>
      </main>
    );
  }

  if (view === "success") {
    return (
      <main className="min-h-screen bg-noir flex items-center justify-center px-4" data-testid="success-view">
        <div className={`${cardCls} text-center`}>
          <CheckCircle className="w-16 h-16 text-champagne mx-auto mb-6" strokeWidth={1.5} />
          <h1 className="text-2xl font-heading font-semibold text-white mb-2">Code envoye!</h1>
          <p className="text-zinc-400 mb-8">Consultez votre boite email pour recuperer votre code d'acces.</p>
          <Button onClick={() => setView("code")} className="w-full h-12 btn-gold" data-testid="enter-code-btn">
            <KeyRound className="w-5 h-5 mr-2" strokeWidth={1.5} /> Entrer mon code
          </Button>
        </div>
      </main>
    );
  }

  if (view === "download" && product) {
    return (
      <main className="min-h-screen bg-noir flex items-center justify-center px-4" data-testid="download-view">
        <div className="max-w-lg w-full bg-surface border border-white/5 p-8">
          <div className="text-center mb-8">
            <CheckCircle className="w-14 h-14 text-champagne mx-auto mb-4" strokeWidth={1.5} />
            <h1 className="text-2xl font-heading font-semibold text-white mb-2">Acces autorise!</h1>
            <div className="flex items-center justify-center gap-2 text-zinc-400">
              <Clock className="w-4 h-4" strokeWidth={1.5} />
              <span className="text-sm">Expire dans: <strong className="text-champagne">{expiresIn}</strong></span>
            </div>
          </div>
          <div className="border border-white/5 p-6 mb-6 bg-noir">
            <h2 className="font-heading text-lg font-semibold text-white mb-2">{product.name}</h2>
            <p className="text-sm text-zinc-400 mb-3">{product.description}</p>
            {product.file_size && <p className="text-xs text-zinc-600">Taille: {product.file_size}</p>}
          </div>
          <Button onClick={() => window.open(product.download_url, "_blank")} className="w-full h-14 btn-gold text-base" data-testid="download-btn">
            <Download className="w-5 h-5 mr-2" strokeWidth={1.5} /> Telecharger
          </Button>
          <p className="text-xs text-center text-zinc-600 mt-4">Apres expiration, vous pourrez demander un nouveau code.</p>
        </div>
      </main>
    );
  }

  if (view === "expired") {
    return (
      <main className="min-h-screen bg-noir flex items-center justify-center px-4" data-testid="expired-view">
        <div className={`${cardCls} text-center`}>
          <AlertTriangle className="w-14 h-14 text-champagne mx-auto mb-6" strokeWidth={1.5} />
          <h1 className="text-2xl font-heading font-semibold text-white mb-2">Code expire</h1>
          <p className="text-zinc-400 mb-8">Votre code d'acces a expire. Demandez-en un nouveau gratuitement.</p>
          <div className="space-y-4">
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" strokeWidth={1.5} />
              <Input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="votre@email.com" className={`h-12 pl-10 ${inputCls}`} data-testid="resend-email-input" />
            </div>
            <Button onClick={resendCode} disabled={processing} className="w-full h-12 btn-gold" data-testid="resend-btn">
              {processing ? <Loader2 className="w-5 h-5 animate-spin" /> : <><RefreshCw className="w-4 h-4 mr-2" strokeWidth={1.5} /> Renvoyer le code</>}
            </Button>
          </div>
          <button onClick={() => { setView("code"); setError(""); }} className="text-sm text-zinc-500 hover:text-champagne mt-6 transition-colors">Retour</button>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-noir flex items-center justify-center px-4" data-testid="code-entry-view">
      <div className={cardCls}>
        <div className="text-center mb-8">
          <KeyRound className="w-14 h-14 text-champagne mx-auto mb-4" strokeWidth={1.5} />
          <h1 className="text-2xl font-heading font-semibold text-white mb-2">Entrez votre code</h1>
          <p className="text-zinc-400 text-sm">Saisissez le code recu par email pour acceder a votre produit.</p>
        </div>
        <div className="space-y-4">
          <Input type="text" value={code} onChange={e => setCode(e.target.value.toUpperCase())} placeholder="EX: A1B2C3"
            className={`h-16 text-center text-2xl tracking-[0.3em] font-mono uppercase ${inputCls}`} maxLength={6} data-testid="code-input" />
          {error && (
            <div className="flex items-center gap-2 text-red-400 text-sm">
              <XCircle className="w-4 h-4" strokeWidth={1.5} /> {error}
            </div>
          )}
          <Button onClick={verifyCode} disabled={processing || code.length < 6} className="w-full h-12 btn-gold" data-testid="verify-btn">
            {processing ? <Loader2 className="w-5 h-5 animate-spin" /> : "Verifier"}
          </Button>
        </div>
        <div className="mt-8 pt-6 border-t border-white/5 text-center">
          <p className="text-sm text-zinc-600 mb-3">Code expire ou perdu?</p>
          <button onClick={() => setView("expired")} className="text-sm font-medium text-champagne hover:text-champagne-hover transition-colors" data-testid="resend-link">
            <RefreshCw className="w-4 h-4 inline mr-1" strokeWidth={1.5} /> Renvoyer le code
          </button>
        </div>
      </div>
    </main>
  );
}
