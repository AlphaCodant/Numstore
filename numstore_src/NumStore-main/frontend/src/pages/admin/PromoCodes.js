import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Plus, Trash, Spinner, ArrowLeft, Tag } from "@phosphor-icons/react";
import { useAuth } from "../../context/AuthContext";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../../components/ui/dialog";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AdminPromoCodes() {
  const navigate = useNavigate();
  const { user, token, loading: authLoading } = useAuth();
  const [promoCodes, setPromoCodes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    code: "",
    discount_percent: "",
    max_uses: "100",
    expires_at: "",
  });

  useEffect(() => {
    if (!authLoading) {
      if (!user || !user.is_admin) {
        navigate("/login");
        return;
      }
      fetchPromoCodes();
    }
  }, [user, authLoading]);

  const fetchPromoCodes = async () => {
    try {
      const res = await axios.get(`${API}/admin/promo-codes`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setPromoCodes(res.data);
    } catch (err) {
      console.error("Error fetching promo codes:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.code || !formData.discount_percent) {
      toast.error("Veuillez remplir tous les champs obligatoires");
      return;
    }

    setSaving(true);
    try {
      await axios.post(
        `${API}/admin/promo-codes`,
        {
          code: formData.code.toUpperCase(),
          discount_percent: parseFloat(formData.discount_percent),
          max_uses: parseInt(formData.max_uses) || 100,
          expires_at: formData.expires_at || null,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success("Code promo créé");
      setDialogOpen(false);
      setFormData({ code: "", discount_percent: "", max_uses: "100", expires_at: "" });
      fetchPromoCodes();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Erreur lors de la création");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (codeId) => {
    if (!window.confirm("Êtes-vous sûr de vouloir supprimer ce code promo?")) {
      return;
    }

    try {
      await axios.delete(`${API}/admin/promo-codes/${codeId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      toast.success("Code promo supprimé");
      fetchPromoCodes();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Erreur lors de la suppression");
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
    <main className="min-h-screen bg-[#FAFAFA]" data-testid="admin-promo-codes">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <button
            onClick={() => navigate("/admin")}
            className="p-2 hover:bg-[#E4E4E7] transition-colors"
          >
            <ArrowLeft weight="bold" className="w-5 h-5" />
          </button>
          <div className="flex-1">
            <h1
              className="text-3xl font-black text-[#0A0A0A]"
              style={{ fontFamily: 'Cabinet Grotesk' }}
            >
              Codes Promo
            </h1>
            <p className="text-[#52525B]">{promoCodes.length} codes actifs</p>
          </div>
          <Button
            onClick={() => setDialogOpen(true)}
            className="bg-[#0055FF] hover:bg-[#0040CC] gap-2"
            data-testid="add-promo-btn"
          >
            <Plus weight="bold" className="w-5 h-5" />
            Créer
          </Button>
        </div>

        {/* Promo Codes Table */}
        <div className="bg-white border border-[#E4E4E7] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="admin-table" data-testid="promo-codes-table">
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Réduction</th>
                  <th>Utilisations</th>
                  <th>Expiration</th>
                  <th>Statut</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {promoCodes.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center text-[#52525B] py-12">
                      <Tag weight="light" className="w-12 h-12 mx-auto mb-4 text-[#E4E4E7]" />
                      <p>Aucun code promo</p>
                    </td>
                  </tr>
                ) : (
                  promoCodes.map((promo) => (
                    <tr key={promo.id} data-testid={`promo-row-${promo.id}`}>
                      <td>
                        <span className="font-mono font-medium bg-[#F4F4F5] px-2 py-1">
                          {promo.code}
                        </span>
                      </td>
                      <td className="font-medium text-[#34C759]">
                        -{promo.discount_percent}%
                      </td>
                      <td>
                        <span className="text-[#52525B]">
                          {promo.current_uses} / {promo.max_uses}
                        </span>
                      </td>
                      <td className="text-[#52525B] text-sm">
                        {promo.expires_at
                          ? new Date(promo.expires_at).toLocaleDateString("fr-FR")
                          : "Jamais"}
                      </td>
                      <td>
                        <span
                          className={`px-2 py-1 text-xs font-medium ${
                            promo.is_active
                              ? "bg-[#34C759]/10 text-[#34C759]"
                              : "bg-[#FF3B30]/10 text-[#FF3B30]"
                          }`}
                        >
                          {promo.is_active ? "Actif" : "Inactif"}
                        </span>
                      </td>
                      <td className="text-right">
                        <button
                          onClick={() => handleDelete(promo.id)}
                          className="p-2 hover:bg-red-50 transition-colors"
                          data-testid={`delete-promo-${promo.id}`}
                        >
                          <Trash weight="regular" className="w-4 h-4 text-[#FF3B30]" />
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

      {/* Create Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Cabinet Grotesk' }}>
              Nouveau code promo
            </DialogTitle>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4 mt-4">
            <div>
              <label className="text-sm font-medium text-[#0A0A0A] block mb-1">
                Code *
              </label>
              <Input
                value={formData.code}
                onChange={(e) =>
                  setFormData({ ...formData, code: e.target.value.toUpperCase() })
                }
                placeholder="SUMMER20"
                className="uppercase"
                data-testid="promo-code-input"
              />
            </div>

            <div>
              <label className="text-sm font-medium text-[#0A0A0A] block mb-1">
                Réduction (%) *
              </label>
              <Input
                type="number"
                min="1"
                max="100"
                value={formData.discount_percent}
                onChange={(e) =>
                  setFormData({ ...formData, discount_percent: e.target.value })
                }
                placeholder="20"
                data-testid="promo-discount-input"
              />
            </div>

            <div>
              <label className="text-sm font-medium text-[#0A0A0A] block mb-1">
                Nombre max d'utilisations
              </label>
              <Input
                type="number"
                min="1"
                value={formData.max_uses}
                onChange={(e) =>
                  setFormData({ ...formData, max_uses: e.target.value })
                }
                placeholder="100"
                data-testid="promo-max-uses-input"
              />
            </div>

            <div>
              <label className="text-sm font-medium text-[#0A0A0A] block mb-1">
                Date d'expiration (optionnel)
              </label>
              <Input
                type="date"
                value={formData.expires_at}
                onChange={(e) =>
                  setFormData({ ...formData, expires_at: e.target.value })
                }
                data-testid="promo-expires-input"
              />
            </div>

            <div className="flex gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => setDialogOpen(false)}
                className="flex-1"
              >
                Annuler
              </Button>
              <Button
                type="submit"
                disabled={saving}
                className="flex-1 bg-[#0055FF] hover:bg-[#0040CC]"
                data-testid="save-promo-btn"
              >
                {saving ? <Spinner className="w-5 h-5 animate-spin" /> : "Créer"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </main>
  );
}
