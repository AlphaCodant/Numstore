"""
Routes qui rendent des pages HTML (équivalent res.render() Express).
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from database import get_db
from auth import get_current_user, require_auth

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
#  Helpers                                                                     #
# --------------------------------------------------------------------------- #

def _membres_stats(rows: list) -> dict:
    """Calcule les stats membres : total, superficie, essence/partenaire dominants."""
    total = len(rows)
    superficie_totale = sum(float(r.get("superficie") or 0) for r in rows)

    essence_count: dict = {}
    for r in rows:
        e = r.get("essence") or ""
        essence_count[e] = essence_count.get(e, 0) + 1
    predominant_essence = max(essence_count, key=lambda k: essence_count[k], default="")
    occurance = essence_count.get(predominant_essence, 0)

    partenaire_count: dict = {}
    for r in rows:
        p = r.get("partenaire") or ""
        partenaire_count[p] = partenaire_count.get(p, 0) + 1
    predominant_partenaire = max(partenaire_count, key=lambda k: partenaire_count[k], default="")

    return {
        "totalMembres": total,
        "superficieTotale": round(superficie_totale),
        "predominantEssence": predominant_essence,
        "occurance": occurance,
        "predominantPartenaire": predominant_partenaire,
    }


# --------------------------------------------------------------------------- #
#  Pages publiques                                                              #
# --------------------------------------------------------------------------- #

@router.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse("/accueil", status_code=302)


@router.get("/accueil", response_class=HTMLResponse)
async def page_accueil(request: Request):
    return templates.TemplateResponse("accueil.html", {"request": request})


@router.get("/presentation", response_class=HTMLResponse)
async def page_presentation(request: Request):
    return templates.TemplateResponse("presentation.html", {"request": request})


# --------------------------------------------------------------------------- #
#  Pages admin publiques (sans auth — comme dans le JS original)               #
# --------------------------------------------------------------------------- #

@router.get("/admin/inscrit", response_class=HTMLResponse)
async def admin_inscrit(request: Request):
    return templates.TemplateResponse("admin_inscrit.html", {"request": request})


@router.get("/admin/membre", response_class=HTMLResponse)
async def admin_membre(request: Request):
    return templates.TemplateResponse("admin_membre.html", {"request": request})


@router.get("/admin/connecte", response_class=HTMLResponse)
async def admin_connecte(request: Request):
    return templates.TemplateResponse("admin_connecte.html", {"request": request})


@router.get("/admin/demande", response_class=HTMLResponse)
async def admin_demande(request: Request):
    return templates.TemplateResponse("admin_demande.html", {"request": request})


@router.get("/admin/{id}", response_class=HTMLResponse)
async def admin_dashboard(request: Request, id: str, db=Depends(get_db)):
    user = require_auth(request)
    token_y = user.get("tokenY")

    inscrit = await db.fetchval("SELECT COUNT(*) FROM utilisateur")
    membre = await db.fetchval("SELECT COUNT(*) FROM utilisateur WHERE statut LIKE 'valide'")
    attente = await db.fetchval("SELECT COUNT(*) FROM utilisateur WHERE statut LIKE 'attente'")
    connecte = await db.fetchval("SELECT COUNT(*) FROM utilisateurs WHERE etat LIKE 'connecte'")

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "id": token_y,
        "inscrit": inscrit,
        "membre": membre,
        "attente": attente,
        "connecte": connecte,
    })


# --------------------------------------------------------------------------- #
#  Pages protégées simples                                                      #
# --------------------------------------------------------------------------- #

@router.get("/stats", response_class=HTMLResponse)
async def page_stats(request: Request):
    require_auth(request)
    return templates.TemplateResponse("stats.html", {"request": request})


@router.get("/fiche", response_class=HTMLResponse)
async def page_fiche(request: Request):
    require_auth(request)
    return templates.TemplateResponse("table.html", {"request": request})


@router.get("/fiche2", response_class=HTMLResponse)
async def page_fiche2(request: Request):
    require_auth(request)
    return templates.TemplateResponse("tableau.html", {"request": request})


@router.get("/devis", response_class=HTMLResponse)
async def page_devis_redirect(request: Request):
    user = require_auth(request)
    return RedirectResponse(f"/devis/{user['tokenY']}", status_code=302)


@router.get("/devis/{id}", response_class=HTMLResponse)
async def page_devis(request: Request, id: str):
    user = require_auth(request)
    return templates.TemplateResponse("tableau.html", {"request": request, "id": user["tokenY"]})


@router.get("/statistiques", response_class=HTMLResponse)
async def page_statistiques_redirect(request: Request):
    user = require_auth(request)
    return RedirectResponse(f"/statistiques/{user['tokenY']}", status_code=302)


@router.get("/statistiques/{id}", response_class=HTMLResponse)
async def page_statistiques(request: Request, id: str):
    user = require_auth(request)
    return templates.TemplateResponse("ch_stats.html", {"request": request, "id": user["tokenY"]})


# --------------------------------------------------------------------------- #
#  Page membre / mise_en_place                                                  #
# --------------------------------------------------------------------------- #

@router.get("/membres", response_class=HTMLResponse)
async def page_membres(request: Request, db=Depends(get_db)):
    rows = await db.fetch(
        """SELECT a.id, b.foret AS foret, a.annee, a.numero, a.essence,
                  a.densite, a.partenaire, a.longitude AS x, a.latitude AS y,
                  a.superficie
           FROM parcelles AS a
           JOIN foret AS b ON a.foret = b.id
           ORDER BY a.numero ASC"""
    )
    membres = [dict(r) for r in rows]
    stats = _membres_stats(membres)
    return templates.TemplateResponse("membre.html", {
        "request": request,
        "membre": membres,
        **stats,
    })


@router.get("/mise_en_place/{id}", response_class=HTMLResponse)
async def page_mise_en_place(request: Request, id: str, db=Depends(get_db)):
    rows = await db.fetch(
        """SELECT a.id, b.foret AS foret, a.annee, a.numero, a.essence,
                  a.densite, a.partenaire, a.longitude AS x, a.latitude AS y,
                  a.superficie
           FROM parcelles AS a
           JOIN foret AS b ON a.foret = b.id
           ORDER BY a.numero ASC"""
    )
    membres = [dict(r) for r in rows]
    stats = _membres_stats(membres)
    return templates.TemplateResponse("membre_mise.html", {
        "request": request,
        "id": id,
        "membre": membres,
        **stats,
    })


# --------------------------------------------------------------------------- #
#  Page principale dashboard                                                   #
# --------------------------------------------------------------------------- #

@router.get("/page/{id}", response_class=HTMLResponse)
async def page_dashboard(request: Request, id: str, db=Depends(get_db)):
    user = require_auth(request)
    fonction = {
        "sangoue": 2, "tene": 1, "cg": 3, "csotc": 4,
        "agent_sotc": 5, "agent_tene": 6, "agent_sangoue": 7, "autre_sodefor": 8,
    }
    row = await db.fetchrow(
        "SELECT ugf FROM utilisateurs WHERE email = $1", user["email"]
    )
    ugf_val = row["ugf"] if row else user.get("ugf", "")
    poste = fonction.get(ugf_val, 0)

    return templates.TemplateResponse("dashboard_conn.html", {
        "request": request,
        "id": user["tokenY"],
        "ugf": user.get("ugf"),
        "admin": user.get("admin"),
        "poste": poste,
    })


@router.post("/page/init/{id}")
async def page_init(request: Request, id: str):
    return RedirectResponse(f"/page/{id}", status_code=302)


# --------------------------------------------------------------------------- #
#  Entretien / Sylviculture / Missions — pages HTML                             #
# --------------------------------------------------------------------------- #

@router.get("/entretien_p/{id}", response_class=HTMLResponse)
async def page_entretien(request: Request, id: str):
    return templates.TemplateResponse("membre_entretien.html", {"request": request, "id": id})


@router.get("/sylviculture/{id}", response_class=HTMLResponse)
async def page_sylviculture(request: Request, id: str):
    require_auth(request)
    return templates.TemplateResponse("membre_sylviculture.html", {"request": request, "id": id})


@router.get("/plan_mission/{id}", response_class=HTMLResponse)
async def page_plan_mission(request: Request, id: str):
    return templates.TemplateResponse("plan_mission.html", {"request": request, "id": id})


@router.get("/confirm_mission", response_class=HTMLResponse)
async def page_confirm_mission(request: Request):
    return templates.TemplateResponse("confirm_mission.html", {"request": request})


@router.get("/confirm_ivt/{id}", response_class=HTMLResponse)
async def page_confirm_ivt(request: Request, id: str):
    return templates.TemplateResponse("confirm_inventaire.html", {"request": request, "id": id})


@router.get("/inventaire/dossier/{id}", response_class=HTMLResponse)
async def page_dossier_ivt(request: Request, id: str):
    require_auth(request)
    return templates.TemplateResponse("dossier_ivt.html", {"request": request, "id": id})


@router.get("/api/dossier/{id}", response_class=HTMLResponse)
async def page_inventaire_dossier(request: Request, id: str):
    require_auth(request)
    return templates.TemplateResponse("inventaire_dossier.html", {"request": request, "id": id})


# --------------------------------------------------------------------------- #
#  CUGF (Cellule UGF) — pages HTML                                             #
# --------------------------------------------------------------------------- #

@router.get("/api/cugf/{foret}", response_class=HTMLResponse)
async def page_cugf(request: Request, foret: str):
    user = require_auth(request)
    return templates.TemplateResponse("interface_cugf.html", {
        "request": request,
        "foret": foret,
        "id": user["tokenY"],
    })


@router.get("/api/cugf/mise_en_place/{foret}", response_class=HTMLResponse)
async def page_cugf_mise_en_place(request: Request, foret: str, db=Depends(get_db)):
    require_auth(request)
    return templates.TemplateResponse("mise_en_place.html", {"request": request, "foret": foret})


@router.get("/api/cugf/mise_en_place/{foret}/{travail}/{nom}", response_class=HTMLResponse)
async def page_cugf_mise_en_place_detail(request: Request, foret: str, travail: str, nom: str):
    require_auth(request)
    return templates.TemplateResponse("mise_en_place_parc.html", {
        "request": request,
        "travail": travail,
        "foret": foret,
        "nom": nom.upper(),
    })


@router.get("/api/cugf/entretien/{annee}/{foret}", response_class=HTMLResponse)
async def page_cugf_entretien(request: Request, annee: str, foret: str):
    require_auth(request)
    return templates.TemplateResponse("entretien.html", {
        "request": request, "foret": foret, "annee": annee,
    })


@router.get("/api/cugf/entretien_1/{annee}/{foret}", response_class=HTMLResponse)
async def page_cugf_entretien_1(request: Request, annee: str, foret: str):
    require_auth(request)
    return templates.TemplateResponse("entretien_1.html", {
        "request": request, "foret": foret, "annee": annee,
    })


@router.get("/api/cugf/entretien_2/{annee}/{foret}", response_class=HTMLResponse)
async def page_cugf_entretien_2(request: Request, annee: str, foret: str):
    require_auth(request)
    return templates.TemplateResponse("entretien_2.html", {
        "request": request, "foret": foret, "annee": annee,
    })


@router.get("/api/cugf/entretien_3/{annee}/{foret}", response_class=HTMLResponse)
async def page_cugf_entretien_3(request: Request, annee: str, foret: str):
    require_auth(request)
    return templates.TemplateResponse("entretien_3.html", {
        "request": request, "foret": foret, "annee": annee,
    })


@router.get("/api/cugf/entretien_recap/{foret}", response_class=HTMLResponse)
async def page_cugf_entretien_recap(request: Request, foret: str):
    require_auth(request)
    return templates.TemplateResponse("entretien_recap.html", {"request": request, "foret": foret})


@router.get("/api/cugf/entretien/{annee}/{foret}/{travail}", response_class=HTMLResponse)
@router.get("/api/cugf/entretien_1/{annee}/{foret}/{travail}", response_class=HTMLResponse)
@router.get("/api/cugf/entretien_2/{annee}/{foret}/{travail}", response_class=HTMLResponse)
@router.get("/api/cugf/entretien_3/{annee}/{foret}/{travail}", response_class=HTMLResponse)
async def page_cugf_entretien_detail(request: Request, annee: str, foret: str, travail: str):
    require_auth(request)
    return templates.TemplateResponse("entretien_parc.html", {
        "request": request, "foret": foret, "annee": annee, "travail": travail,
    })


# --------------------------------------------------------------------------- #
#  Supervision gestionnaire                                                     #
# --------------------------------------------------------------------------- #

@router.get("/api/gest/{admin}", response_class=HTMLResponse)
async def page_gest(request: Request, admin: str):
    user = require_auth(request)
    return templates.TemplateResponse("dashboard_gest.html", {
        "request": request,
        "foret": admin,
        "id": user["tokenY"],
    })


@router.get("/api/gest/{admin}/mise_en_place", response_class=HTMLResponse)
async def page_gest_mise_en_place(request: Request, admin: str):
    return templates.TemplateResponse("dash_mise_en_place.html", {
        "request": request, "foret": admin,
    })
