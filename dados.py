"""
Gerenciamento de dados do bolão — Supabase como banco de dados.
"""
import os
import requests

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://jwyrvijbfiaegoengdyt.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_FaHwpxfEu56AgD1w_dk12g_3lqFtpqO")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}


def _get(table: str, params: dict = None):
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}", headers=HEADERS, params=params)
    r.raise_for_status()
    return r.json()


def _upsert(table: str, data: dict):
    h = {**HEADERS, "Prefer": "resolution=merge-duplicates,return=representation"}
    r = requests.post(f"{SUPABASE_URL}/rest/v1/{table}", headers=h, json=data)
    r.raise_for_status()
    return r.json()


def _delete(table: str, params: dict):
    r = requests.delete(f"{SUPABASE_URL}/rest/v1/{table}", headers=HEADERS, params=params)
    r.raise_for_status()


# ── palpites ──────────────────────────────────────────────────────────────────

def palpites_participante(nome: str) -> dict:
    rows = _get("palpites", {"participante": f"eq.{nome}"})
    trancado_rows = _get("trancados", {"participante": f"eq.{nome}"})
    trancado = trancado_rows[0]["trancado"] if trancado_rows else False
    palpites = {str(r["jogo_id"]): {"gols1": r["gols1"], "gols2": r["gols2"]} for r in rows}
    return {"trancado": trancado, "palpites": palpites}


def salvar_palpite(nome: str, jogo_id: int, gols1: int, gols2: int):
    # checa se está trancado
    trancado_rows = _get("trancados", {"participante": f"eq.{nome}"})
    if trancado_rows and trancado_rows[0]["trancado"]:
        return False
    _upsert("palpites", {"participante": nome, "jogo_id": jogo_id, "gols1": gols1, "gols2": gols2})
    return True


def trancar(nome: str):
    _upsert("trancados", {"participante": nome, "trancado": True})


def destrancar(nome: str):
    _upsert("trancados", {"participante": nome, "trancado": False})


def carregar_palpites() -> dict:
    """Retorna todos os palpites agrupados por participante (usado no admin)."""
    rows = _get("palpites")
    trancados = {r["participante"]: r["trancado"] for r in _get("trancados")}
    result = {}
    for r in rows:
        nome = r["participante"]
        if nome not in result:
            result[nome] = {"trancado": trancados.get(nome, False), "palpites": {}}
        result[nome]["palpites"][str(r["jogo_id"])] = {"gols1": r["gols1"], "gols2": r["gols2"]}
    return result


# ── resultados reais ──────────────────────────────────────────────────────────

def carregar_resultados() -> dict:
    rows = _get("resultados")
    return {str(r["jogo_id"]): {"gols1": r["gols1"], "gols2": r["gols2"]} for r in rows}


def salvar_resultado(jogo_id: int, gols1: int, gols2: int):
    _upsert("resultados", {"jogo_id": jogo_id, "gols1": gols1, "gols2": gols2})


def remover_resultado(jogo_id: int):
    _delete("resultados", {"jogo_id": f"eq.{jogo_id}"})


# ── pontuação ─────────────────────────────────────────────────────────────────

def _vencedor(g1: int, g2: int) -> str:
    if g1 > g2:
        return "time1"
    if g2 > g1:
        return "time2"
    return "empate"


def calcular_pontos(nome: str) -> dict:
    resultados = carregar_resultados()
    palpite_info = palpites_participante(nome)
    palpites = palpite_info.get("palpites", {})

    total = 0
    detalhes = {}

    for jid, res in resultados.items():
        pal = palpites.get(str(jid))
        if pal is None:
            detalhes[jid] = {"acerto_resultado": False, "acerto_placar": False, "pontos": 0}
            continue

        acerto_res = _vencedor(pal["gols1"], pal["gols2"]) == _vencedor(res["gols1"], res["gols2"])
        acerto_placar = pal["gols1"] == res["gols1"] and pal["gols2"] == res["gols2"]

        pts = 0
        if acerto_placar:
            pts = 3
        elif acerto_res:
            pts = 1

        total += pts
        detalhes[jid] = {"acerto_resultado": acerto_res, "acerto_placar": acerto_placar, "pontos": pts}

    return {"total": total, "detalhes": detalhes}


def tabela_geral(participantes: list) -> list:
    bonus_map = carregar_bonus()
    rows = []
    for nome in participantes:
        pts = calcular_pontos(nome)
        info = palpites_participante(nome)
        bonus = bonus_map.get(nome, 0)
        rows.append({
            "Participante": nome,
            "Pts Auto": pts["total"],
            "Bônus": bonus,
            "Pontos": pts["total"] + bonus,
            "🔒 Trancado": "✅" if info.get("trancado") else "❌",
        })
    rows.sort(key=lambda x: x["Pontos"], reverse=True)
    for i, r in enumerate(rows):
        emoji = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}º"
        r["Pos"] = emoji
    return rows


# ── pontos bônus ─────────────────────────────────────────────────────────────

def carregar_bonus() -> dict:
    rows = _get("pontos_bonus")
    return {r["participante"]: r["bonus"] for r in rows}


def salvar_bonus(nome: str, bonus: int):
    _upsert("pontos_bonus", {"participante": nome, "bonus": bonus})
