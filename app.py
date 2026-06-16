"""
🏆 Bolão dos Doutrinadores — Copa do Mundo 2026
Rode com:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

from jogos import JOGOS, PARTICIPANTES
from dados import (
    palpites_participante,
    salvar_palpite,
    trancar,
    destrancar,
    carregar_resultados,
    salvar_resultado,
    remover_resultado,
    calcular_pontos,
    tabela_geral,
)

# ── configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bolão dos Doutrinadores 🏆",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── estilo custom ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Fundo e fonte geral */
body, .stApp { background-color: #0d1117; color: #e6edf3; }

/* Cabeçalho do bolão */
.header-box {
    background: linear-gradient(135deg, #1a6b3c 0%, #0d3d20 100%);
    border-radius: 16px;
    padding: 20px 30px;
    margin-bottom: 20px;
    text-align: center;
    border: 1px solid #2ea043;
}
.header-box h1 { margin: 0; font-size: 2.2rem; color: #ffd700; }
.header-box p  { margin: 4px 0 0; color: #8bcc9c; font-size: 1rem; }

/* Card de jogo */
.jogo-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
.jogo-header {
    display: flex;
    justify-content: space-between;
    color: #8b949e;
    font-size: 0.78rem;
    margin-bottom: 8px;
}
.times {
    font-size: 1.1rem;
    font-weight: 600;
    color: #e6edf3;
    text-align: center;
}

/* Placar verde quando acertou */
.acerto-placar { color: #2ea043; font-weight: bold; }
.acerto-res    { color: #f0a500; font-weight: bold; }
.sem-acerto    { color: #6e7681; }

/* Tabela geral */
.medal-row { font-size: 1.05rem; }

/* Botão trancar */
div[data-testid="stButton"] > button[kind="primary"] {
    background: #b91c1c;
    border: none;
    color: white;
    font-weight: bold;
}

div[data-testid="stButton"] > button:hover {
    filter: brightness(1.15);
}
</style>
""", unsafe_allow_html=True)

# ── header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-box">
  <h1>⚽ Bolão dos Doutrinadores</h1>
  <p>Copa do Mundo 2026 · Vamos ver quem manda!</p>
</div>
""", unsafe_allow_html=True)

# ── abas ──────────────────────────────────────────────────────────────────────
abas_nomes = ["🏆 Tabela Geral"] + [f"⚽ {p}" for p in PARTICIPANTES] + ["🔧 Admin"]
abas = st.tabs(abas_nomes)

# ─────────────────────────────────────────────────────────────────────────────
# ABA 0: Tabela Geral
# ─────────────────────────────────────────────────────────────────────────────
with abas[0]:
    st.subheader("📊 Quadro de Pontuação")

    resultados = carregar_resultados()
    jogos_finalizados = len(resultados)
    st.caption(f"Jogos com resultado registrado: **{jogos_finalizados}** / {len(JOGOS)}")

    tabela = tabela_geral(PARTICIPANTES)
    df = pd.DataFrame(tabela)[["Pos", "Participante", "Pontos", "🔒 Trancado"]]
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("🗓️ Últimos resultados registrados")

    if not resultados:
        st.info("Nenhum resultado registrado ainda. Aguardando os jogos!")
    else:
        jogo_map = {str(j["id"]): j for j in JOGOS}
        res_rows = []
        for jid, res in sorted(resultados.items(), key=lambda x: int(x[0])):
            jogo = jogo_map.get(jid)
            if jogo:
                res_rows.append({
                    "Jogo": f"{jogo['time1']} {res['gols1']} × {res['gols2']} {jogo['time2']}",
                    "Data": f"{jogo['data']}  {jogo['hora']}",
                    "Grupo": jogo["grupo"],
                })
        st.dataframe(pd.DataFrame(res_rows), use_container_width=True, hide_index=True)

    # placar individual dos palpites
    st.divider()
    st.subheader("🔎 Detalhes por participante")
    part_sel = st.selectbox("Selecione um participante", PARTICIPANTES, key="sel_detalhe")
    if part_sel:
        pts_info = calcular_pontos(part_sel)
        detalhes = pts_info["detalhes"]
        jogo_map = {str(j["id"]): j for j in JOGOS}
        pal_info = palpites_participante(part_sel)
        palpites = pal_info.get("palpites", {})

        rows_det = []
        for jid, det in sorted(detalhes.items(), key=lambda x: int(x[0])):
            jogo = jogo_map.get(jid)
            if not jogo:
                continue
            res = resultados.get(jid, {})
            pal = palpites.get(jid, {})
            rows_det.append({
                "Jogo": f"{jogo['time1']} × {jogo['time2']}",
                "Real": f"{res.get('gols1','?')} × {res.get('gols2','?')}",
                "Palpite": f"{pal.get('gols1','?')} × {pal.get('gols2','?')}",
                "Pontos": det["pontos"],
            })

        if rows_det:
            st.dataframe(pd.DataFrame(rows_det), use_container_width=True, hide_index=True)
        else:
            st.info("Ainda sem jogos finalizados para mostrar detalhes.")


# ─────────────────────────────────────────────────────────────────────────────
# ABAS DOS PARTICIPANTES
# ─────────────────────────────────────────────────────────────────────────────
for idx, nome in enumerate(PARTICIPANTES):
    with abas[idx + 1]:
        info = palpites_participante(nome)
        trancado = info.get("trancado", False)
        palpites_salvos = info.get("palpites", {})

        col_l, col_r = st.columns([3, 1])
        with col_l:
            st.subheader(f"⚽ Palpites de {nome}")
        with col_r:
            pts = calcular_pontos(nome)["total"]
            st.metric("Pontuação atual", f"{pts} pts")

        if trancado:
            st.warning("🔒 Seus palpites estão **trancados** e não podem ser alterados.")
        else:
            st.info("✏️ Você ainda pode editar seus palpites. Lembre-se de **Salvar** e depois **Trancar** antes do início dos jogos!")

        # ── formulário de palpites ────────────────────────────────────────────
        resultados = carregar_resultados()

        # Agrupa jogos por data para facilitar a visualização
        datas_unicas = sorted(set(j["data"] for j in JOGOS))

        novos_palpites = {}

        for data in datas_unicas:
            jogos_do_dia = [j for j in JOGOS if j["data"] == data]
            # formata data em pt-BR
            try:
                dt = datetime.strptime(data, "%Y-%m-%d")
                data_fmt = dt.strftime("%d/%m/%Y")
            except Exception:
                data_fmt = data

            st.markdown(f"#### 📅 {data_fmt}")

            for jogo in jogos_do_dia:
                jid = str(jogo["id"])
                pal_atual = palpites_salvos.get(jid, {"gols1": 0, "gols2": 0})
                res_real = resultados.get(jid)

                # Card visual
                with st.container():
                    st.markdown(
                        f"""<div class="jogo-card">
                        <div class="jogo-header">
                            <span>Grupo {jogo['grupo']}</span>
                            <span>⏰ {jogo['hora']}</span>
                        </div>
                        <div class="times">{jogo['time1']} ⚔️ {jogo['time2']}</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )

                    col1, col2, col3, col4, col5 = st.columns([3, 1, 0.5, 1, 3])
                    with col1:
                        st.markdown(f"**{jogo['time1']}**")
                    with col2:
                        g1 = st.number_input(
                            "Gols",
                            min_value=0, max_value=30,
                            value=int(pal_atual.get("gols1", 0)),
                            key=f"g1_{nome}_{jid}",
                            disabled=trancado,
                            label_visibility="collapsed",
                        )
                    with col3:
                        st.markdown("<p style='text-align:center;font-size:1.3rem;margin-top:4px'>×</p>", unsafe_allow_html=True)
                    with col4:
                        g2 = st.number_input(
                            "Gols",
                            min_value=0, max_value=30,
                            value=int(pal_atual.get("gols2", 0)),
                            key=f"g2_{nome}_{jid}",
                            disabled=trancado,
                            label_visibility="collapsed",
                        )
                    with col5:
                        st.markdown(f"**{jogo['time2']}**")

                    # Mostra resultado real se disponível
                    if res_real:
                        acerto_placar = (g1 == res_real["gols1"] and g2 == res_real["gols2"])
                        def venc(a, b):
                            return "time1" if a > b else ("time2" if b > a else "emp")
                        acerto_res = venc(g1, g2) == venc(res_real["gols1"], res_real["gols2"])

                        res_str = f"Resultado: **{res_real['gols1']} × {res_real['gols2']}**"
                        if acerto_placar:
                            st.success(f"✅ {res_str} — Placar certo! **+3 pts**")
                        elif acerto_res:
                            st.warning(f"🟡 {res_str} — Acertou o resultado! **+1 pt**")
                        else:
                            st.error(f"❌ {res_str} — Sem pontos")

                    novos_palpites[jid] = {"gols1": int(g1), "gols2": int(g2)}

        st.divider()

        if not trancado:
            col_s, col_t = st.columns(2)
            with col_s:
                if st.button("💾 Salvar palpites", key=f"salvar_{nome}", use_container_width=True):
                    for jid, pal in novos_palpites.items():
                        salvar_palpite(nome, int(jid), pal["gols1"], pal["gols2"])
                    st.success("✅ Palpites salvos!")
                    st.rerun()

            with col_t:
                if st.button("🔒 Trancar palpites", key=f"trancar_btn_{nome}", type="primary", use_container_width=True):
                    st.session_state[f"confirmar_trancar_{nome}"] = True

            # ── diálogo de confirmação ────────────────────────────────────
            if st.session_state.get(f"confirmar_trancar_{nome}"):
                st.warning(
                    f"⚠️ **Tem certeza?**\n\n"
                    f"Após trancar, **{nome}** não poderá mais alterar nenhum palpite. "
                    "Só o admin consegue destrancar.",
                    icon="🔒",
                )
                col_sim, col_nao = st.columns(2)
                with col_sim:
                    if st.button("✅ Sim, trancar!", key=f"confirmar_sim_{nome}", use_container_width=True, type="primary"):
                        for jid, pal in novos_palpites.items():
                            salvar_palpite(nome, int(jid), pal["gols1"], pal["gols2"])
                        trancar(nome)
                        st.session_state.pop(f"confirmar_trancar_{nome}", None)
                        st.success("🔒 Palpites trancados! Boa sorte!")
                        st.rerun()
                with col_nao:
                    if st.button("❌ Cancelar", key=f"confirmar_nao_{nome}", use_container_width=True):
                        st.session_state.pop(f"confirmar_trancar_{nome}", None)
                        st.rerun()
        else:
            st.markdown("### 📋 Seus palpites trancados")
            jogo_map = {str(j["id"]): j for j in JOGOS}
            rows_pal = []
            for jid, pal in sorted(palpites_salvos.items(), key=lambda x: int(x[0])):
                jogo = jogo_map.get(jid)
                if jogo:
                    rows_pal.append({
                        "Data": jogo["data"],
                        "Hora": jogo["hora"],
                        "Jogo": f"{jogo['time1']} × {jogo['time2']}",
                        "Seu palpite": f"{pal['gols1']} × {pal['gols2']}",
                    })
            if rows_pal:
                st.dataframe(pd.DataFrame(rows_pal), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# ABA ADMIN
# ─────────────────────────────────────────────────────────────────────────────
with abas[-1]:
    st.subheader("🔧 Painel do Administrador")
    st.caption("Use esta aba para registrar os resultados reais dos jogos.")

    # senha simples
    senha = st.text_input("Senha do admin", type="password", key="admin_senha")
    SENHA_CORRETA = "doutrinadores2026"  # troque aqui se quiser

    if senha != SENHA_CORRETA:
        st.warning("🔐 Digite a senha para acessar o painel.")
        st.stop()

    st.success("✅ Acesso liberado!")

    st.divider()
    st.subheader("📝 Registrar / atualizar resultado")

    jogo_opcoes = {f"#{j['id']} | {j['data']} {j['hora']} | {j['time1']} × {j['time2']}": j for j in JOGOS}
    jogo_sel_str = st.selectbox("Selecione o jogo", list(jogo_opcoes.keys()), key="admin_jogo")
    jogo_sel = jogo_opcoes[jogo_sel_str]

    resultados = carregar_resultados()
    res_existente = resultados.get(str(jogo_sel["id"]), {"gols1": 0, "gols2": 0})

    ac1, ac2, ac3, ac4, ac5 = st.columns([3, 1, 0.5, 1, 3])
    with ac1:
        st.markdown(f"**{jogo_sel['time1']}**")
    with ac2:
        rg1 = st.number_input("G1", 0, 30, value=res_existente["gols1"], key="admin_g1", label_visibility="collapsed")
    with ac3:
        st.markdown("<p style='text-align:center;font-size:1.3rem;margin-top:4px'>×</p>", unsafe_allow_html=True)
    with ac4:
        rg2 = st.number_input("G2", 0, 30, value=res_existente["gols2"], key="admin_g2", label_visibility="collapsed")
    with ac5:
        st.markdown(f"**{jogo_sel['time2']}**")

    ca, cb = st.columns(2)
    with ca:
        if st.button("✅ Salvar resultado", use_container_width=True):
            salvar_resultado(jogo_sel["id"], int(rg1), int(rg2))
            st.success(f"Resultado salvo: {jogo_sel['time1']} {rg1} × {rg2} {jogo_sel['time2']}")
            st.rerun()
    with cb:
        if st.button("🗑️ Remover resultado", use_container_width=True):
            remover_resultado(jogo_sel["id"])
            st.warning("Resultado removido.")
            st.rerun()

    st.divider()
    st.subheader("🎯 Pontuação bônus (manual)")
    st.caption("Use para ajustar pontos de jogos anteriores que não foram registrados automaticamente.")

    from dados import carregar_bonus, salvar_bonus
    bonus_atual = carregar_bonus()

    for p in PARTICIPANTES:
        col_nome, col_pts, col_btn = st.columns([3, 2, 1])
        with col_nome:
            st.markdown(f"**{p}**")
        with col_pts:
            novo_bonus = st.number_input(
                "Bônus", min_value=0, max_value=999,
                value=int(bonus_atual.get(p, 0)),
                key=f"bonus_{p}",
                label_visibility="collapsed",
            )
        with col_btn:
            if st.button("💾", key=f"btn_bonus_{p}"):
                salvar_bonus(p, novo_bonus)
                st.success(f"Salvo!")
                st.rerun()

    st.divider()
    st.subheader("🔓 Destrancar participante")
    part_dest = st.selectbox("Participante", PARTICIPANTES, key="admin_dest")
    if st.button("🔓 Destrancar", key="btn_dest"):
        destrancar(part_dest)
        st.success(f"{part_dest} destrancado.")

    st.divider()
    st.subheader("📊 Status atual dos palpites")
    from dados import carregar_palpites
    pals = carregar_palpites()
    status_rows = []
    for p in PARTICIPANTES:
        info = pals.get(p, {})
        status_rows.append({
            "Participante": p,
            "Palpites salvos": len(info.get("palpites", {})),
            "Trancado": "✅ Sim" if info.get("trancado") else "❌ Não",
        })
    st.dataframe(pd.DataFrame(status_rows), use_container_width=True, hide_index=True)
