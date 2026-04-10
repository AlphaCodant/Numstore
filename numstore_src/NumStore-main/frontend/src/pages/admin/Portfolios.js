import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { ArrowLeft, Loader2, Eye, CheckCircle, Clock, Hourglass, Link as LinkIcon, User, Briefcase } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../../components/ui/dialog";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const statusConfig = {
  pending: { label: "En attente", color: "text-amber-400", bg: "bg-amber-500/10", icon: Clock },
  in_progress: { label: "En cours", color: "text-champagne", bg: "bg-champagne/10", icon: Hourglass },
  completed: { label: "Termine", color: "text-emerald-400", bg: "bg-emerald-500/10", icon: CheckCircle }
};

export default function AdminPortfolios() {
  const navigate = useNavigate();
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSubmission, setSelectedSubmission] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [portfolioUrl, setPortfolioUrl] = useState("");
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem("admin_auth")) { navigate("/admin"); return; }
    fetchSubmissions();
  }, []);

  const fetchSubmissions = async () => {
    try { const res = await axios.get(`${API}/admin/portfolio-submissions`); setSubmissions(res.data); }
    catch (err) { console.error("Error:", err); }
    finally { setLoading(false); }
  };

  const openDetail = (sub) => { setSelectedSubmission(sub); setPortfolioUrl(sub.portfolio_url || ""); setDialogOpen(true); };

  const updateStatus = async (newStatus) => {
    if (!selectedSubmission) return;
    if (newStatus === "completed" && !portfolioUrl.trim()) { toast.error("Veuillez entrer l'URL du portfolio"); return; }
    setUpdating(true);
    try {
      const url = `${API}/admin/portfolio-submissions/${selectedSubmission.id}?status=${newStatus}${portfolioUrl ? `&portfolio_url=${encodeURIComponent(portfolioUrl)}` : ""}`;
      await axios.put(url);
      toast.success("Statut mis a jour"); setDialogOpen(false); fetchSubmissions();
    } catch { toast.error("Erreur lors de la mise a jour"); }
    finally { setUpdating(false); }
  };

  if (loading) return <main className="min-h-screen bg-noir flex items-center justify-center"><Loader2 className="w-8 h-8 text-champagne animate-spin" /></main>;

  return (
    <main className="min-h-screen bg-noir" data-testid="admin-portfolios">
      <div className="max-w-6xl mx-auto px-6 lg:px-12 py-8">
        <div className="flex items-center gap-4 mb-8">
          <button onClick={() => navigate("/admin/dashboard")} className="p-2 text-zinc-500 hover:text-champagne transition-colors">
            <ArrowLeft className="w-5 h-5" strokeWidth={1.5} />
          </button>
          <div>
            <h1 className="text-3xl font-heading font-semibold text-white">Demandes de Portfolio</h1>
            <p className="text-zinc-500 text-sm">{submissions.length} demande(s)</p>
          </div>
        </div>

        <div className="bg-surface border border-white/5">
          {submissions.length === 0 ? (
            <div className="p-12 text-center text-zinc-600">Aucune demande de portfolio pour le moment.</div>
          ) : (
            <div className="divide-y divide-white/5">
              {submissions.map(sub => {
                const status = statusConfig[sub.status] || statusConfig.pending;
                const StatusIcon = status.icon;
                return (
                  <div key={sub.id} className="flex items-center gap-4 p-4 hover:bg-white/[0.02] cursor-pointer" onClick={() => openDetail(sub)} data-testid={`submission-${sub.id}`}>
                    <div className="w-10 h-10 bg-champagne/10 flex items-center justify-center">
                      <User className="w-5 h-5 text-champagne" strokeWidth={1.5} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-white text-sm">{sub.full_name}</p>
                      <p className="text-xs text-zinc-500 truncate">{sub.job_title}</p>
                      <p className="text-xs text-zinc-600">{sub.email}</p>
                    </div>
                    <div className="text-right">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium ${status.bg} ${status.color}`}>
                        <StatusIcon className="w-3 h-3" strokeWidth={1.5} /> {status.label}
                      </span>
                      <p className="text-xs text-zinc-600 mt-1">{new Date(sub.created_at).toLocaleDateString("fr-FR")}</p>
                    </div>
                    <Eye className="w-4 h-4 text-zinc-600" strokeWidth={1.5} />
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto bg-surface border-white/10 text-white">
          <DialogHeader><DialogTitle className="font-heading text-xl">Details de la demande</DialogTitle></DialogHeader>
          {selectedSubmission && (
            <div className="space-y-6 mt-4">
              <div className="bg-noir border border-white/5 p-4">
                <div className="flex items-center gap-4 mb-4">
                  {selectedSubmission.photo_url ? (
                    <img src={selectedSubmission.photo_url} alt={selectedSubmission.full_name} className="w-14 h-14 object-cover rounded-full border border-white/10" />
                  ) : (
                    <div className="w-14 h-14 bg-champagne/10 flex items-center justify-center rounded-full"><User className="w-7 h-7 text-champagne" strokeWidth={1.5} /></div>
                  )}
                  <div>
                    <h3 className="text-lg font-semibold text-white">{selectedSubmission.full_name}</h3>
                    <p className="text-champagne text-sm">{selectedSubmission.job_title}</p>
                  </div>
                </div>
                <p className="text-sm text-zinc-400">{selectedSubmission.bio}</p>
                <div className="mt-3 flex gap-4 text-xs text-zinc-500">
                  {selectedSubmission.phone && <span>Tel: {selectedSubmission.phone}</span>}
                  {selectedSubmission.location && <span>Loc: {selectedSubmission.location}</span>}
                </div>
              </div>

              {selectedSubmission.skills?.length > 0 && (
                <div>
                  <h4 className="font-semibold text-sm text-zinc-300 mb-2">Competences</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedSubmission.skills.map((skill, i) => <span key={i} className="px-2 py-1 bg-champagne/10 text-champagne text-xs border border-champagne/20">{skill}</span>)}
                  </div>
                </div>
              )}

              {selectedSubmission.experiences?.length > 0 && (
                <div>
                  <h4 className="font-semibold text-sm text-zinc-300 mb-2">Experiences</h4>
                  <div className="space-y-3">
                    {selectedSubmission.experiences.map((exp, i) => (
                      <div key={i} className="border-l-2 border-champagne/30 pl-3">
                        <p className="font-medium text-sm text-white">{exp.role}</p>
                        <p className="text-xs text-zinc-500">{exp.company} | {exp.duration}</p>
                        <p className="text-xs text-zinc-400 mt-1">{exp.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedSubmission.education?.length > 0 && (
                <div>
                  <h4 className="font-semibold text-sm text-zinc-300 mb-2">Formation</h4>
                  {selectedSubmission.education.map((edu, i) => (
                    <div key={i} className="flex justify-between text-xs text-zinc-400"><span>{edu.degree} - {edu.school}</span><span>{edu.year}</span></div>
                  ))}
                </div>
              )}

              {selectedSubmission.projects?.length > 0 && (
                <div>
                  <h4 className="font-semibold text-sm text-zinc-300 mb-2">Projets</h4>
                  {selectedSubmission.projects.map((proj, i) => (
                    <div key={i} className="text-xs mb-2">
                      <p className="font-medium text-white">{proj.title}</p>
                      <p className="text-zinc-500">{proj.description}</p>
                      {proj.link && <a href={proj.link} target="_blank" rel="noopener noreferrer" className="text-champagne hover:underline">{proj.link}</a>}
                    </div>
                  ))}
                </div>
              )}

              <div className="flex flex-wrap gap-3 text-xs">
                {selectedSubmission.linkedin_url && <a href={selectedSubmission.linkedin_url} target="_blank" className="text-[#0A66C2] hover:underline">LinkedIn</a>}
                {selectedSubmission.twitter_url && <a href={selectedSubmission.twitter_url} target="_blank" className="text-zinc-300 hover:underline">Twitter</a>}
                {selectedSubmission.github_url && <a href={selectedSubmission.github_url} target="_blank" className="text-zinc-300 hover:underline">GitHub</a>}
                {selectedSubmission.website_url && <a href={selectedSubmission.website_url} target="_blank" className="text-champagne hover:underline">Site web</a>}
              </div>

              <div className="border-t border-white/5 pt-4">
                <h4 className="font-semibold text-sm text-zinc-300 mb-3">Mettre a jour le statut</h4>
                {selectedSubmission.status !== "completed" && (
                  <div className="mb-4">
                    <label className="block text-xs font-medium text-zinc-400 mb-1">URL du portfolio cree</label>
                    <div className="relative">
                      <LinkIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" strokeWidth={1.5} />
                      <Input value={portfolioUrl} onChange={e => setPortfolioUrl(e.target.value)} placeholder="https://portfolio-client.com"
                        className="h-10 pl-10 bg-noir border-white/10 text-white placeholder:text-zinc-600 focus:ring-champagne" />
                    </div>
                  </div>
                )}
                <div className="flex gap-2">
                  {selectedSubmission.status === "pending" && (
                    <Button onClick={() => updateStatus("in_progress")} disabled={updating} variant="outline" className="flex-1 border-white/10 text-zinc-300 hover:border-champagne hover:text-champagne text-sm">
                      {updating ? <Loader2 className="w-4 h-4 animate-spin" /> : "Marquer en cours"}
                    </Button>
                  )}
                  {selectedSubmission.status !== "completed" && (
                    <Button onClick={() => updateStatus("completed")} disabled={updating} className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white text-sm">
                      {updating ? <Loader2 className="w-4 h-4 animate-spin" /> : "Marquer termine"}
                    </Button>
                  )}
                </div>
                {selectedSubmission.portfolio_url && (
                  <div className="mt-4 p-3 bg-emerald-500/10 border border-emerald-500/20 text-xs">
                    <p className="font-medium text-emerald-400">Portfolio livre:</p>
                    <a href={selectedSubmission.portfolio_url} target="_blank" className="text-champagne hover:underline">{selectedSubmission.portfolio_url}</a>
                  </div>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </main>
  );
}
