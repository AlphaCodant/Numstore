import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { ArrowLeft, Mail, Loader2, CheckCircle, Globe, User, Clock, Star } from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const formatPrice = (price, currency = "XOF") => {
  if (currency === "XOF") {
    return `${price.toLocaleString("fr-FR")} FCFA`;
  }
  return `$${price.toFixed(2)}`;
};

export default function ProductPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState("");
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    fetchProduct();
  }, [id]);

  const fetchProduct = async () => {
    try {
      const res = await axios.get(`${API}/products/${id}`);
      setProduct(res.data);
    } catch (err) {
      toast.error("Produit non trouve");
      navigate("/");
    } finally {
      setLoading(false);
    }
  };

  const handlePurchase = async () => {
    if (!email.trim()) {
      toast.error("Veuillez entrer votre adresse email");
      return;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      toast.error("Veuillez entrer une adresse email valide");
      return;
    }
    setProcessing(true);
    if (product.is_service) {
      navigate(`/portfolio/form?product_id=${id}&email=${encodeURIComponent(email)}`);
      return;
    }
    try {
      const res = await axios.post(`${API}/payment/create-session`, {
        product_id: id,
        email: email,
        origin_url: window.location.origin
      });
      if (res.data.checkout_url) {
        window.location.href = res.data.checkout_url;
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || "Erreur lors du paiement");
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-noir flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-champagne animate-spin" />
      </div>
    );
  }

  if (!product) return null;

  const isService = product.is_service;

  return (
    <main className="min-h-screen bg-noir" data-testid="product-page">
      <div className="max-w-5xl mx-auto px-6 lg:px-12 py-12">
        {/* Back */}
        <button
          onClick={() => navigate("/")}
          className="flex items-center gap-2 text-zinc-500 hover:text-champagne mb-10 transition-colors text-sm"
          data-testid="back-button"
        >
          <ArrowLeft className="w-4 h-4" strokeWidth={1.5} />
          Retour
        </button>

        <div className="grid md:grid-cols-2 gap-12">
          {/* Image */}
          <div className="relative overflow-hidden bg-surface border border-white/5">
            <img
              src={product.image_url || "https://images.unsplash.com/photo-1697292859784-c319e612ea15?w=600"}
              alt={product.name}
              className="w-full h-[400px] object-cover"
              data-testid="product-image"
            />
            {isService && (
              <div className="absolute top-4 left-4 flex items-center gap-1.5 px-3 py-1.5 bg-champagne text-noir text-xs font-bold tracking-wider uppercase">
                <Star className="w-3 h-3" fill="currentColor" strokeWidth={0} />
                Service Premium
              </div>
            )}
          </div>

          {/* Details */}
          <div className="flex flex-col">
            <h1
              className="text-3xl sm:text-4xl tracking-tight font-heading font-semibold text-white mb-4"
              data-testid="product-name"
            >
              {product.name}
            </h1>

            <p className="text-zinc-400 leading-relaxed mb-6" data-testid="product-description">
              {product.description}
            </p>

            {isService && (
              <div className="bg-surface border border-white/5 p-5 mb-6 space-y-3">
                <div className="flex items-center gap-3 text-sm text-zinc-300">
                  <Globe className="w-5 h-5 text-champagne flex-shrink-0" strokeWidth={1.5} />
                  <span>Site web heberge a votre nom</span>
                </div>
                <div className="flex items-center gap-3 text-sm text-zinc-300">
                  <User className="w-5 h-5 text-champagne flex-shrink-0" strokeWidth={1.5} />
                  <span>Design personnalise selon vos infos</span>
                </div>
                <div className="flex items-center gap-3 text-sm text-zinc-300">
                  <Clock className="w-5 h-5 text-champagne flex-shrink-0" strokeWidth={1.5} />
                  <span>Livraison sous 48-72h</span>
                </div>
              </div>
            )}

            {/* Price */}
            <div className="mb-8">
              <span className="text-4xl font-heading font-bold text-champagne" data-testid="product-price">
                {formatPrice(product.price, product.currency)}
              </span>
            </div>

            {/* Purchase */}
            <div className="bg-surface border border-white/5 p-6">
              <h3 className="font-heading text-lg font-semibold text-white mb-4">
                {isService ? "Commander ce service" : "Acheter maintenant"}
              </h3>

              <div className="space-y-4">
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" strokeWidth={1.5} />
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="votre@email.com"
                    className="h-12 pl-10 bg-noir border-white/10 text-white placeholder:text-zinc-600 focus:ring-champagne focus:border-champagne/30"
                    data-testid="email-input"
                  />
                </div>
                <p className="text-xs text-zinc-500">
                  {isService
                    ? "Vous remplirez un formulaire avec vos informations avant le paiement."
                    : "Vous recevrez votre code d'acces a cette adresse."}
                </p>

                <Button
                  onClick={handlePurchase}
                  disabled={processing}
                  className="w-full h-14 btn-gold text-base"
                  data-testid="purchase-button"
                >
                  {processing ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    `Payer ${formatPrice(product.price, product.currency)}`
                  )}
                </Button>
              </div>

              {!isService && (
                <div className="mt-4 pt-4 border-t border-white/5">
                  <div className="flex items-start gap-2 text-sm text-zinc-400">
                    <CheckCircle className="w-5 h-5 text-champagne flex-shrink-0 mt-0.5" strokeWidth={1.5} />
                    <span>Code d'acces valide 6 heures. Renouvelable gratuitement.</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
