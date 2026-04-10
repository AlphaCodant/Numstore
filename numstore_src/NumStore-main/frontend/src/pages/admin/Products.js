import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Plus, Pencil, Trash2, Loader2, ArrowLeft } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../../components/ui/dialog";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const inputCls = "bg-noir border-white/10 text-white placeholder:text-zinc-600 focus:ring-champagne focus:border-champagne/30";

const categories = [
  { id: "ebook", label: "E-book" },
  { id: "template", label: "Template" },
  { id: "software", label: "Logiciel" },
  { id: "course", label: "Cours" },
  { id: "audio", label: "Audio" },
];

const initialForm = { name: "", description: "", price: "", category: "ebook", image_url: "", download_url: "", file_size: "" };

export default function AdminProducts() {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(initialForm);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem("admin_auth")) { navigate("/admin"); return; }
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try { const res = await axios.get(`${API}/admin/products`); setProducts(res.data); }
    catch (err) { console.error("Error:", err); }
    finally { setLoading(false); }
  };

  const openCreate = () => { setEditingId(null); setForm(initialForm); setDialogOpen(true); };
  const openEdit = (p) => { setEditingId(p.id); setForm({ name: p.name, description: p.description, price: p.price.toString(), category: p.category, image_url: p.image_url || "", download_url: p.download_url || "", file_size: p.file_size || "" }); setDialogOpen(true); };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.description || !form.price) { toast.error("Remplissez les champs obligatoires"); return; }
    setSaving(true);
    try {
      const payload = { ...form, price: parseFloat(form.price) };
      if (editingId) { await axios.put(`${API}/admin/products/${editingId}`, payload); toast.success("Produit mis a jour"); }
      else { await axios.post(`${API}/admin/products`, payload); toast.success("Produit cree"); }
      setDialogOpen(false); fetchProducts();
    } catch (err) { toast.error(err.response?.data?.detail || "Erreur"); }
    finally { setSaving(false); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Supprimer ce produit?")) return;
    try { await axios.delete(`${API}/admin/products/${id}`); toast.success("Produit supprime"); fetchProducts(); }
    catch { toast.error("Erreur lors de la suppression"); }
  };

  if (loading) return <main className="min-h-screen bg-noir flex items-center justify-center"><Loader2 className="w-8 h-8 text-champagne animate-spin" /></main>;

  return (
    <main className="min-h-screen bg-noir" data-testid="admin-products">
      <div className="max-w-6xl mx-auto px-6 lg:px-12 py-8">
        <div className="flex items-center gap-4 mb-8">
          <button onClick={() => navigate("/admin/dashboard")} className="p-2 text-zinc-500 hover:text-champagne transition-colors">
            <ArrowLeft className="w-5 h-5" strokeWidth={1.5} />
          </button>
          <div className="flex-1">
            <h1 className="text-3xl font-heading font-semibold text-white">Produits</h1>
            <p className="text-zinc-500 text-sm">{products.length} produits</p>
          </div>
          <Button onClick={openCreate} className="btn-gold gap-2" data-testid="add-product-btn">
            <Plus className="w-4 h-4" strokeWidth={1.5} /> Ajouter
          </Button>
        </div>

        <div className="bg-surface border border-white/5">
          {products.length === 0 ? (
            <div className="p-12 text-center text-zinc-600">Aucun produit. Cliquez sur "Ajouter" pour creer.</div>
          ) : (
            <div className="divide-y divide-white/5">
              {products.map(p => (
                <div key={p.id} className="flex items-center gap-4 p-4 hover:bg-white/[0.02]" data-testid={`product-${p.id}`}>
                  <img src={p.image_url || "https://images.unsplash.com/photo-1697292859784-c319e612ea15?w=100"} alt={p.name} className="w-14 h-14 object-cover border border-white/5" />
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-white text-sm truncate">{p.name}</p>
                    <p className="text-xs text-zinc-500">{p.category} | {p.price.toLocaleString("fr-FR")} FCFA {p.is_service ? "| Service" : ""}</p>
                  </div>
                  <div className="flex items-center gap-1">
                    <button onClick={() => openEdit(p)} className="p-2 text-zinc-500 hover:text-champagne transition-colors" data-testid={`edit-${p.id}`}>
                      <Pencil className="w-4 h-4" strokeWidth={1.5} />
                    </button>
                    <button onClick={() => handleDelete(p.id)} className="p-2 text-zinc-500 hover:text-red-400 transition-colors" data-testid={`delete-${p.id}`}>
                      <Trash2 className="w-4 h-4" strokeWidth={1.5} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg bg-surface border-white/10 text-white">
          <DialogHeader>
            <DialogTitle className="font-heading text-xl">{editingId ? "Modifier le produit" : "Nouveau produit"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4 mt-4">
            <div><label className="text-sm font-medium text-zinc-300 block mb-1">Nom *</label><Input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="Nom du produit" className={inputCls} data-testid="input-name" /></div>
            <div><label className="text-sm font-medium text-zinc-300 block mb-1">Description *</label>
              <textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="Description"
                className="w-full px-3 py-2 bg-noir border border-white/10 text-white placeholder:text-zinc-600 focus:ring-1 focus:ring-champagne focus:outline-none min-h-[80px]" data-testid="input-description" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="text-sm font-medium text-zinc-300 block mb-1">Prix (FCFA) *</label><Input type="number" min="0" value={form.price} onChange={e => setForm({ ...form, price: e.target.value })} placeholder="25000" className={inputCls} data-testid="input-price" /></div>
              <div><label className="text-sm font-medium text-zinc-300 block mb-1">Categorie</label>
                <Select value={form.category} onValueChange={v => setForm({ ...form, category: v })}>
                  <SelectTrigger className={inputCls} data-testid="select-category"><SelectValue /></SelectTrigger>
                  <SelectContent className="bg-surface border-white/10 text-white">
                    {categories.map(c => <SelectItem key={c.id} value={c.id}>{c.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div><label className="text-sm font-medium text-zinc-300 block mb-1">URL Image</label><Input value={form.image_url} onChange={e => setForm({ ...form, image_url: e.target.value })} placeholder="https://..." className={inputCls} data-testid="input-image" /></div>
            <div><label className="text-sm font-medium text-zinc-300 block mb-1">URL Telechargement</label><Input value={form.download_url} onChange={e => setForm({ ...form, download_url: e.target.value })} placeholder="https://..." className={inputCls} data-testid="input-download" /></div>
            <div><label className="text-sm font-medium text-zinc-300 block mb-1">Taille fichier</label><Input value={form.file_size} onChange={e => setForm({ ...form, file_size: e.target.value })} placeholder="15 MB" className={inputCls} data-testid="input-size" /></div>
            <div className="flex gap-3 pt-4">
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)} className="flex-1 border-white/10 text-zinc-300 hover:border-champagne hover:text-champagne">Annuler</Button>
              <Button type="submit" disabled={saving} className="flex-1 btn-gold" data-testid="save-btn">
                {saving ? <Loader2 className="w-5 h-5 animate-spin" /> : editingId ? "Enregistrer" : "Creer"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </main>
  );
}
