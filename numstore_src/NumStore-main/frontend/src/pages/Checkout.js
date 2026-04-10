import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { CreditCard, Phone, Tag, Spinner, CheckCircle, XCircle } from "@phosphor-icons/react";
import { useCart } from "../context/CartContext";
import { useAuth } from "../context/AuthContext";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Checkout() {
  const navigate = useNavigate();
  const { items, total, clearCart } = useCart();
  const { user } = useAuth();
  
  const [email, setEmail] = useState(user?.email || "");
  const [promoCode, setPromoCode] = useState("");
  const [discount, setDiscount] = useState(0);
  const [promoApplied, setPromoApplied] = useState(false);
  const [promoError, setPromoError] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("stripe");
  const [loading, setLoading] = useState(false);

  const subtotal = total;
  const discountAmount = subtotal * (discount / 100);
  const finalTotal = subtotal - discountAmount;

  const validatePromoCode = async () => {
    if (!promoCode.trim()) return;
    
    try {
      const res = await axios.post(`${API}/promo-codes/validate?code=${promoCode}`);
      setDiscount(res.data.discount_percent);
      setPromoApplied(true);
      setPromoError("");
      toast.success(`Code promo appliqué: -${res.data.discount_percent}%`);
    } catch (err) {
      setPromoError(err.response?.data?.detail || "Code invalide");
      setPromoApplied(false);
      setDiscount(0);
    }
  };

  const handleCheckout = async () => {
    if (!email.trim()) {
      toast.error("Veuillez entrer votre email");
      return;
    }

    if (items.length === 0) {
      toast.error("Votre panier est vide");
      return;
    }

    setLoading(true);

    try {
      const res = await axios.post(`${API}/checkout/create-session`, {
        items: items.map((item) => ({
          product_id: item.id,
          quantity: item.quantity,
        })),
        email,
        promo_code: promoApplied ? promoCode : null,
        payment_method: paymentMethod,
        origin_url: window.location.origin,
      });

      if (paymentMethod === "stripe" && res.data.checkout_url) {
        // Redirect to Stripe checkout
        window.location.href = res.data.checkout_url;
      } else if (paymentMethod === "mobile_money") {
        // For mobile money, show instructions (mock for MVP)
        toast.info("Mobile Money: Cette fonctionnalité sera disponible bientôt avec Flutterwave");
        // In production, integrate with Flutterwave
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || "Erreur lors du paiement");
    } finally {
      setLoading(false);
    }
  };

  if (items.length === 0) {
    navigate("/cart");
    return null;
  }

  return (
    <main className="min-h-screen bg-[#FAFAFA]" data-testid="checkout-page">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1
          className="text-3xl font-black text-[#0A0A0A] mb-8"
          style={{ fontFamily: 'Cabinet Grotesk' }}
        >
          Paiement
        </h1>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left: Payment form */}
          <div className="space-y-6">
            {/* Email */}
            <div className="bg-white border border-[#E4E4E7] p-6">
              <h2 className="text-lg font-semibold text-[#0A0A0A] mb-4" style={{ fontFamily: 'Cabinet Grotesk' }}>
                Email
              </h2>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="votre@email.com"
                className="h-12"
                data-testid="checkout-email"
              />
              <p className="text-xs text-[#52525B] mt-2">
                Vous recevrez les liens de téléchargement à cette adresse.
              </p>
            </div>

            {/* Promo code */}
            <div className="bg-white border border-[#E4E4E7] p-6">
              <h2 className="text-lg font-semibold text-[#0A0A0A] mb-4" style={{ fontFamily: 'Cabinet Grotesk' }}>
                Code promo
              </h2>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Tag weight="regular" className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#52525B]" />
                  <Input
                    type="text"
                    value={promoCode}
                    onChange={(e) => {
                      setPromoCode(e.target.value.toUpperCase());
                      setPromoError("");
                    }}
                    placeholder="WELCOME10"
                    className="h-12 pl-10"
                    disabled={promoApplied}
                    data-testid="promo-code-input"
                  />
                </div>
                <Button
                  onClick={validatePromoCode}
                  variant="outline"
                  className="h-12 px-6"
                  disabled={promoApplied || !promoCode.trim()}
                  data-testid="apply-promo"
                >
                  Appliquer
                </Button>
              </div>
              {promoApplied && (
                <div className="flex items-center gap-2 mt-2 text-sm text-[#34C759]">
                  <CheckCircle weight="fill" className="w-4 h-4" />
                  Code appliqué: -{discount}%
                </div>
              )}
              {promoError && (
                <div className="flex items-center gap-2 mt-2 text-sm text-[#FF3B30]">
                  <XCircle weight="fill" className="w-4 h-4" />
                  {promoError}
                </div>
              )}
            </div>

            {/* Payment method */}
            <div className="bg-white border border-[#E4E4E7] p-6">
              <h2 className="text-lg font-semibold text-[#0A0A0A] mb-4" style={{ fontFamily: 'Cabinet Grotesk' }}>
                Mode de paiement
              </h2>
              <div className="space-y-3">
                <label
                  className={`flex items-center gap-4 p-4 border cursor-pointer transition-all ${
                    paymentMethod === "stripe"
                      ? "border-[#0055FF] bg-blue-50/50"
                      : "border-[#E4E4E7] hover:border-[#52525B]"
                  }`}
                  data-testid="payment-stripe"
                >
                  <input
                    type="radio"
                    name="payment"
                    value="stripe"
                    checked={paymentMethod === "stripe"}
                    onChange={(e) => setPaymentMethod(e.target.value)}
                    className="sr-only"
                  />
                  <CreditCard weight="duotone" className="w-8 h-8 text-[#0055FF]" />
                  <div className="flex-1">
                    <p className="font-medium text-[#0A0A0A]">Carte bancaire</p>
                    <p className="text-sm text-[#52525B]">Visa, Mastercard, AMEX</p>
                  </div>
                  <div className={`w-5 h-5 rounded-full border-2 ${
                    paymentMethod === "stripe" ? "border-[#0055FF] bg-[#0055FF]" : "border-[#E4E4E7]"
                  }`}>
                    {paymentMethod === "stripe" && (
                      <div className="w-full h-full flex items-center justify-center">
                        <div className="w-2 h-2 bg-white rounded-full" />
                      </div>
                    )}
                  </div>
                </label>

                <label
                  className={`flex items-center gap-4 p-4 border cursor-pointer transition-all ${
                    paymentMethod === "mobile_money"
                      ? "border-[#0055FF] bg-blue-50/50"
                      : "border-[#E4E4E7] hover:border-[#52525B]"
                  }`}
                  data-testid="payment-mobile-money"
                >
                  <input
                    type="radio"
                    name="payment"
                    value="mobile_money"
                    checked={paymentMethod === "mobile_money"}
                    onChange={(e) => setPaymentMethod(e.target.value)}
                    className="sr-only"
                  />
                  <Phone weight="duotone" className="w-8 h-8 text-[#FFCC00]" />
                  <div className="flex-1">
                    <p className="font-medium text-[#0A0A0A]">Mobile Money</p>
                    <p className="text-sm text-[#52525B]">MTN, Orange, Airtel, Wave</p>
                  </div>
                  <div className={`w-5 h-5 rounded-full border-2 ${
                    paymentMethod === "mobile_money" ? "border-[#0055FF] bg-[#0055FF]" : "border-[#E4E4E7]"
                  }`}>
                    {paymentMethod === "mobile_money" && (
                      <div className="w-full h-full flex items-center justify-center">
                        <div className="w-2 h-2 bg-white rounded-full" />
                      </div>
                    )}
                  </div>
                </label>
              </div>
            </div>
          </div>

          {/* Right: Order summary */}
          <div>
            <div className="bg-white border border-[#E4E4E7] p-6 sticky top-24">
              <h2 className="text-lg font-semibold text-[#0A0A0A] mb-4" style={{ fontFamily: 'Cabinet Grotesk' }}>
                Récapitulatif
              </h2>

              {/* Items */}
              <div className="space-y-4 mb-6 max-h-64 overflow-y-auto">
                {items.map((item) => (
                  <div key={item.id} className="flex gap-3" data-testid={`summary-item-${item.id}`}>
                    <img
                      src={item.image_url || "https://images.unsplash.com/photo-1764452846368-2709775eb926?w=100"}
                      alt={item.name}
                      className="w-16 h-16 object-cover flex-shrink-0"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-[#0A0A0A] text-sm truncate">{item.name}</p>
                      <p className="text-xs text-[#52525B]">Qté: {item.quantity}</p>
                    </div>
                    <span className="font-medium text-sm">${(item.price * item.quantity).toFixed(2)}</span>
                  </div>
                ))}
              </div>

              {/* Totals */}
              <div className="border-t border-[#E4E4E7] pt-4 space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-[#52525B]">Sous-total</span>
                  <span className="font-medium">${subtotal.toFixed(2)}</span>
                </div>
                {promoApplied && (
                  <div className="flex justify-between text-sm text-[#34C759]">
                    <span>Réduction ({discount}%)</span>
                    <span>-${discountAmount.toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between pt-3 border-t border-[#E4E4E7]">
                  <span className="font-semibold">Total</span>
                  <span className="text-2xl font-bold text-[#0055FF]">${finalTotal.toFixed(2)}</span>
                </div>
              </div>

              <Button
                onClick={handleCheckout}
                disabled={loading}
                className="w-full h-14 mt-6 bg-[#0055FF] hover:bg-[#0040CC] text-white font-medium text-lg"
                data-testid="pay-button"
              >
                {loading ? (
                  <Spinner className="w-6 h-6 animate-spin" />
                ) : (
                  `Payer $${finalTotal.toFixed(2)}`
                )}
              </Button>

              <p className="text-xs text-center text-[#52525B] mt-4">
                Paiement sécurisé par Stripe
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
