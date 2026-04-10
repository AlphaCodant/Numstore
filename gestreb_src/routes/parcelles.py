"""
Routes API parcelles : GET/POST données, mise en place, entretien, graphiques.
"""
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Request, Depends, Body
from fastapi.responses import JSONResponse

from database import get_db
from auth import require_auth

router = APIRouter()
logger = logging.getLogger(__name__)
current_year = datetime.now().year


# ─────────────────────────────────────────────────────────────────────────────
#  Parcelles
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/api/parcelles")
async def get_parcelles(db=Depends(get_db)):
    rows = await db.fetch(
        """SELECT a.id, a.annee, a.numero, a.essence, a.superficie, b.foret
           FROM parcelles AS a
           INNER JOIN foret AS b ON a.foret = b.id
           ORDER BY a.annee ASC, a.numero ASC"""
    )
    return [dict(r) for r in rows]


@router.get("/api/parcelles/{id}")
async def get_parcelle(id: str, db=Depends(get_db)):
    row = await db.fetchrow("SELECT * FROM parcelles WHERE id = $1", int(id))
    if not row:
        return JSONResponse({"message": "Non trouvé"}, status_code=404)
    return dict(row)


@router.post("/api/parcelles/{id}")
async def post_parcelles_liste(id: str, db=Depends(get_db)):
    rows = await db.fetch("SELECT * FROM parcelles ORDER BY annee ASC")
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
#  Mise en place — GET résumé et détail
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/get/parcelles/mise_en_place/{foret}/{travail}")
async def get_mise_en_place_detail(foret: str, travail: str, db=Depends(get_db)):
    rows = await db.fetch(
        f"""SELECT a.id, a.numero, a.annee, a.essence, a.superficie,
                   b.superficie_traitee,
                   TO_CHAR(b.date_init, 'dd/mm/yyyy') AS date_init,
                   TO_CHAR(b.date_fin, 'dd/mm/yyyy') AS date_fin
            FROM parcelles AS a, appliquer AS b
            WHERE a.id = b.fk_parcelles
              AND a.foret = {int(foret)}
              AND a.annee = {current_year}
              AND b.fk_cout_fixe = {int(travail)}
            ORDER BY id ASC"""
    )
    return [dict(r) for r in rows]


@router.post("/get/parcelles/mise_en_place/{foret}/{travail}")
async def post_mise_en_place_update(
    foret: str, travail: str,
    body: dict = Body({}),
    db=Depends(get_db),
):
    realise    = body.get("realise")
    date_debut = body.get("date_debut")
    date_fin   = body.get("date_fin")

    async def _update(items, field, cast=None):
        if not items:
            return
        for item in items:
            if not item.get("id") or item.get("value") in (None, ""):
                continue
            val = cast(item["value"]) if cast else item["value"]
            await db.execute(
                f"UPDATE appliquer SET {field} = $1 WHERE fk_parcelles = $2 AND fk_cout_fixe = $3",
                val, int(item["id"]), int(travail),
            )

    await _update(date_debut, "date_init")
    await _update(realise, "superficie_traitee", float)
    await _update(date_fin, "date_fin")
    return JSONResponse("Mise à jour réussie", status_code=200)


@router.get("/get/parcelles/mise_en_place/{foret}")
async def get_mise_en_place_foret(foret: str, db=Depends(get_db)):
    rows = await db.fetch(
        f"""SELECT a.fk_cout_fixe AS travail,
                   SUM(b.superficie) AS objectif,
                   SUM(a.superficie_traitee) AS realise
            FROM appliquer AS a, parcelles AS b
            WHERE a.fk_parcelles = b.id
              AND fk_cout_fixe BETWEEN 1 AND 7
              AND b.foret = {int(foret)}
              AND annee = {current_year}
            GROUP BY a.fk_cout_fixe
            ORDER BY a.fk_cout_fixe ASC"""
    )
    return [dict(r) for r in rows]


@router.post("/get/parcelles/mise_en_place/{foret}")
async def post_mise_en_place_resultats(foret: str, db=Depends(get_db)):
    f = int(foret)
    await db.execute(
        f"""UPDATE resultats SET (objectif, realise) = (
            (SELECT SUM(superficie) FROM parcelles WHERE foret={f} AND annee={current_year}),
            (SELECT SUM(a.superficie_traitee/7) FROM appliquer AS a, parcelles AS b
             WHERE a.fk_parcelles=b.id
               AND a.fk_cout_fixe IN (SELECT id FROM cout_fixe WHERE fk_resultat=1)
               AND b.foret={f} AND b.annee={current_year})
        ) WHERE id = 1"""
    )
    return JSONResponse("OK")


# ─────────────────────────────────────────────────────────────────────────────
#  Entretien — GET résultats par activité
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/get/parcelles/entretien0/{foret}")
async def get_entretien0(foret: str, db=Depends(get_db)):
    rows = await db.fetch(
        f"SELECT * FROM resultats WHERE fk_activite=2 AND annee={current_year} AND fk_foret={int(foret)}"
    )
    return [dict(r) for r in rows]


@router.get("/get/parcelles/entretien1/{foret}")
async def get_entretien1(foret: str, db=Depends(get_db)):
    rows = await db.fetch(
        f"SELECT * FROM resultats WHERE fk_activite=3 AND annee={current_year-1} AND fk_foret={int(foret)}"
    )
    return [dict(r) for r in rows]


@router.get("/get/parcelles/entretien2/{foret}")
async def get_entretien2(foret: str, db=Depends(get_db)):
    rows = await db.fetch(
        f"SELECT * FROM resultats WHERE fk_activite=4 AND annee={current_year-2} AND fk_foret={int(foret)}"
    )
    return [dict(r) for r in rows]


@router.get("/get/parcelles/entretien3/{foret}")
async def get_entretien3(foret: str, db=Depends(get_db)):
    rows = await db.fetch(
        f"SELECT * FROM resultats WHERE fk_activite=5 AND annee={current_year-3} AND fk_foret={int(foret)}"
    )
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
#  Entretien — POST UPDATE resultats
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/get/parcelles/entretien0/{foret}")
async def post_entretien0(foret: str, db=Depends(get_db)):
    f, a = int(foret), current_year
    await db.execute(
        f"""UPDATE resultats SET (objectif, realise) = (
            (SELECT SUM(superficie) FROM parcelles WHERE foret={f} AND annee={a}) * 2,
            (SELECT passage_1+passage_2 FROM (SELECT DISTINCT
                (SELECT SUM(a.superficie_traitee)/3.2 FROM appliquer a, parcelles b
                 WHERE a.fk_parcelles=b.id AND fk_cout_fixe BETWEEN 8 AND 11 AND b.annee={a} AND b.foret={f}) AS passage_1,
                (SELECT SUM(a.superficie_traitee)/2 FROM appliquer a, parcelles b
                 WHERE a.fk_parcelles=b.id AND fk_cout_fixe BETWEEN 12 AND 13 AND b.annee={a} AND b.foret={f}) AS passage_2
            FROM appliquer))
        ) WHERE fk_activite=2 AND annee={a}"""
    )
    return JSONResponse("OK")


@router.post("/get/parcelles/entretien1/{foret}")
async def post_entretien1(foret: str, db=Depends(get_db)):
    f, a = int(foret), current_year
    await db.execute(
        f"""UPDATE resultats SET (objectif, realise) = (
            (SELECT SUM(superficie) FROM parcelles WHERE foret={f} AND annee={a-1}) * 3,
            (SELECT passage_1+passage_2+passage_3 FROM (SELECT DISTINCT
                (SELECT SUM(a.superficie_traitee)/2.2 FROM appliquer a, parcelles b
                 WHERE a.fk_parcelles=b.id AND fk_cout_fixe BETWEEN 14 AND 16 AND b.annee={a-1} AND b.foret={f}) AS passage_1,
                (SELECT SUM(a.superficie_traitee)/2 FROM appliquer a, parcelles b
                 WHERE a.fk_parcelles=b.id AND fk_cout_fixe BETWEEN 17 AND 18 AND b.annee={a-1} AND b.foret={f}) AS passage_2,
                (SELECT SUM(a.superficie_traitee)/2 FROM appliquer a, parcelles b
                 WHERE a.fk_parcelles=b.id AND fk_cout_fixe BETWEEN 19 AND 20 AND b.annee={a-1} AND b.foret={f}) AS passage_3
            FROM appliquer))
        ) WHERE fk_activite=3 AND annee={a-1}"""
    )
    return JSONResponse("OK")


@router.post("/get/parcelles/entretien2/{foret}")
async def post_entretien2(foret: str, db=Depends(get_db)):
    f, a = int(foret), current_year
    await db.execute(
        f"""UPDATE resultats SET (objectif, realise) = (
            (SELECT SUM(superficie) FROM parcelles WHERE foret={f} AND annee={a-2}) * 3,
            (SELECT passage_1+passage_2+passage_3 FROM (SELECT DISTINCT
                (SELECT SUM(a.superficie_traitee)/2.2 FROM appliquer a, parcelles b
                 WHERE a.fk_parcelles=b.id AND fk_cout_fixe BETWEEN 14 AND 16 AND b.annee={a-2} AND b.foret={f}) AS passage_1,
                (SELECT SUM(a.superficie_traitee)/2 FROM appliquer a, parcelles b
                 WHERE a.fk_parcelles=b.id AND fk_cout_fixe BETWEEN 17 AND 18 AND b.annee={a-2} AND b.foret={f}) AS passage_2,
                (SELECT SUM(a.superficie_traitee)/2 FROM appliquer a, parcelles b
                 WHERE a.fk_parcelles=b.id AND fk_cout_fixe BETWEEN 19 AND 20 AND b.annee={a-2} AND b.foret={f}) AS passage_3
            FROM appliquer))
        ) WHERE fk_activite=4 AND annee={a-2}"""
    )
    return JSONResponse("OK")


@router.post("/get/parcelles/entretien3/{foret}")
async def post_entretien3(foret: str, db=Depends(get_db)):
    f, a = int(foret), current_year
    await db.execute(
        f"""UPDATE resultats SET (objectif, realise) = (
            (SELECT SUM(superficie) FROM parcelles WHERE foret={f} AND annee={a-3}) * 2,
            (SELECT passage_1+passage_2 FROM (SELECT DISTINCT
                (SELECT SUM(a.superficie_traitee)/2 FROM appliquer a, parcelles b
                 WHERE a.fk_parcelles=b.id AND fk_cout_fixe BETWEEN 28 AND 29 AND b.annee={a-3} AND b.foret={f}) AS passage_1,
                (SELECT SUM(a.superficie_traitee)/2 FROM appliquer a, parcelles b
                 WHERE a.fk_parcelles=b.id AND fk_cout_fixe BETWEEN 30 AND 31 AND b.annee={a-3} AND b.foret={f}) AS passage_2
            FROM appliquer))
        ) WHERE fk_activite=5 AND annee={a-3}"""
    )
    return JSONResponse("OK")


# ─────────────────────────────────────────────────────────────────────────────
#  Entretien par parcelle — détail et mise à jour
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/get/parcelles/entretien/{foret}")
async def get_entretien_recap(foret: str, db=Depends(get_db)):
    rows = await db.fetch(
        f"SELECT SUM(objectif) AS objectif, SUM(realise) AS realise FROM resultats WHERE fk_activite BETWEEN 2 AND 5 AND fk_foret={int(foret)}"
    )
    return [dict(r) for r in rows]


@router.get("/get/parcelles/entretien/{annee}/{foret}")
async def get_entretien_annee(annee: str, foret: str, db=Depends(get_db)):
    a, f = int(annee), int(foret)
    annee_calc = current_year if a == 0 else current_year - a
    rows = await db.fetch(
        f"""SELECT b.fk_cout_fixe, SUM(a.superficie) AS superficie,
                   SUM(b.superficie_traitee) AS superficie_traitee
            FROM parcelles AS a, appliquer AS b
            WHERE a.id = b.fk_parcelles AND a.foret={f} AND a.annee={annee_calc}
            GROUP BY fk_cout_fixe ORDER BY fk_cout_fixe ASC"""
    )
    return [dict(r) for r in rows]


@router.get("/get/parcelles/entretien/{annee}/{foret}/{travail}")
async def get_entretien_detail(annee: str, foret: str, travail: str, db=Depends(get_db)):
    a, f, t = int(annee), int(foret), int(travail)
    annee_calc = current_year if a == 0 else current_year - a
    rows = await db.fetch(
        f"""SELECT a.id, a.numero, a.annee, a.essence, a.superficie, b.superficie_traitee
            FROM parcelles AS a, appliquer AS b
            WHERE a.id=b.fk_parcelles AND a.foret={f} AND a.annee={annee_calc} AND b.fk_cout_fixe={t}
            ORDER BY id ASC"""
    )
    return [dict(r) for r in rows]


@router.post("/get/parcelles/entretien/{annee}/{foret}/{travail}")
async def post_entretien_update(
    annee: str, foret: str, travail: str,
    body: dict = Body({}),
    db=Depends(get_db),
):
    updates = body.get("updates", [])
    if not isinstance(updates, list):
        return JSONResponse({"message": "Paramètre updates invalide"}, status_code=400)
    for item in updates:
        if not item.get("id") or item.get("value") in (None, ""):
            continue
        await db.execute(
            "UPDATE appliquer SET superficie_traitee=$1 WHERE fk_parcelles=$2 AND fk_cout_fixe=$3",
            float(item["value"]), int(item["id"]), int(travail),
        )
    return JSONResponse("Mise à jour réussie", status_code=200)


# ─────────────────────────────────────────────────────────────────────────────
#  Graphiques
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/get/parcelles/cu/graph1/{foret}/{annee}")
async def get_graph1(foret: str, annee: str, db=Depends(get_db)):
    f, a = int(foret), int(annee)
    row = await db.fetchrow(
        f"""SELECT
            (SELECT SUM(a.superficie_traitee) FROM appliquer a,parcelles b WHERE a.fk_parcelles=b.id AND b.foret={f} AND fk_cout_fixe=1 AND b.annee={a}) AS raba,
            (SELECT SUM(superficie_traitee) FROM appliquer a,parcelles b WHERE a.fk_parcelles=b.id AND b.foret={f} AND fk_cout_fixe=2 AND b.annee={a}) AS aba,
            (SELECT SUM(superficie_traitee) FROM appliquer a,parcelles b WHERE a.fk_parcelles=b.id AND b.foret={f} AND fk_cout_fixe=3 AND b.annee={a}) AS bru,
            (SELECT SUM(superficie_traitee) FROM appliquer a,parcelles b WHERE a.fk_parcelles=b.id AND b.foret={f} AND fk_cout_fixe=4 AND b.annee={a}) AS piq,
            (SELECT SUM(superficie_traitee) FROM appliquer a,parcelles b WHERE a.fk_parcelles=b.id AND b.foret={f} AND fk_cout_fixe=5 AND b.annee={a}) AS ouv,
            (SELECT SUM(superficie_traitee) FROM appliquer a,parcelles b WHERE a.fk_parcelles=b.id AND b.foret={f} AND fk_cout_fixe=6 AND b.annee={a}) AS trou,
            (SELECT SUM(superficie_traitee) FROM appliquer a,parcelles b WHERE a.fk_parcelles=b.id AND b.foret={f} AND fk_cout_fixe=7 AND b.annee={a}) AS plan
            FROM appliquer LIMIT 1"""
    )
    return [dict(row)] if row else []


@router.get("/get/fiches/cu/graph1/{id}")
async def get_fiche_graph1(id: str, db=Depends(get_db)):
    rows = await db.fetch(
        f"""SELECT c.numero, c.essence, c.annee, c.partenaire, c.densite, c.ugf, c.foret,
                   c.superficie, c.partenaire AS financement,
                   a.fk_cout_fixe AS id_travail,
                   TO_CHAR(a.date_init,'dd/mm/yyyy') AS date_debut,
                   TO_CHAR(a.date_fin,'dd/mm/yyyy') AS date_fin,
                   a.superficie_traitee AS realise, b.cout
            FROM appliquer AS a, cout_fixe AS b, parcelles AS c
            WHERE a.fk_cout_fixe=b.id AND a.fk_parcelles=c.id
              AND a.fk_parcelles={int(id)} AND a.fk_cout_fixe BETWEEN 1 AND 13
            ORDER BY a.fk_cout_fixe ASC"""
    )
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
#  POST sélections
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/mise_en_place")
async def post_selection_mise_en_place(body: dict = Body({}), db=Depends(get_db)):
    foret  = body.get("foret", [])
    annees = body.get("annees", [])
    if not foret or not annees:
        return JSONResponse({"message": "Paramètres requis."}, status_code=400)
    fl = ",".join(str(f) for f in foret)
    al = ",".join(str(a) for a in annees)
    rows = await db.fetch(
        f"""SELECT a.id, b.foret AS foret, a.annee, a.numero, a.essence,
                   a.densite, a.partenaire, a.longitude AS x, a.latitude AS y, a.superficie
            FROM parcelles AS a JOIN foret AS b ON a.foret=b.id
            WHERE a.foret IN ({fl}) AND a.annee IN ({al}) ORDER BY a.numero ASC"""
    )
    if not rows:
        return JSONResponse({"message": "Aucune donnée trouvée."}, status_code=404)
    return [dict(r) for r in rows]


@router.post("/entretien_p")
async def post_selection_entretien(body: dict = Body({}), db=Depends(get_db)):
    foret           = body.get("foret", [])
    annees          = body.get("annees", [])
    entretien_annee = body.get("entretien_annee", [])
    if not foret or not annees or not entretien_annee:
        return JSONResponse({"message": "Paramètres requis."}, status_code=400)
    annee_calc = [a - e for a in annees for e in entretien_annee]
    fl = ",".join(str(f) for f in foret)
    al = ",".join(str(a) for a in annee_calc)
    rows = await db.fetch(
        f"""SELECT a.id, b.foret AS foret, a.annee, a.numero, a.essence,
                   a.densite, a.partenaire, a.longitude AS x, a.latitude AS y, a.superficie
            FROM parcelles AS a JOIN foret AS b ON a.foret=b.id
            WHERE a.foret IN ({fl}) AND a.annee IN ({al}) ORDER BY a.numero ASC"""
    )
    if not rows:
        return JSONResponse({"message": "Aucune donnée trouvée."}, status_code=404)
    return [dict(r) for r in rows]


@router.post("/sylviculture")
async def post_selection_sylviculture(body: dict = Body({}), db=Depends(get_db)):
    body["entretien_annee"] = [4]
    return await post_selection_entretien(body, db)


@router.post("/rapport_entretien")
async def post_rapport_entretien(body: dict = Body({}), db=Depends(get_db)):
    parcelle_id = body.get("parcelleId")
    if not parcelle_id:
        return JSONResponse({"message": "parcelleId requis."}, status_code=400)
    rows = await db.fetch(
        f"""SELECT a.montant AS montant, a.travail AS activite,
                   b.superficie_traitee AS realise, b.fk_cout_fixe,
                   c.numero AS numero_parcelle
            FROM cout_fixe AS a
            JOIN appliquer AS b ON a.id=b.fk_cout_fixe
            JOIN parcelles AS c ON b.fk_parcelles=c.id
            WHERE c.id={int(parcelle_id)}"""
    )
    if not rows:
        return JSONResponse({"message": "Aucune donnée trouvée."}, status_code=404)
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
#  /api/donnees — graphiques dashboard
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/api/donnees")
async def post_api_donnees(body: dict = Body({}), db=Depends(get_db)):
    foret  = body.get("foret", [])
    annees = body.get("annees", [])
    if not foret or not annees:
        return JSONResponse({"message": "Forêt et années requis."}, status_code=400)
    al = ",".join(str(a) for a in annees)
    fl = ",".join(str(f) for f in foret)
    rows = await db.fetch(
        f"""SELECT a.id, a.superficie, a.essence, a.partenaire, a.densite, a.numero,
            COALESCE(SUM(CASE WHEN a.annee IN ({al}) AND a.foret=ANY(ARRAY[{fl}]) AND b.fk_cout_fixe=1 THEN b.superficie_traitee ELSE 0 END),0) AS rabattage,
            COALESCE(SUM(CASE WHEN a.annee IN ({al}) AND a.foret=ANY(ARRAY[{fl}]) AND b.fk_cout_fixe=2 THEN b.superficie_traitee ELSE 0 END),0) AS abattage,
            COALESCE(SUM(CASE WHEN a.annee IN ({al}) AND a.foret=ANY(ARRAY[{fl}]) AND b.fk_cout_fixe=3 THEN b.superficie_traitee ELSE 0 END),0) AS brulage,
            COALESCE(SUM(CASE WHEN a.annee IN ({al}) AND a.foret=ANY(ARRAY[{fl}]) AND b.fk_cout_fixe=4 THEN b.superficie_traitee ELSE 0 END),0) AS ouverture,
            COALESCE(SUM(CASE WHEN a.annee IN ({al}) AND a.foret=ANY(ARRAY[{fl}]) AND b.fk_cout_fixe=5 THEN b.superficie_traitee ELSE 0 END),0) AS piquetage,
            COALESCE(SUM(CASE WHEN a.annee IN ({al}) AND a.foret=ANY(ARRAY[{fl}]) AND b.fk_cout_fixe=6 THEN b.superficie_traitee ELSE 0 END),0) AS trouaison,
            COALESCE(SUM(CASE WHEN a.annee IN ({al}) AND a.foret=ANY(ARRAY[{fl}]) AND b.fk_cout_fixe=7 THEN b.superficie_traitee ELSE 0 END),0) AS planting,
            COALESCE((((SUM(CASE WHEN a.annee IN ({al}) AND a.foret=ANY(ARRAY[{fl}]) AND b.fk_cout_fixe BETWEEN 1 AND 7 THEN b.superficie_traitee ELSE 0 END))/(a.superficie*7))*100),0) AS taux
            FROM parcelles a LEFT JOIN appliquer b ON a.id=b.fk_parcelles
            WHERE a.annee IN ({al}) AND a.foret=ANY(ARRAY[{fl}])
            GROUP BY a.id ORDER BY a.id ASC"""
    )
    if not rows:
        return JSONResponse({"message": "Aucune donnée trouvée."}, status_code=404)
    return [dict(r) for r in rows]


@router.get("/api/donnees")
async def get_api_donnees(foret: str, annees: str, db=Depends(get_db)):
    rows = await db.fetch(
        f"""SELECT a.id, a.superficie, a.essence, a.partenaire, a.densite, a.annee,
                   a.foret, b.superficie_traitee AS realise, a.numero,
            COALESCE(SUM(CASE WHEN a.annee IN ({annees}) AND a.foret IN ({foret}) AND b.fk_cout_fixe=1 THEN b.superficie_traitee ELSE 0 END),0) AS rabattage,
            COALESCE(SUM(CASE WHEN a.annee IN ({annees}) AND a.foret IN ({foret}) AND b.fk_cout_fixe=2 THEN b.superficie_traitee ELSE 0 END),0) AS abattage,
            COALESCE(SUM(CASE WHEN a.annee IN ({annees}) AND a.foret IN ({foret}) AND b.fk_cout_fixe=3 THEN b.superficie_traitee ELSE 0 END),0) AS brulage,
            COALESCE(SUM(CASE WHEN a.annee IN ({annees}) AND a.foret IN ({foret}) AND b.fk_cout_fixe=4 THEN b.superficie_traitee ELSE 0 END),0) AS ouverture,
            COALESCE(SUM(CASE WHEN a.annee IN ({annees}) AND a.foret IN ({foret}) AND b.fk_cout_fixe=5 THEN b.superficie_traitee ELSE 0 END),0) AS piquetage,
            COALESCE(SUM(CASE WHEN a.annee IN ({annees}) AND a.foret IN ({foret}) AND b.fk_cout_fixe=6 THEN b.superficie_traitee ELSE 0 END),0) AS trouaison,
            COALESCE(SUM(CASE WHEN a.annee IN ({annees}) AND a.foret IN ({foret}) AND b.fk_cout_fixe=7 THEN b.superficie_traitee ELSE 0 END),0) AS planting,
            COALESCE((((SUM(CASE WHEN a.annee IN ({annees}) AND a.foret IN ({foret}) AND b.fk_cout_fixe BETWEEN 1 AND 7 THEN b.superficie_traitee ELSE 0 END))/(a.superficie*7))*100),0) AS taux
            FROM parcelles a LEFT JOIN appliquer b ON a.id=b.fk_parcelles
            WHERE a.annee IN ({annees}) AND a.foret IN ({foret})
            GROUP BY a.id, b.superficie_traitee ORDER BY a.id ASC"""
    )
    if not rows:
        return JSONResponse({"message": "Aucune donnée trouvée."}, status_code=404)
    return [dict(r) for r in rows]
