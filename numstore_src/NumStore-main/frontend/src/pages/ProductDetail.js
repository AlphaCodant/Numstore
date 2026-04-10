import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { Book, Layout, Desktop, GraduationCap, MusicNote, ShoppingCart, Download, ArrowLeft } from "@phosphor-icons/react";
import { useCart } from "../context/CartContext";
import { toast } from "sonner";
import { Button } from "../components/ui/button";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const categoryMap = {
  ebook: { label: "E-book", icon: Book },
  template: { label: "Template", icon: Layout },
  software: { label: "Logiciel", icon: Desktop },
  course: { label: "Cours", icon: GraduationCap },
  audio: { label: "Audio", icon: MusicNote },
};

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const { addItem } = useCart();

  useEffect(() => {
    fetchProduct();
  }, [id]);

  const fetchProduct = async () => {
    try {
      const res = await axios.get(`${API}/products/${id}`);
      setProduct(res.data);
    } catch (err) {
      toast.error("Produit non trouvé");
      navigate("/");
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = () => {
    addItem(product);
    toast.success(`${product.name} ajouté au panier`);
  };

  const handleBuyNow = () => {
    addItem(product);
    navigate("/checkout");
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="animate-pulse">
          <div className="h-8 bg-[#F4F4F5] w-32 mb-8" />
          <div className="grid md:grid-cols-2 gap-12">
            <div className="h-[400px] bg-[#F4F4F5]" />
            <div className="space-y-4">
              <div className="h-8 bg-[#F4F4F5] w-3/4" />
              <div className="h-4 bg-[#F4F4F5] w-full" />
              <div className="h-4 bg-[#F4F4F5] w-2/3" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!product) return null;

  const category = categoryMap[product.category] || { label: product.category, icon: null };
  const CategoryIcon = category.icon;

  return (
    <main className="min-h-screen bg-white" data-testid="product-detail-page">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Back button */}
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-[#52525B] hover:text-[#0A0A0A] mb-8 transition-colors"
          data-testid="back-button"
        >
          <ArrowLeft weight="bold" className="w-5 h-5" />
          Retour
        </button>

        <div className="grid md:grid-cols-2 gap-12">
          {/* Image */}
          <div className="relative">
            <img
              src={product.image_url || "https://images.unsplash.com/photo-1764452846368-2709775eb926?w=600"}
              alt={product.name}
              className="w-full h-[400px] md:h-[500px] object-cover"
              data-testid="product-image"
            />
            <div className="absolute top-4 left-4 flex items-center gap-2 px-3 py-2 bg-white text-sm font-medium text-[#52525B]">
              {CategoryIcon && <CategoryIcon weight="duotone" className="w-4 h-4" />}
              {category.label}
            </div>
          </div>

          {/* Details */}
          <div className="flex flex-col">
            <h1
              className="text-3xl sm:text-4xl font-black text-[#0A0A0A] mb-4"
              style={{ fontFamily: 'Cabinet Grotesk' }}
              data-testid="product-name"
            >
              {product.name}
            </h1>

            <p className="text-lg text-[#52525B] mb-6" data-testid="product-description">
              {product.description}
            </p>

            {/* Features */}
            <div className="border-t border-b border-[#E4E4E7] py-6 mb-6 space-y-4">
              <div className="flex items-center gap-3">
                <Download weight="duotone" className="w-5 h-5 text-[#0055FF]" />
                <span className="text-sm text-[#52525B]">
                  Téléchargement instantané après achat
                </span>
              </div>
              {product.file_size && (
                <div className="flex items-center gap-3">
                  <div className="w-5 h-5 flex items-center justify-center text-xs font-bold text-[#0055FF]">
                    MB
                  </div>
                  <span className="text-sm text-[#52525B]">
                    Taille du fichier: {product.file_size}
                  </span>
                </div>
              )}
            </div>

            {/* Price and actions */}
            <div className="mt-auto">
              <div className="mb-6">
                <span className="text-4xl font-black text-[#0055FF]" data-testid="product-price">
                  ${product.price.toFixed(2)}
                </span>
              </div>

              <div className="flex flex-col sm:flex-row gap-4">
                <Button
                  onClick={handleBuyNow}
                  className="flex-1 h-12 bg-[#0055FF] hover:bg-[#0040CC] text-white font-medium"
                  data-testid="buy-now-button"
                >
                  Acheter maintenant
                </Button>
                <Button
                  onClick={handleAddToCart}
                  variant="outline"
                  className="flex-1 h-12 border-[#0A0A0A] text-[#0A0A0A] hover:bg-[#0A0A0A] hover:text-white font-medium"
                  data-testid="add-to-cart-button"
                >
                  <ShoppingCart weight="bold" className="w-5 h-5 mr-2" />
                  Ajouter au panier
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
