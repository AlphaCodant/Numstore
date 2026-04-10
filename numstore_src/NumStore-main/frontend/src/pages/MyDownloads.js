import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Download, Package, Spinner, ArrowSquareOut } from "@phosphor-icons/react";
import { useAuth } from "../context/AuthContext";
import { Button } from "../components/ui/button";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function MyDownloads() {
  const navigate = useNavigate();
  const { user, token, loading: authLoading } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !user) {
      navigate("/login");
      return;
    }
    if (user) {
      fetchOrders();
    }
  }, [user, authLoading]);

  const fetchOrders = async () => {
    try {
      const res = await axios.get(`${API}/orders/my-orders`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setOrders(res.data);
    } catch (err) {
      console.error("Error fetching orders:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (productId, productName) => {
    try {
      const res = await axios.get(`${API}/downloads/${productId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (res.data.download_url) {
        // In production, this would be a real download link
        toast.success(`Téléchargement de "${productName}" démarré`);
        window.open(res.data.download_url, "_blank");
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || "Erreur lors du téléchargement");
    }
  };

  if (authLoading || loading) {
    return (
      <main className="min-h-screen bg-white flex items-center justify-center">
        <Spinner className="w-12 h-12 text-[#0055FF] animate-spin" />
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-white" data-testid="my-downloads-page">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1
          className="text-3xl font-black text-[#0A0A0A] mb-8"
          style={{ fontFamily: 'Cabinet Grotesk' }}
        >
          Mes téléchargements
        </h1>

        {orders.length === 0 ? (
          <div className="text-center py-16 border border-[#E4E4E7]">
            <Package weight="light" className="w-20 h-20 text-[#E4E4E7] mx-auto mb-6" />
            <h2 className="text-xl font-semibold text-[#0A0A0A] mb-2" style={{ fontFamily: 'Cabinet Grotesk' }}>
              Aucun achat
            </h2>
            <p className="text-[#52525B] mb-6">
              Vous n'avez pas encore effectué d'achat.
            </p>
            <Button
              onClick={() => navigate("/")}
              className="bg-[#0055FF] hover:bg-[#0040CC]"
            >
              Explorer les produits
            </Button>
          </div>
        ) : (
          <div className="space-y-6">
            {orders.map((order) => (
              <div
                key={order.id}
                className="border border-[#E4E4E7] p-6"
                data-testid={`order-${order.id}`}
              >
                <div className="flex items-center justify-between mb-4 pb-4 border-b border-[#E4E4E7]">
                  <div>
                    <p className="text-sm text-[#52525B]">
                      Commande #{order.id?.slice(0, 8)}
                    </p>
                    <p className="text-xs text-[#52525B]">
                      {new Date(order.created_at).toLocaleDateString("fr-FR", {
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                      })}
                    </p>
                  </div>
                  <span className="px-3 py-1 bg-[#34C759]/10 text-[#34C759] text-sm font-medium">
                    Payé
                  </span>
                </div>

                <div className="space-y-4">
                  {order.items?.map((item, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-4"
                      data-testid={`download-item-${item.product_id}`}
                    >
                      <div className="flex-1">
                        <p className="font-medium text-[#0A0A0A]">{item.name}</p>
                        <p className="text-sm text-[#52525B]">
                          ${item.price?.toFixed(2)} x {item.quantity}
                        </p>
                      </div>
                      <Button
                        onClick={() => handleDownload(item.product_id, item.name)}
                        variant="outline"
                        className="gap-2"
                        data-testid={`download-btn-${item.product_id}`}
                      >
                        <Download weight="bold" className="w-4 h-4" />
                        Télécharger
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
