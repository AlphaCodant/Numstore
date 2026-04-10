"""
Routes dashboard : sélection UGF, requêtes géospatiales, stock, éléments.
"""
import json
import logging

from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse

from database import get_db
from auth import require_auth

router = APIRouter()
logger = logging.getLogger(__name__)

# Correspondance nom UGF → id forêt
CORRESP = {"tene": 1, "sangoue": 2}

# Opérateurs SQL autorisés (whitelist sécurité)
ALLOWED_OPERATORS = {
    "=", "!=", "<", ">", "<=", ">=",
    "ilike", "not ilike", "like", "not like"
}


def _build_ddf(elements: list) -> str:
    ids = [str(CORRESP[e]) for e in elements if e in CORRESP]
    return f"({','.join(ids)})" if ids else "(0)"


def _validate_op(op: str) -> str:
    op = op.strip().lower()
    if op not in ALLOWED_OPERATORS:
        raise ValueError(f"Opérateur non autorisé: {op}")
    return op


def _fmt_val(op: str, val: str) -> str:
    if op in ("ilike", "not ilike", "like", "not like"):
        return f"'{val}%'"
    return val


# ─────────────────────────────────────────────────────────────────────────────
#  POST /dashboard/00000/:id — sélection UGF
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/dashboard/00000/{id}")
async def dashboard_selection(request: Request, id: str, db=Depends(get_db)):
    user    = require_auth(request)
    email   = user["email"]
    token_y = user["tokenY"]

    form       = await request.form()
    tout_ugf   = form.get("tout_ugf")
    ugf_tene   = form.get("ugf_tene")
    ugf_sangoue = form.get("ugf_sangoue")

    elements = [v for v in [tout_ugf, ugf_sangoue, ugf_tene] if v]
    if not elements:
        return JSONResponse(status_code=204, content=None)

    ddf = _build_ddf(elements)

    # Mettre à jour stock
    existing = await db.fetchrow("SELECT email FROM stock WHERE email LIKE $1", email)
    if existing:
        await db.execute("UPDATE stock SET data=$1 WHERE email LIKE $2", ddf, email)
    else:
        await db.execute("INSERT INTO stock (email, data) VALUES ($1,$2)", email, ddf)

    # Générer GeoJSON
    row = await db.fetchrow(
        f"""SELECT json_build_object('type','FeatureCollection','features',
                json_agg(ST_AsGeoJSON(t.*)::json)) AS donnee
            FROM (SELECT a.id, b.foret AS foret, a.annee, a.numero, a.essence,
                         a.densite, a.partenaire, a.longitude AS x, a.latitude AS y,
                         a.superficie, ST_Transform(geom, 4326)
                  FROM public.parcelles_{token_y} a
                  JOIN public.foret_{token_y} b ON a.foret=b.id
                  WHERE a.foret IN {ddf}) AS t"""
    )
    if row and row["donnee"]:
        geojson_path = f"static/json/fichier-{token_y}.geojson"
        with open(geojson_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(row["donnee"]))

    return JSONResponse(status_code=204, content=None)


# ─────────────────────────────────────────────────────────────────────────────
#  POST /requete/:id — filtre géospatial
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/requete/{id}")
async def requete_geo(request: Request, id: str, db=Depends(get_db)):
    user    = require_auth(request)
    email   = user["email"]
    token_y = user["tokenY"]

    stock_row = await db.fetchrow("SELECT data FROM stock WHERE email LIKE $1", email)
    if not stock_row:
        return JSONResponse(status_code=204, content=None)
    ddf = stock_row["data"]

    form = await request.form()
    cocher  = form.get("cocher")
    cocher2 = form.get("cocher2")
    cocher3 = form.get("cocher3")
    attr1   = form.get("attributes", "")
    attr2   = form.get("attributes2", "")
    attr3   = form.get("attributes3", "")
    val1    = form.get("value", "")
    val2    = form.get("value2", "")
    val3    = form.get("value3", "")

    try:
        op1 = _validate_op(form.get("operator", "="))
        op2 = _validate_op(form.get("operator2", "="))
        op3 = _validate_op(form.get("operator3", "="))
    except ValueError as e:
        return JSONResponse({"message": str(e)}, status_code=400)

    v1, v2, v3 = _fmt_val(op1, val1), _fmt_val(op2, val2), _fmt_val(op3, val3)

    base = (
        f"SELECT a.id, b.foret AS foret, a.annee, a.numero, a.essence, "
        f"a.densite, a.partenaire, a.longitude AS x, a.latitude AS y, "
        f"a.superficie, ST_Transform(geom, 4326) "
        f"FROM public.parcelles_{token_y} a "
        f"JOIN public.foret_{token_y} b ON a.foret=b.id "
        f"WHERE a.foret IN {ddf}"
    )

    if cocher and cocher2 and cocher3:
        j1 = "OR" if attr1 == attr2 else "AND"
        j2 = "OR" if attr2 == attr3 else "AND"
        where = f"AND {attr1} {op1} {v1} {j1} {attr2} {op2} {v2} {j2} {attr3} {op3} {v3}"
    elif cocher and cocher2:
        j1 = "OR" if attr1 == attr2 else "AND"
        where = f"AND {attr1} {op1} {v1} {j1} {attr2} {op2} {v2}"
    elif cocher:
        where = f"AND {attr1} {op1} {v1}"
    else:
        return JSONResponse(status_code=204, content=None)

    row = await db.fetchrow(
        f"""SELECT json_build_object('type','FeatureCollection','features',
                json_agg(ST_AsGeoJSON(t.*)::json)) AS donnee
            FROM ({base} {where}) AS t"""
    )

    if row and row["donnee"]:
        geojson_path = f"static/json/fichier-{token_y}.geojson"
        with open(geojson_path, "w", encoding="utf-8") as f_out:
            f_out.write(json.dumps(row["donnee"]))

    return JSONResponse(status_code=204, content=None)


# ─────────────────────────────────────────────────────────────────────────────
#  Éléments / stock
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/elements/elem/{id}")
async def get_elements_elem(request: Request, id: str, db=Depends(get_db)):
    user  = require_auth(request)
    email = user["email"]
    row   = await db.fetchrow("SELECT data FROM stock WHERE email LIKE $1", email)
    return JSONResponse(row["data"] if row else None)


@router.get("/elements/token")
async def get_elements_token(request: Request):
    user = require_auth(request)
    return JSONResponse(user.get("tokenY", ""))


@router.get("/elements/requetes")
async def get_elements_requetes():
    return JSONResponse([])


@router.get("/elements/element")
async def get_elements_element():
    return JSONResponse([])


@router.get("/iteration")
async def get_iteration():
    return JSONResponse([])


@router.get("/data")
async def get_data():
    return JSONResponse([])
