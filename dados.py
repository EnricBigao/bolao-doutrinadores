"""
Gerenciamento de dados do bolão — salva/carrega palpites e resultados em JSON.
"""
import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
PALPITES_FILE = DATA_DIR / "palpites.json"
RESULTADOS_FILE = DATA_DIR / "resultados.json"

DATA_DIR.mkdir(exist_ok=True)


# ── helpers genéricos ────────────────────────────────────────────────────────

def _load(path: Path) -> dict:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save(path: Path, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── palpites ─────────────────────────────────────────────────────────────────

def carregar_palpites() -> dict:
    """
    Estrutura:
    {
      "Thiaguinho Vrau": {
        "trancado": false,
        "palpites": {
          "1": {"gols1": 2, "gols2": 1},
          ...
        }
      },
      ...
    }
    """
    return _load(PALPITES_FILE)


def salvar_palpites(dados: dict):
    _save(PALPITES_FILE, dados)


def palpites_participante(nome: str) -> dict:
    dados = carregar_palpites()
    return dados.get(nome, {"trancado": False, "palpites": {}})


def salvar_palpite(nome: str, jogo_id: int, gols1: int, gols2: int):
    dados = carregar_palpites()
    if nome not in dados:
        dados[nome] = {"trancado": False, "palpites": {}}
    if dados[nome].get("trancado"):
        return False  # não pode editar
    dados[nome]["palpites"][str(jogo_id)] = {"gols1": gols1, "gols2": gols2}
    _save(PALPITES_FILE, dados)
    return True


def trancar(nome: str):
    dados = carregar_palpites()
    if nome not in dados:
        dados[nome] = {"trancado": False, "palpites": {}}
    dados[nome]["trancado"] = True
    _save(PALPITES_FILE, dados)


def destrancar(nome: str):
    """Usado pelo admin para corrigir em caso de necessidade."""
    dados = carregar_palpites()
    if nome in dados:
        dados[nome]["trancado"] = False
    _save(PALPITES_FILE, dados)


# ── resultados reais ──────────────────────────────────────────────────────────

def carregar_resultados() -> dict:
    """
    {
      "1": {"gols1": 2, "gols2": 0},
      ...
    }
    """
    return _load(RESULTADOS_FILE)


def salvar_resultado(jogo_id: int, gols1: int, gols2: int):
    dados = carregar_resultados()
    dados[str(jogo_id)] = {"gols1": gols1, "gols2": gols2}
    _save(RESULTADOS_FILE, dados)


def remover_resultado(jogo_id: int):
    dados = carregar_resultados()
    dados.pop(str(jogo_id), None)
    _save(RESULTADOS_FILE, dados)


# ── pontuação ─────────────────────────────────────────────────────────────────

def _vencedor(g1: int, g2: int) -> str:
    if g1 > g2:
        return "time1"
    if g2 > g1:
        return "time2"
    return "empate"


def calcular_pontos(nome: str) -> dict:
    """
    Retorna {"total": N, "detalhes": {jogo_id: {"acerto_resultado": bool, "acerto_placar": bool}}}
    """
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
            pts = 3  # placar certo já inclui resultado certo
        elif acerto_res:
            pts = 1

        total += pts
        detalhes[jid] = {"acerto_resultado": acerto_res, "acerto_placar": acerto_placar, "pontos": pts}

    return {"total": total, "detalhes": detalhes}


def tabela_geral(participantes: list) -> list:
    """Retorna lista ordenada por pontos."""
    rows = []
    for nome in participantes:
        pts = calcular_pontos(nome)
        info = palpites_participante(nome)
        rows.append({
            "Participante": nome,
            "Pontos": pts["total"],
            "🔒 Trancado": "✅" if info.get("trancado") else "❌",
        })
    rows.sort(key=lambda x: x["Pontos"], reverse=True)
    # adiciona posição
    for i, r in enumerate(rows):
        emoji = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}º"
        r["Pos"] = emoji
    return rows
