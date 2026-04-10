import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { ArrowLeft, Spinner, Eye } from "@phosphor-icons/react";
import { useAuth } from "../../context/AuthContext";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../../components/ui/dialog";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AdminOrders() {
  const navigate = useNavigate();
  const { user, token, loading: authLoading } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState(null);

  useEffect(() => {
    if (!authLoading) {
      if (!user || !user.is_admin) {
        navigate("/login");
        return;
      }
      fetchOrders();
    }
  }, [user, authLoading]);

  const fetchOrders = async () => {
    try {
      const res = await axios.get(`${API}/admin/orders`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setOrders(res.data);
    } catch (err) {
      console.error("Error fetching orders:", err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusStyle = (status) => {
    switch (status) {
      case "paid":
        return "bg-[#34C759]/10 text-[#34C759]";
      case "pending":
        return "bg-[#FFCC00]/10 text-[#FFCC00]";
      default:
        return "bg-[#FF3B30]/10 text-[#FF3B30]";
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case "paid":
        return "Payé";
      case "pending":
        return "En attente";
      default:
        return status;
    }
  };

  if (authLoading || loading) {
    return (
      <main className="min-h-screen bg-[#FAFAFA] flex items-center justify-center">
        <Spinner className="w-12 h-12 text-[#0055FF] animate-spin" />
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#FAFAFA]" data-testid="admin-orders">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <button
            onClick={() => navigate("/admin")}
            className="p-2 hover:bg-[#E4E4E7] transition-colors"
          >
            <ArrowLeft weight="bold" className="w-5 h-5" />
          </button>
          <div>
            <h1
              className="text-3xl font-black text-[#0A0A0A]"
              style={{ fontFamily: 'Cabinet Grotesk' }}
            >
              Commandes
            </h1>
            <p className="text-[#52525B]">{orders.length} commandes</p>
          </div>
        </div>

        {/* Orders Table */}
        <div className="bg-white border border-[#E4E4E7] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="admin-table" data-testid="orders-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Client</th>
                  <th>Produits</th>
                  <th>Total</th>
                  <th>Paiement</th>
                  <th>Statut</th>
                  <th>Date</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {orders.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="text-center text-[#52525B] py-12">
                      Aucune commande
                    </td>
                  </tr>
                ) : (
                  orders.map((order) => (
                    <tr key={order.id} data-testid={`order-row-${order.id}`}>
                      <td className="font-mono text-sm">#{order.id?.slice(0, 8)}</td>
                      <td>{order.user_email}</td>
                      <td>
                        <span className="text-sm text-[#52525B]">
                          {order.items?.length || 0} article(s)
                        </span>
                      </td>
                      <td className="font-medium text-[#0055FF]">
                        ${order.total?.toFixed(2)}
                      </td>
                      <td className="text-sm capitalize">
                        {order.payment_method === "stripe" ? "Carte" : "Mobile Money"}
                      </td>
                      <td>
                        <span className={`px-2 py-1 text-xs font-medium ${getStatusStyle(order.payment_status)}`}>
                          {getStatusLabel(order.payment_status)}
                        </span>
                      </td>
                      <td className="text-[#52525B] text-sm">
                        {new Date(order.created_at).toLocaleDateString("fr-FR")}
                      </td>
                      <td className="text-right">
                        <button
                          onClick={() => setSelectedOrder(order)}
                          className="p-2 hover:bg-[#F4F4F5] transition-colors"
                          data-testid={`view-order-${order.id}`}
                        >
                          <Eye weight="regular" className="w-4 h-4 text-[#52525B]" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Order Detail Dialog */}
      <Dialog open={!!selectedOrder} onOpenChange={() => setSelectedOrder(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Cabinet Grotesk' }}>
              Commande #{selectedOrder?.id?.slice(0, 8)}
            </DialogTitle>
          </DialogHeader>

          {selectedOrder && (
            <div className="mt-4 space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-[#52525B]">Client</p>
                  <p className="font-medium">{selectedOrder.user_email}</p>
                </div>
                <div>
                  <p className="text-[#52525B]">Date</p>
                  <p className="font-medium">
                    {new Date(selectedOrder.created_at).toLocaleDateString("fr-FR", {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
                <div>
                  <p className="text-[#52525B]">Mode de paiement</p>
                  <p className="font-medium capitalize">
                    {selectedOrder.payment_method === "stripe" ? "Carte bancaire" : "Mobile Money"}
                  </p>
                </div>
                <div>
                  <p className="text-[#52525B]">Statut</p>
                  <span className={`inline-block px-2 py-1 text-xs font-medium ${getStatusStyle(selectedOrder.payment_status)}`}>
                    {getStatusLabel(selectedOrder.payment_status)}
                  </span>
                </div>
              </div>

              <div className="border-t border-[#E4E4E7] pt-4">
                <p className="font-medium mb-3">Articles</p>
                <div className="space-y-2">
                  {selectedOrder.items?.map((item, idx) => (
                    <div key={idx} className="flex justify-between text-sm">
                      <span>
                        {item.name} <span className="text-[#52525B]">x{item.quantity}</span>
                      </span>
                      <span className="font-medium">${item.total?.toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="border-t border-[#E4E4E7] pt-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-[#52525B]">Sous-total</span>
                  <span>${selectedOrder.subtotal?.toFixed(2)}</span>
                </div>
                {selectedOrder.discount > 0 && (
                  <div className="flex justify-between text-sm text-[#34C759]">
                    <span>Réduction ({selectedOrder.promo_code})</span>
                    <span>-${selectedOrder.discount?.toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between font-semibold pt-2 border-t border-[#E4E4E7]">
                  <span>Total</span>
                  <span className="text-[#0055FF]">${selectedOrder.total?.toFixed(2)}</span>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </main>
  );
}
