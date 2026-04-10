import { Link, useNavigate } from "react-router-dom";
import { Trash, Plus, Minus, ShoppingCart, ArrowRight } from "@phosphor-icons/react";
import { useCart } from "../context/CartContext";
import { Button } from "../components/ui/button";

export default function Cart() {
  const { items, removeItem, updateQuantity, total, clearCart } = useCart();
  const navigate = useNavigate();

  if (items.length === 0) {
    return (
      <main className="min-h-screen bg-white" data-testid="cart-page-empty">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <ShoppingCart weight="light" className="w-24 h-24 mx-auto text-[#E4E4E7] mb-6" />
            <h1
              className="text-3xl font-black text-[#0A0A0A] mb-4"
              style={{ fontFamily: 'Cabinet Grotesk' }}
            >
              Votre panier est vide
            </h1>
            <p className="text-[#52525B] mb-8">
              Découvrez nos produits numériques et commencez vos achats.
            </p>
            <Link
              to="/"
              className="inline-flex items-center px-6 py-3 bg-[#0055FF] text-white font-medium hover:bg-[#0040CC] transition-all"
              data-testid="continue-shopping"
            >
              Explorer les produits
            </Link>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-white" data-testid="cart-page">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1
          className="text-3xl font-black text-[#0A0A0A] mb-8"
          style={{ fontFamily: 'Cabinet Grotesk' }}
        >
          Votre panier ({items.length} {items.length === 1 ? 'article' : 'articles'})
        </h1>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Items list */}
          <div className="lg:col-span-2 space-y-4">
            {items.map((item) => (
              <div
                key={item.id}
                className="flex gap-4 p-4 border border-[#E4E4E7]"
                data-testid={`cart-item-${item.id}`}
              >
                <img
                  src={item.image_url || "https://images.unsplash.com/photo-1764452846368-2709775eb926?w=200"}
                  alt={item.name}
                  className="w-24 h-24 object-cover flex-shrink-0"
                />
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-[#0A0A0A] mb-1 truncate" style={{ fontFamily: 'Cabinet Grotesk' }}>
                    {item.name}
                  </h3>
                  <p className="text-sm text-[#52525B] mb-3">Produit numérique</p>
                  
                  {/* Quantity controls */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => updateQuantity(item.id, item.quantity - 1)}
                      className="w-8 h-8 flex items-center justify-center border border-[#E4E4E7] hover:bg-[#F4F4F5] transition-colors"
                      data-testid={`decrease-${item.id}`}
                    >
                      <Minus weight="bold" className="w-4 h-4" />
                    </button>
                    <span className="w-8 text-center font-medium">{item.quantity}</span>
                    <button
                      onClick={() => updateQuantity(item.id, item.quantity + 1)}
                      className="w-8 h-8 flex items-center justify-center border border-[#E4E4E7] hover:bg-[#F4F4F5] transition-colors"
                      data-testid={`increase-${item.id}`}
                    >
                      <Plus weight="bold" className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                
                <div className="flex flex-col items-end justify-between">
                  <span className="font-bold text-[#0055FF]">
                    ${(item.price * item.quantity).toFixed(2)}
                  </span>
                  <button
                    onClick={() => removeItem(item.id)}
                    className="p-2 text-[#52525B] hover:text-[#FF3B30] hover:bg-red-50 transition-colors"
                    data-testid={`remove-${item.id}`}
                  >
                    <Trash weight="regular" className="w-5 h-5" />
                  </button>
                </div>
              </div>
            ))}

            <button
              onClick={clearCart}
              className="text-sm text-[#52525B] hover:text-[#FF3B30] transition-colors"
              data-testid="clear-cart"
            >
              Vider le panier
            </button>
          </div>

          {/* Order summary */}
          <div className="lg:col-span-1">
            <div className="border border-[#E4E4E7] p-6 sticky top-24">
              <h2 className="text-lg font-semibold text-[#0A0A0A] mb-4" style={{ fontFamily: 'Cabinet Grotesk' }}>
                Résumé de la commande
              </h2>
              
              <div className="space-y-3 mb-6">
                <div className="flex justify-between text-sm">
                  <span className="text-[#52525B]">Sous-total</span>
                  <span className="font-medium">${total.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-[#52525B]">Frais</span>
                  <span className="font-medium text-[#34C759]">Gratuit</span>
                </div>
              </div>

              <div className="border-t border-[#E4E4E7] pt-4 mb-6">
                <div className="flex justify-between">
                  <span className="font-semibold">Total</span>
                  <span className="text-xl font-bold text-[#0055FF]">${total.toFixed(2)}</span>
                </div>
              </div>

              <Button
                onClick={() => navigate("/checkout")}
                className="w-full h-12 bg-[#0055FF] hover:bg-[#0040CC] text-white font-medium"
                data-testid="checkout-button"
              >
                Passer la commande
                <ArrowRight weight="bold" className="w-5 h-5 ml-2" />
              </Button>

              <Link
                to="/"
                className="block text-center text-sm text-[#52525B] hover:text-[#0055FF] mt-4 transition-colors"
              >
                Continuer les achats
              </Link>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
