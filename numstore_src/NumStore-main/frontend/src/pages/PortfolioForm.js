import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import axios from "axios";
import {
  User, Briefcase, GraduationCap, Globe, Linkedin, Twitter, Github, Loader2,
  CheckCircle, Plus, Trash2, CreditCard
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const formatPrice = (price, currency = "XOF") => {
  if (currency === "XOF") return `${price.toLocaleString("fr-FR")} FCFA`;
  return `$${price.toFixed(2)}`;
};

const inputCls = "h-12 bg-noir border-white/10 text-white placeholder:text-zinc-600 focus:ring-champagne focus:border-champagne/30";
const textareaCls = "w-full px-3 py-3 bg-noir border border-white/10 text-white placeholder:text-zinc-600 focus:ring-1 focus:ring-champagne focus:border-champagne/30 focus:outline-none min-h-[120px]";

export default function PortfolioForm() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const productId = searchParams.get("product_id");
  const initialEmail = searchParams.get("email") || "";

  const [product, setProduct] = useState(null);
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    email: initialEmail, full_name: "", job_title: "", bio: "", phone: "", location: "", photo_url: "",
    skills: [], experiences: [], education: [], projects: [],
    linkedin_url: "", twitter_url: "", github_url: "", website_url: ""
  });
  const [newSkill, setNewSkill] = useState("");

  useEffect(() => {
    if (!productId) { toast.error("Produit non specifie"); navigate("/"); return; }
    fetchProduct();
  }, [productId]);

  const fetchProduct = async () => {
    try { const res = await axios.get(`${API}/products/${productId}`); setProduct(res.data); }
    catch { toast.error("Produit non trouve"); navigate("/"); }
  };

  const addSkill = () => {
    if (newSkill.trim() && !form.skills.includes(newSkill.trim())) {
      setForm({ ...form, skills: [...form.skills, newSkill.trim()] }); setNewSkill("");
    }
  };
  const removeSkill = (skill) => setForm({ ...form, skills: form.skills.filter(s => s !== skill) });

  const addExperience = () => setForm({ ...form, experiences: [...form.experiences, { company: "", role: "", duration: "", description: "" }] });
  const updateExperience = (i, f, v) => { const u = [...form.experiences]; u[i][f] = v; setForm({ ...form, experiences: u }); };
  const removeExperience = (i) => setForm({ ...form, experiences: form.experiences.filter((_, idx) => idx !== i) });

  const addEducation = () => setForm({ ...form, education: [...form.education, { school: "", degree: "", year: "" }] });
  const updateEducation = (i, f, v) => { const u = [...form.education]; u[i][f] = v; setForm({ ...form, education: u }); };
  const removeEducation = (i) => setForm({ ...form, education: form.education.filter((_, idx) => idx !== i) });

  const addProject = () => setForm({ ...form, projects: [...form.projects, { title: "", description: "", link: "" }] });
  const updateProject = (i, f, v) => { const u = [...form.projects]; u[i][f] = v; setForm({ ...form, projects: u }); };
  const removeProject = (i) => setForm({ ...form, projects: form.projects.filter((_, idx) => idx !== i) });

  const handleSubmitAndPay = async () => {
    if (!form.full_name || !form.job_title || !form.bio || !form.email) {
      toast.error("Veuillez remplir les champs obligatoires"); setStep(1); return;
    }
    setSubmitting(true);
    try {
      const submitRes = await axios.post(`${API}/portfolio/submit`, { ...form, product_id: productId });
      const payRes = await axios.post(`${API}/portfolio/pay/${submitRes.data.submission_id}`);
      if (payRes.data.checkout_url) window.location.href = payRes.data.checkout_url;
    } catch (err) {
      toast.error(err.response?.data?.detail || "Erreur lors de la soumission"); setSubmitting(false);
    }
  };

  const totalSteps = 5;
  const stepIcons = [User, Briefcase, GraduationCap, Globe, CreditCard];
  const stepLabels = ["Infos", "Experiences", "Formation", "Liens", "Paiement"];

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <User className="w-10 h-10 text-champagne mx-auto mb-4" strokeWidth={1.5} />
              <h2 className="text-xl font-heading font-semibold text-white">Informations Personnelles</h2>
              <p className="text-sm text-zinc-500">Commencez par les bases</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-1">Email *</label>
              <Input type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} placeholder="votre@email.com" className={inputCls} />
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-1">Nom complet *</label>
              <Input value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} placeholder="Jean Kouassi" className={inputCls} />
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-1">Titre professionnel *</label>
              <Input value={form.job_title} onChange={e => setForm({ ...form, job_title: e.target.value })} placeholder="Developpeur Web, Comptable, Designer..." className={inputCls} />
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-1">Bio / Presentation *</label>
              <textarea value={form.bio} onChange={e => setForm({ ...form, bio: e.target.value })} placeholder="Decrivez-vous en quelques phrases..." className={textareaCls} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-1">Telephone</label>
                <Input value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} placeholder="+225 07 00 00 00" className={inputCls} />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-1">Localisation</label>
                <Input value={form.location} onChange={e => setForm({ ...form, location: e.target.value })} placeholder="Abidjan, Cote d'Ivoire" className={inputCls} />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-1">URL de votre photo</label>
              <Input value={form.photo_url} onChange={e => setForm({ ...form, photo_url: e.target.value })} placeholder="https://..." className={inputCls} />
              <p className="text-xs text-zinc-600 mt-1">Lien vers une photo professionnelle</p>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <Briefcase className="w-10 h-10 text-champagne mx-auto mb-4" strokeWidth={1.5} />
              <h2 className="text-xl font-heading font-semibold text-white">Competences & Experiences</h2>
              <p className="text-sm text-zinc-500">Mettez en valeur votre parcours</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-2">Competences</label>
              <div className="flex gap-2 mb-2">
                <Input value={newSkill} onChange={e => setNewSkill(e.target.value)} placeholder="Ex: Excel, Management, Python..." className={`${inputCls} h-10`}
                  onKeyDown={e => { if (e.key === "Enter") { e.preventDefault(); addSkill(); } }} />
                <Button type="button" onClick={addSkill} variant="outline" className="h-10 px-3 border-white/10 text-zinc-300 hover:border-champagne hover:text-champagne">
                  <Plus className="w-4 h-4" strokeWidth={1.5} />
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {form.skills.map((skill, i) => (
                  <span key={i} className="inline-flex items-center gap-1 px-3 py-1 bg-champagne/10 text-champagne text-sm border border-champagne/20">
                    {skill}
                    <button onClick={() => removeSkill(skill)} className="hover:text-red-400 ml-1"><Trash2 className="w-3 h-3" /></button>
                  </span>
                ))}
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-zinc-300">Experiences professionnelles</label>
                <Button type="button" onClick={addExperience} variant="outline" size="sm" className="gap-1 border-white/10 text-zinc-300 hover:border-champagne hover:text-champagne">
                  <Plus className="w-4 h-4" strokeWidth={1.5} /> Ajouter
                </Button>
              </div>
              <div className="space-y-4">
                {form.experiences.map((exp, i) => (
                  <div key={i} className="p-4 border border-white/5 bg-noir relative">
                    <button onClick={() => removeExperience(i)} className="absolute top-2 right-2 text-zinc-500 hover:text-red-400">
                      <Trash2 className="w-4 h-4" />
                    </button>
                    <div className="grid grid-cols-2 gap-3 mb-3">
                      <Input value={exp.company} onChange={e => updateExperience(i, "company", e.target.value)} placeholder="Entreprise" className={`${inputCls} h-10`} />
                      <Input value={exp.role} onChange={e => updateExperience(i, "role", e.target.value)} placeholder="Poste" className={`${inputCls} h-10`} />
                    </div>
                    <Input value={exp.duration} onChange={e => updateExperience(i, "duration", e.target.value)} placeholder="Duree (ex: 2020 - 2023)" className={`${inputCls} h-10 mb-3`} />
                    <textarea value={exp.description} onChange={e => updateExperience(i, "description", e.target.value)} placeholder="Description des responsabilites..."
                      className="w-full px-3 py-2 bg-noir border border-white/10 text-white placeholder:text-zinc-600 focus:ring-1 focus:ring-champagne focus:outline-none text-sm min-h-[80px]" />
                  </div>
                ))}
                {form.experiences.length === 0 && <p className="text-sm text-zinc-600 text-center py-4">Cliquez sur "Ajouter" pour ajouter une experience</p>}
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <GraduationCap className="w-10 h-10 text-champagne mx-auto mb-4" strokeWidth={1.5} />
              <h2 className="text-xl font-heading font-semibold text-white">Formation & Projets</h2>
              <p className="text-sm text-zinc-500">Votre parcours academique et realisations</p>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-zinc-300">Formation</label>
                <Button type="button" onClick={addEducation} variant="outline" size="sm" className="gap-1 border-white/10 text-zinc-300 hover:border-champagne hover:text-champagne">
                  <Plus className="w-4 h-4" strokeWidth={1.5} /> Ajouter
                </Button>
              </div>
              <div className="space-y-3">
                {form.education.map((edu, i) => (
                  <div key={i} className="flex gap-2 items-start">
                    <div className="flex-1 grid grid-cols-3 gap-2">
                      <Input value={edu.school} onChange={e => updateEducation(i, "school", e.target.value)} placeholder="Ecole" className={`${inputCls} h-10`} />
                      <Input value={edu.degree} onChange={e => updateEducation(i, "degree", e.target.value)} placeholder="Diplome" className={`${inputCls} h-10`} />
                      <Input value={edu.year} onChange={e => updateEducation(i, "year", e.target.value)} placeholder="Annee" className={`${inputCls} h-10`} />
                    </div>
                    <button onClick={() => removeEducation(i)} className="p-2 text-zinc-500 hover:text-red-400"><Trash2 className="w-4 h-4" /></button>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-zinc-300">Projets / Realisations</label>
                <Button type="button" onClick={addProject} variant="outline" size="sm" className="gap-1 border-white/10 text-zinc-300 hover:border-champagne hover:text-champagne">
                  <Plus className="w-4 h-4" strokeWidth={1.5} /> Ajouter
                </Button>
              </div>
              <div className="space-y-4">
                {form.projects.map((proj, i) => (
                  <div key={i} className="p-4 border border-white/5 bg-noir relative">
                    <button onClick={() => removeProject(i)} className="absolute top-2 right-2 text-zinc-500 hover:text-red-400"><Trash2 className="w-4 h-4" /></button>
                    <Input value={proj.title} onChange={e => updateProject(i, "title", e.target.value)} placeholder="Titre du projet" className={`${inputCls} h-10 mb-3`} />
                    <textarea value={proj.description} onChange={e => updateProject(i, "description", e.target.value)} placeholder="Description du projet..."
                      className="w-full px-3 py-2 bg-noir border border-white/10 text-white placeholder:text-zinc-600 focus:ring-1 focus:ring-champagne focus:outline-none text-sm min-h-[60px] mb-3" />
                    <Input value={proj.link} onChange={e => updateProject(i, "link", e.target.value)} placeholder="Lien (optionnel)" className={`${inputCls} h-10`} />
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <Globe className="w-10 h-10 text-champagne mx-auto mb-4" strokeWidth={1.5} />
              <h2 className="text-xl font-heading font-semibold text-white">Liens & Reseaux Sociaux</h2>
              <p className="text-sm text-zinc-500">Connectez vos profils (optionnel)</p>
            </div>
            {[
              { label: "LinkedIn", icon: Linkedin, key: "linkedin_url", placeholder: "https://linkedin.com/in/...", color: "text-[#0A66C2]" },
              { label: "Twitter / X", icon: Twitter, key: "twitter_url", placeholder: "https://twitter.com/...", color: "text-zinc-300" },
              { label: "GitHub", icon: Github, key: "github_url", placeholder: "https://github.com/...", color: "text-zinc-300" },
              { label: "Site web personnel", icon: Globe, key: "website_url", placeholder: "https://...", color: "text-champagne" },
            ].map(({ label, icon: Icon, key, placeholder, color }) => (
              <div key={key}>
                <label className="block text-sm font-medium text-zinc-300 mb-1">{label}</label>
                <div className="relative">
                  <Icon className={`absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 ${color}`} strokeWidth={1.5} />
                  <Input value={form[key]} onChange={e => setForm({ ...form, [key]: e.target.value })} placeholder={placeholder} className={`${inputCls} pl-10`} />
                </div>
              </div>
            ))}
          </div>
        );

      case 5:
        return (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <CreditCard className="w-10 h-10 text-champagne mx-auto mb-4" strokeWidth={1.5} />
              <h2 className="text-xl font-heading font-semibold text-white">Recapitulatif & Paiement</h2>
              <p className="text-sm text-zinc-500">Verifiez vos informations et procedez au paiement</p>
            </div>
            <div className="bg-noir border border-white/5 p-6 space-y-4">
              <div className="flex items-start gap-4">
                <User className="w-6 h-6 text-champagne mt-1" strokeWidth={1.5} />
                <div>
                  <p className="font-semibold text-white">{form.full_name || "Non renseigne"}</p>
                  <p className="text-sm text-zinc-400">{form.job_title || "Non renseigne"}</p>
                  <p className="text-sm text-zinc-500">{form.email}</p>
                </div>
              </div>
              {form.skills.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-zinc-300 mb-2">Competences:</p>
                  <div className="flex flex-wrap gap-1">
                    {form.skills.map((s, i) => <span key={i} className="text-xs px-2 py-1 bg-champagne/10 text-champagne border border-champagne/20">{s}</span>)}
                  </div>
                </div>
              )}
              <div className="text-sm text-zinc-500">
                <p>{form.experiences.length} experience(s) | {form.education.length} formation(s) | {form.projects.length} projet(s)</p>
              </div>
            </div>
            {product && (
              <div className="border border-champagne/20 p-6">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="font-heading font-semibold text-white">{product.name}</p>
                    <p className="text-sm text-zinc-500">Creation de portfolio professionnel</p>
                  </div>
                  <p className="text-2xl font-heading font-bold text-champagne">{formatPrice(product.price, product.currency)}</p>
                </div>
              </div>
            )}
            <div className="bg-champagne/10 border border-champagne/20 p-4 text-sm text-champagne flex items-center gap-2">
              <CheckCircle className="w-5 h-5 flex-shrink-0" strokeWidth={1.5} />
              Apres paiement, notre equipe creera votre portfolio sous 48-72h
            </div>
          </div>
        );

      default: return null;
    }
  };

  return (
    <main className="min-h-screen bg-noir py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-heading font-semibold text-white">Creation de Portfolio</h1>
          {product && <p className="text-sm text-zinc-500">{product.name}</p>}
        </div>

        {/* Progress */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-3">
            {[1, 2, 3, 4, 5].map((s) => {
              const Icon = stepIcons[s - 1];
              return (
                <div key={s} className={`w-10 h-10 flex items-center justify-center transition-colors ${
                  s <= step ? "bg-champagne text-noir" : "bg-surface border border-white/10 text-zinc-600"
                }`}>
                  <Icon className="w-4 h-4" strokeWidth={1.5} />
                </div>
              );
            })}
          </div>
          <div className="h-0.5 bg-white/5">
            <div className="h-full bg-champagne transition-all duration-500" style={{ width: `${(step / totalSteps) * 100}%` }} />
          </div>
          <div className="flex justify-between mt-1.5 text-xs text-zinc-600">
            {stepLabels.map((l, i) => <span key={i} className={step >= i + 1 ? "text-champagne" : ""}>{l}</span>)}
          </div>
        </div>

        {/* Form Card */}
        <div className="bg-surface border border-white/5 p-8">
          {renderStep()}

          <div className="flex gap-4 mt-8 pt-6 border-t border-white/5">
            {step > 1 && (
              <Button type="button" variant="outline" onClick={() => setStep(step - 1)}
                className="flex-1 h-12 border-white/10 text-zinc-300 hover:border-champagne hover:text-champagne">
                Precedent
              </Button>
            )}
            {step < totalSteps ? (
              <Button type="button" onClick={() => setStep(step + 1)} className="flex-1 h-12 btn-gold">
                Suivant
              </Button>
            ) : (
              <Button type="button" onClick={handleSubmitAndPay} disabled={submitting} className="flex-1 h-14 btn-gold text-base">
                {submitting ? <Loader2 className="w-5 h-5 animate-spin" /> : (
                  <>
                    <CreditCard className="w-5 h-5 mr-2" strokeWidth={1.5} />
                    Payer {product ? formatPrice(product.price, product.currency) : ""}
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
