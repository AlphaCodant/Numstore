import { useState, useEffect } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import axios from "axios";
import { CheckCircle, Loader2, Clock, Mail } from "lucide-react";
import { Button } from "../components/ui/button";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function PortfolioSuccess() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const submissionId = searchParams.get("submission_id");

  const [status, setStatus] = useState("checking");
  const [submission, setSubmission] = useState(null);

  useEffect(() => {
    if (!submissionId) { navigate("/"); return; }
    checkPayment();
  }, [submissionId]);

  const checkPayment = async (attempts = 0) => {
    try {
      const res = await axios.get(`${API}/portfolio/payment-status/${submissionId}`);
      if (res.data.status === "paid") {
        setStatus("paid");
        const subRes = await axios.get(`${API}/portfolio/submission/${submissionId}`);
        setSubmission(subRes.data);
      } else if (attempts < 10) {
        setTimeout(() => checkPayment(attempts + 1), 2000);
      } else { setStatus("pending"); }
    } catch {
      if (attempts < 10) setTimeout(() => checkPayment(attempts + 1), 2000);
      else setStatus("error");
    }
  };

  const cardCls = "max-w-md w-full bg-surface border border-white/5 p-8";

  if (status === "checking") {
    return (
      <main className="min-h-screen bg-noir flex items-center justify-center px-4">
        <div className={`${cardCls} text-center`}>
          <Loader2 className="w-12 h-12 text-champagne animate-spin mx-auto mb-6" />
          <h1 className="text-2xl font-heading font-semibold text-white mb-2">Verification du paiement...</h1>
          <p className="text-zinc-500">Veuillez patienter quelques instants.</p>
        </div>
      </main>
    );
  }

  if (status === "paid") {
    return (
      <main className="min-h-screen bg-noir flex items-center justify-center px-4">
        <div className={`${cardCls} text-center`}>
          <CheckCircle className="w-16 h-16 text-champagne mx-auto mb-6" strokeWidth={1.5} />
          <h1 className="text-2xl font-heading font-semibold text-white mb-4">Paiement reussi !</h1>
          <p className="text-zinc-400 mb-6">
            Merci {submission?.full_name?.split(' ')[0]} ! Votre demande de portfolio a ete enregistree.
          </p>
          <div className="bg-noir border border-white/5 p-4 mb-6 text-left space-y-3">
            <div className="flex items-center gap-3">
              <Clock className="w-5 h-5 text-champagne" strokeWidth={1.5} />
              <span className="text-sm text-zinc-300">Delai de creation: <strong className="text-white">48-72 heures</strong></span>
            </div>
            <div className="flex items-center gap-3">
              <Mail className="w-5 h-5 text-champagne" strokeWidth={1.5} />
              <span className="text-sm text-zinc-300">Notification a: <strong className="text-white">{submission?.email}</strong></span>
            </div>
          </div>
          <div className="bg-champagne/10 border border-champagne/20 p-4 mb-6 text-sm text-champagne">
            Notre equipe va creer votre portfolio professionnel. Vous recevrez un email avec le lien de votre site des qu'il sera pret.
          </div>
          <Link to="/">
            <Button className="w-full h-12 btn-gold">Retour a l'accueil</Button>
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-noir flex items-center justify-center px-4">
      <div className={`${cardCls} text-center`}>
        <Clock className="w-14 h-14 text-champagne mx-auto mb-6" strokeWidth={1.5} />
        <h1 className="text-2xl font-heading font-semibold text-white mb-4">En attente de confirmation</h1>
        <p className="text-zinc-400 mb-6">Le paiement est en cours de traitement. Vous recevrez une confirmation par email.</p>
        <Link to="/"><Button variant="outline" className="w-full h-12 border-white/10 text-zinc-300 hover:border-champagne hover:text-champagne">Retour a l'accueil</Button></Link>
      </div>
    </main>
  );
}
