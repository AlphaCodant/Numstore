"""
Routes missions, inventaires IVT et agents.
"""
import logging
import base64

from fastapi import APIRouter, Request, Depends, Body
from fastapi.responses import JSONResponse

from database import get_db
from auth import require_auth

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/agents")
async def get_agents(db=Depends(get_db)):
    rows = await db.fetch("SELECT * FROM agent ORDER BY nom_prenoms ASC")
    return [dict(r) for r in rows]


@router.get("/mission")
async def get_missions(db=Depends(get_db)):
    rows = await db.fetch("SELECT * FROM cout_variable ORDER BY date_debut DESC")
    if not rows:
        return JSONResponse({"message": "Aucune mission trouvée."}, status_code=404)
    return [dict(r) for r in rows]


@router.get("/inventaire")
async def get_inventaires(db=Depends(get_db)):
    rows = await db.fetch("SELECT * FROM dossier_ivt ORDER BY date_reception DESC")
    if not rows:
        return JSONResponse({"message": "Aucun inventaire trouvé."}, status_code=404)
    return [dict(r) for r in rows]


@router.post("/api/planifier_mission")
async def planifier_mission(body: dict = Body({}), db=Depends(get_db)):
    md      = body.get("missionData", {})
    agents  = body.get("agentsSelectionnes", [])
    parcels = body.get("parcellesSelectionnees", [])

    row = await db.fetchrow(
        """INSERT INTO cout_variable
           (libele,nb_jour,nb_homme,cout,date_debut,date_fin,document,
            id_agent,parcelle,nb_agent,nb_parcelle,statut)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,'false')
           RETURNING id""",
        md.get("libele"), md.get("nb_jour"), md.get("nb_agent"),
        md.get("cout"), md.get("date_debut"), md.get("date_fin"),
        md.get("document_mission"),
        ", ".join(str(a) for a in agents),
        ", ".join(str(p) for p in parcels),
        len(agents), len(parcels),
    )
    return JSONResponse({"message": "Plan de mission créé.", "id": row["id"]}, status_code=201)


@router.post("/api/valider_mission")
async def valider_mission(body: dict = Body({}), db=Depends(get_db)):
    agents  = body.get("agentsSelectionnes", [])
    parcels = body.get("parcellesSelectionnees", [])
    nb_parc = len(parcels)

    cv = await db.fetchrow(
        "SELECT id,id_agent,cout,document,libele,date_debut,date_fin,parcelle "
        "FROM cout_variable ORDER BY id DESC LIMIT 1"
    )
    if not cv:
        return JSONResponse({"message": "Aucun cout variable trouvé."}, status_code=404)

    cout_par_parcelle = float(cv["cout"]) / nb_parc if nb_parc else 0
    result_id  = cv["id"]
    id_agent   = cv["id_agent"]

    last_act = await db.fetchrow("SELECT id FROM activite ORDER BY id DESC LIMIT 1")
    next_id  = (last_act["id"] + 1) if last_act else 1

    parc_nums = await db.fetch(
        f"SELECT TRIM(p) AS numero FROM unnest(string_to_array("
        f"(SELECT parcelle FROM cout_variable WHERE id={result_id}), ',')) AS p"
    )

    for i, prow in enumerate(parc_nums):
        parc = await db.fetchrow(
            "SELECT id, superficie FROM parcelles WHERE numero=$1 LIMIT 1", prow["numero"]
        )
        if not parc:
            continue
        agent_row = await db.fetchrow(
            f"SELECT nom_prenoms FROM agent WHERE id IN ({id_agent}) LIMIT 1"
        )
        operateur = agent_row["nom_prenoms"] if agent_row else ""

        await db.execute(
            """INSERT INTO activite
               (id,libele,data_debut,date_fin,date_enreg,"date reception",
                sup_traitee,operateur,cout_fixe,cout_variable,parcelle,
                document,annee_exercice,id_mission)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)""",
            next_id + i, cv["libele"], cv["date_debut"], cv["date_fin"],
            cv["date_fin"], cv["date_fin"],
            float(parc["superficie"]) if parc["superficie"] else 0,
            operateur, 0, cout_par_parcelle, parc["id"],
            cv["document"] or "Document", 2025, result_id,
        )

    return JSONResponse(dict(cv), status_code=200)


@router.post("/api/dossier_ivt")
async def create_dossier_ivt(body: dict = Body({}), db=Depends(get_db)):
    md      = body.get("missionData", {})
    parcels = body.get("parcellesSelectionnees", [])
    cf      = body.get("contenuFichier", {})

    contenu_buffer = None
    if cf.get("contenuFc"):
        contenu_buffer = base64.b64decode(cf["contenuFc"])

    row = await db.fetchrow(
        """INSERT INTO dossier_ivt
           (num_courrier,date_demande,nom_demandeur,foret,type_inventaire,
            date_reception,nom_courier,type_fichier,contenu,parcelles,nb_parcelle)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
           RETURNING id""",
        md.get("ref"), md.get("date_demande"), md.get("demandeur"),
        md.get("foret"), md.get("type"), md.get("date_reception"),
        cf.get("nom"), cf.get("typeFichier"), contenu_buffer,
        ", ".join(str(p) for p in parcels), len(parcels),
    )
    return JSONResponse({"message": "Dossier créé.", "id": row["id"]}, status_code=201)


@router.post("/api/valider_ivt")
async def valider_ivt(body: dict = Body({}), db=Depends(get_db)):
    parcels = body.get("parcellesSelectionnees", [])

    dossier = await db.fetchrow(
        "SELECT * FROM dossier_ivt ORDER BY id DESC LIMIT 1"
    )
    if not dossier:
        return JSONResponse({"message": "Aucun dossier IVT trouvé."}, status_code=404)

    last_parc = await db.fetchrow("SELECT id FROM parcelle_ivt ORDER BY id DESC LIMIT 1")
    next_id   = (last_parc["id"] + 1) if last_parc else 1

    for i, parcelle in enumerate(parcels):
        await db.execute(
            """INSERT INTO parcelle_ivt
               (id,demandeur,data_demande,date_reception,foret,
                type_ivt,ref_ivt,num_parcelle,id_dossier_ivt)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)""",
            next_id + i,
            dossier["nom_demandeur"], dossier["date_demande"],
            dossier["date_reception"], dossier["foret"],
            dossier["type_inventaire"], dossier["nom_courier"],
            parcelle, dossier["id"],
        )

    return JSONResponse({
        "message": "Validation réussie.",
        "id_dossier": dossier["id"],
        "nb_parcelles_inserees": len(parcels),
    }, status_code=200)
