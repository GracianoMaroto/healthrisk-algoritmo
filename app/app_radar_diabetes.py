"""
Aplicação Executiva B2B — Radar Preditivo de Vulnerabilidade ao Diabetes (Bloco 3).
Design inspirado no estilo Glucomate / Apple Health (cards brancos arredondados,
medidor circular em arco SVG, barras visuais de faixas clínicas e preenchimento
100% intuitivo com Horas + Minutos, faixas de renda em R$ e níveis claros de escolaridade).
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import joblib
import numpy as np
import pandas as pd
import streamlit as st

from src.features import FEATURES_MODELO_X, VARIAVEIS_BLOQUEADAS_VAZAMENTO
from src.monotonia_clinica import aplicar_monotonia_clinica, carregar_treino_referencia

PROCESSED_DIR = ROOT_DIR / "data" / "processed"
MODELS_DIR = ROOT_DIR / "models"
FIGURES_DIR = ROOT_DIR / "reports" / "figures"
TABLES_DIR = ROOT_DIR / "reports" / "tables"

st.set_page_config(
    page_title="Radar Preditivo de Diabetes | Inteligência Preventiva",
    page_icon="💚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==============================================================================
# CSS ESTILO GLUCOMATE / APPLE HEALTH (CLEAN, MODERNO E INTUITIVO)
# ==============================================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .stApp {
        background: linear-gradient(180deg, #E6F4F3 0%, #F4F9F9 35%, #F8FAFC 100%);
    }
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2.5rem !important;
        max-width: 1380px !important;
    }

    /* Header estilo Glucomate Teal */
    .gluco-header {
        background: linear-gradient(135deg, #0D9488 0%, #0F766E 100%);
        border-radius: 24px;
        padding: 24px 32px;
        color: #FFFFFF;
        box-shadow: 0 12px 28px rgba(13, 148, 136, 0.20);
        margin-bottom: 22px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
    }
    .gluco-header-title {
        font-size: 1.75rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0;
        color: #FFFFFF;
    }
    .gluco-header-sub {
        font-size: 0.92rem;
        color: #CCFBF1;
        margin-top: 4px;
        font-weight: 500;
    }
    .gluco-pill-top {
        background: rgba(255, 255, 255, 0.16);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.28);
        color: #FFFFFF;
        padding: 8px 16px;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 700;
    }

    /* Cards estilo Apple Health / Glucomate */
    .gluco-card {
        background: #FFFFFF;
        border-radius: 22px;
        padding: 22px 24px;
        box-shadow: 0 6px 20px rgba(15, 23, 42, 0.05);
        border: 1px solid #E2E8F0;
        margin-bottom: 16px;
    }
    .gluco-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
    }
    .gluco-card-title {
        font-size: 1.02rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.01em;
    }
    .gluco-tag {
        font-size: 0.73rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 999px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .tag-teal { background: #CCFBF1; color: #0F766E; }
    .tag-amber { background: #FEF3C7; color: #B45309; }
    .tag-red { background: #FEE2E2; color: #B91C1C; }
    .tag-green { background: #D1FAE5; color: #047857; }

    /* Pílulas de resumo amigável dentro dos formulários */
    .helper-pill {
        background: #F0FDFA;
        border: 1px solid #99F6E4;
        border-radius: 12px;
        padding: 10px 14px;
        font-size: 0.84rem;
        color: #0F766E;
        font-weight: 600;
        margin-top: 6px;
        margin-bottom: 10px;
    }
    .helper-pill-warn {
        background: #FFFBEB;
        border: 1px solid #FDE68A;
        border-radius: 12px;
        padding: 10px 14px;
        font-size: 0.84rem;
        color: #B45309;
        font-weight: 600;
        margin-top: 6px;
        margin-bottom: 10px;
    }

    /* Barras de leitura estilo "Reading Ranges" do Glucomate */
    .range-row {
        padding: 10px 0;
        border-bottom: 1px solid #F1F5F9;
    }
    .range-row:last-child {
        border-bottom: none;
    }
    .range-top {
        display: flex;
        justify-content: space-between;
        font-size: 0.86rem;
        font-weight: 600;
        color: #1E293B;
        margin-bottom: 5px;
    }
    .range-track {
        width: 100%;
        height: 8px;
        background: #E2E8F0;
        border-radius: 999px;
        overflow: hidden;
    }
    .range-fill {
        height: 100%;
        border-radius: 999px;
    }

    /* Abas mais elegantes */
    button[data-baseweb="tab"] {
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        padding: 10px 18px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def carregar_modelos():
    lr = joblib.load(MODELS_DIR / "logistic_regression.joblib")
    X_tr, y_tr = carregar_treino_referencia()
    aplicar_monotonia_clinica(lr, X_tr, y_tr)
    return {
        "Random Forest": joblib.load(MODELS_DIR / "random_forest.joblib"),
        "Regressão Logística": lr,
        "Árvore de Decisão": joblib.load(MODELS_DIR / "decision_tree.joblib"),
    }


@st.cache_data
def carregar_dados():
    df_an = pd.read_parquet(PROCESSED_DIR / "analytic.parquet")
    df_uf = pd.read_parquet(PROCESSED_DIR / "territorial_uf.parquet")
    metricas = json.loads((PROCESSED_DIR / "model_metrics.json").read_text(encoding="utf-8"))
    limpeza = json.loads((PROCESSED_DIR / "relatorio_qualidade_limpeza.json").read_text(encoding="utf-8"))
    df_imp = pd.read_csv(TABLES_DIR / "importancia_e_odds_modelos.csv")
    return df_an, df_uf, metricas, limpeza, df_imp


def renderizar_medidor_arco_svg(
    prob: float,
    titulo_topo: str,
    subtitulo_topo: str,
    rotulo_faixa: str,
    cor_hex: str,
    cor_fundo_badge: str,
    detalhe_rodape: str,
    rotulo_modelo: str = "Regressão Logística",
) -> str:
    """Gera um medidor em arco SVG idêntico ao aplicativo Glucomate (Today / Most Recent)."""
    pct = max(0.0, min(100.0, prob * 100.0))
    # Arco de 260 graus (raio = 76, comprimento útil = 345)
    comprimento_total = 345.0
    preenchido = (pct / 100.0) * comprimento_total
    return f"""
    <div class="gluco-card" style="text-align:center; padding: 22px 20px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <span style="font-size:1.05rem; font-weight:800; color:#0F172A;">{titulo_topo}</span>
            <span style="background:{cor_fundo_badge}; color:{cor_hex}; font-size:0.74rem; font-weight:800; padding:4px 10px; border-radius:999px;">
                {rotulo_faixa}
            </span>
        </div>
        <div style="text-align:left; font-size:0.80rem; color:#64748B; margin-bottom:8px;">{subtitulo_topo}</div>
        <div style="position:relative; width:210px; height:175px; margin:0 auto;">
            <svg viewBox="0 0 200 175" width="210" height="175">
                <!-- Trilho cinza suave -->
                <path d="M 35 148 A 76 76 0 1 1 165 148"
                      fill="none" stroke="#E2E8F0" stroke-width="16" stroke-linecap="round"/>
                <!-- Arco colorido dinâmico -->
                <path d="M 35 148 A 76 76 0 1 1 165 148"
                      fill="none" stroke="{cor_hex}" stroke-width="16" stroke-linecap="round"
                      stroke-dasharray="{preenchido:.1f} 500"/>
            </svg>
            <div style="position:absolute; top:56px; left:0; right:0; text-align:center;">
                <div style="font-size:2.35rem; font-weight:800; color:#0F172A; line-height:1.05;">{pct:.1f}%</div>
                <div style="font-size:0.78rem; font-weight:700; color:#64748B; margin-top:3px;">SCORE DE RISCO</div>
                <div style="font-size:0.72rem; color:{cor_hex}; font-weight:700; margin-top:2px;">{rotulo_modelo}</div>
            </div>
        </div>
        <div style="background:#F8FAFC; border-radius:12px; padding:10px 12px; font-size:0.81rem; color:#334155; font-weight:600; border:1px solid #E2E8F0;">
            {detalhe_rodape}
        </div>
    </div>
    """


modelos = carregar_modelos()
df_analytic, df_terr, metricas, rel_limpeza, df_imp = carregar_dados()
params_dieta = metricas["parametros_indice_dieta_treino"]
limiares_rf = metricas["limiares_tercis_probabilidade_rf"]

# Cabeçalho Principal Estilo Glucomate
st.markdown(
    """
    <div class="gluco-header">
        <div>
            <div class="gluco-header-title">💚 Radar Preditivo de Diabetes</div>
            <div class="gluco-header-sub">
                Plataforma Inteligente de Triagem Preventiva & Simulação Clínica • UNEX Sistemas de Informação (Bloco 3)
            </div>
        </div>
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
            <span class="gluco-pill-top">🛡️ Zero Exames Glicêmicos (Sem Vazamento)</span>
            <span class="gluco-pill-top">🎯 Recall: 86,1% | VPN: 94,9%</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

aba1, aba2, aba3, aba4 = st.tabs([
    "🎯 1. Avaliador de Risco & Simulador What-If",
    "📊 2. Painel da Carteira (5.131 Adultos)",
    "🗺️ 3. Mapa Brasil 27 UFs (IBGE + DATASUS)",
    "🔬 4. Auditoria dos Modelos & Segurança",
])

# ==============================================================================
# ABA 1: SIMULADOR INDIVIDUAL DE FÁCIL PREENCHIMENTO + MEDIDORES GLUCOMATE
# ==============================================================================
with aba1:
    # Barra rápida de perfis prontos para demonstração em sala
    col_p1, col_p2 = st.columns([2.2, 1.8])
    with col_p1:
        preset = st.selectbox(
            "⚡ Escolha um Paciente-Exemplo para testar rápido (ou altere qualquer campo abaixo):",
            [
                "🔴 Perfil 1 — Sr. Carlos (58 anos, sedentário, 9h sentado/dia e cintura abdominal elevada)",
                "🟠 Perfil 2 — Marcelo (46 anos, treina 3x/semana, mas passa 10h sentado no escritório + fast-food)",
                "🟢 Perfil 3 — Mariana (29 anos, ativa, alimentação rica em fibras e apenas 4h sentada/dia)",
            ],
        )
    with col_p2:
        st.markdown(
            "<div class='helper-pill' style='margin-top:26px;'>"
            "💡 <b>Preenchimento Simplificado:</b> Informe tempos em <b>Horas e Minutos</b> e renda em <b>Reais (R$)</b>. "
            "O sistema converte tudo automaticamente para o modelo científico!"
            "</div>",
            unsafe_allow_html=True,
        )

    # Valores iniciais amigáveis conforme o perfil escolhido
    if "Perfil 1" in preset:
        p_id, p_sex, p_esc_idx, p_renda_idx, p_ins_idx = 58, 0, 1, 1, 1
        p_dias_ex, p_h_ex, p_m_ex, p_int_idx = 1, 0, 35, 0
        p_h_sent, p_m_sent = 9, 0
        p_alt, p_peso, p_cint, p_pa_idx, p_hdl, p_hf_idx = 170, 96, 112, 1, 38, 1
        p_kcal, p_acuc, p_fib, p_sod, p_gsat, p_fast = 2400, 145, 10, 4200, 36, 6
    elif "Perfil 2" in preset:
        p_id, p_sex, p_esc_idx, p_renda_idx, p_ins_idx = 46, 0, 3, 2, 0
        p_dias_ex, p_h_ex, p_m_ex, p_int_idx = 3, 0, 55, 1
        p_h_sent, p_m_sent = 10, 0
        p_alt, p_peso, p_cint, p_pa_idx, p_hdl, p_hf_idx = 175, 86, 99, 0, 46, 1
        p_kcal, p_acuc, p_fib, p_sod, p_gsat, p_fast = 2200, 110, 15, 3600, 29, 5
    else:
        p_id, p_sex, p_esc_idx, p_renda_idx, p_ins_idx = 29, 1, 4, 3, 0
        p_dias_ex, p_h_ex, p_m_ex, p_int_idx = 5, 1, 10, 1
        p_h_sent, p_m_sent = 4, 0
        p_alt, p_peso, p_cint, p_pa_idx, p_hdl, p_hf_idx = 165, 61, 74, 0, 62, 0
        p_kcal, p_acuc, p_fib, p_sod, p_gsat, p_fast = 1950, 60, 28, 1900, 18, 1

    # Container para exibir os medidores Glucomate NO TOPO (atualizados em tempo real após ler os inputs)
    container_resultados_topo = st.container()

    st.markdown("### 📝 Dados do Paciente (Preenchimento Guiado e Intuitivo)")

    col_f1, col_f2 = st.columns(2)

    # ------------------------------------------------------------------
    # CARD 1: PERFIL SOCIAL & ROTINA DE MOVIMENTO (COM HORAS E MINUTOS!)
    # ------------------------------------------------------------------
    with col_f1:
        with st.container(border=True):
            st.markdown("#### 👤 1. Perfil Pessoal e Socioeconômico")
            c_id, c_sx = st.columns([1.2, 1])
            with c_id:
                idade = st.slider("Idade do Paciente (anos)", 18, 80, p_id)
            with c_sx:
                sexo_str = st.radio("Sexo Biológico", ["Masculino", "Feminino"], index=p_sex, horizontal=True)
                sexo = 1 if sexo_str == "Masculino" else 2

            opcoes_escolaridade = [
                ("Ensino Fundamental Incompleto (até 8º ano)", 1),
                ("Fundamental Completo ou Médio Incompleto", 2),
                ("Ensino Médio Completo", 3),
                ("Superior Incompleto ou Curso Técnico", 4),
                ("Ensino Superior Completo / Pós-Graduação", 5),
            ]
            esc_escolhida = st.selectbox(
                "🎓 Nível de Escolaridade:",
                options=opcoes_escolaridade,
                index=p_esc_idx,
                format_func=lambda x: x[0],
            )
            escolaridade = esc_escolhida[1]

            opcoes_renda = [
                ("Até R$ 750 por pessoa da família (Alta Vulnerabilidade)", 0.8),
                ("De R$ 750 a R$ 1.500 por pessoa (Baixa Renda)", 1.3),
                ("De R$ 1.500 a R$ 3.000 por pessoa (Renda Média)", 2.6),
                ("De R$ 3.000 a R$ 5.500 por pessoa (Renda Confortável)", 3.9),
                ("Acima de R$ 5.500 por pessoa (Alta Renda)", 4.8),
            ]
            renda_escolhida = st.selectbox(
                "💰 Faixa de Renda Mensal Familiar (por pessoa):",
                options=opcoes_renda,
                index=p_renda_idx,
                format_func=lambda x: x[0],
                help="Converte automaticamente para o indicador socioeconômico PIR (Razão Renda/Pobreza) utilizado pelo modelo.",
            )
            pir = renda_escolhida[1]

            inseg_alim = st.selectbox(
                "🛒 Faltou dinheiro para comprar alimentos saudáveis nos últimos 12 meses?",
                options=[0, 1],
                index=p_ins_idx,
                format_func=lambda x: "Não — Família com segurança alimentar plena" if x == 0 else "Sim — Houve insegurança alimentar domiciliar",
            )

        with st.container(border=True):
            st.markdown("#### 🏃 2. Atividade Física e Tempo Sentado (em Horas e Minutos)")

            st.markdown("**A) Exercícios Físicos, Caminhada ou Esportes na Semana:**")
            c_d, c_h, c_m = st.columns([1.2, 1, 1])
            with c_d:
                dias_treino = st.selectbox(
                    "Dias por semana:",
                    options=[0, 1, 2, 3, 4, 5, 6, 7],
                    index=p_dias_ex,
                    format_func=lambda d: "Nenhum dia (0x)" if d == 0 else f"{d} {'dia' if d == 1 else 'dias'}/semana",
                )
            with c_h:
                horas_treino = st.selectbox(
                    "Horas por dia:",
                    options=[0, 1, 2, 3, 4],
                    index=p_h_ex,
                    format_func=lambda h: f"{h} h",
                    disabled=(dias_treino == 0),
                )
            with c_m:
                opcoes_min_treino = [0, 10, 15, 20, 30, 35, 40, 45, 50, 55]
                idx_m_tr = opcoes_min_treino.index(p_m_ex) if p_m_ex in opcoes_min_treino else 4
                min_treino = st.selectbox(
                    "Minutos por dia:",
                    options=opcoes_min_treino,
                    index=idx_m_tr,
                    format_func=lambda m: f"{m:02d} min",
                    disabled=(dias_treino == 0),
                )

            opcoes_intensidade = [
                ("Leve (Caminhada leve, deslocamento a pé — 3,3 METs)", 3.3),
                ("Moderada (Academia, caminhada rápida, bicicleta leve — 4,0 METs)", 4.0),
                ("Intensa (Corrida, futebol, crossfit, natação forte — 8,0 METs)", 8.0),
            ]
            intensidade_escolhida = st.selectbox(
                "Intensidade principal do exercício:",
                options=opcoes_intensidade,
                index=p_int_idx,
                format_func=lambda x: x[0],
                disabled=(dias_treino == 0),
            )

            duracao_diaria_min = (horas_treino * 60) + min_treino if dias_treino > 0 else 0
            total_min_semana = dias_treino * duracao_diaria_min
            h_sem_tot = total_min_semana // 60
            m_sem_tot = total_min_semana % 60
            met_sem = round(total_min_semana * intensidade_escolhida[1])

            if met_sem >= 600:
                st.markdown(
                    f"<div class='helper-pill'>✅ <b>Tempo Total de Exercício:</b> {h_sem_tot}h {m_sem_tot:02d}min por semana "
                    f"(<b>{met_sem} MET-min/sem</b>) — <b>Cumpre a meta da OMS!</b></div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div class='helper-pill-warn'>⚠️ <b>Tempo Total de Exercício:</b> {h_sem_tot}h {m_sem_tot:02d}min por semana "
                    f"(<b>{met_sem} MET-min/sem</b>) — Abaixo da meta recomendada pela OMS (2h 30min moderadas / 600 MET-min).</div>",
                    unsafe_allow_html=True,
                )

            st.markdown("**B) Tempo Sentado ou Deitado Acordado por Dia (Trabalho, Sofá, Trânsito, Celular):**")
            cs_h, cs_m = st.columns(2)
            with cs_h:
                opcoes_h_sent = list(range(1, 17))
                idx_hs = opcoes_h_sent.index(p_h_sent) if p_h_sent in opcoes_h_sent else 7
                horas_sentado = st.selectbox(
                    "Horas sentado por dia:",
                    options=opcoes_h_sent,
                    index=idx_hs,
                    format_func=lambda h: f"{h} {'hora' if h == 1 else 'horas'}",
                )
            with cs_m:
                opcoes_m_sent = [0, 15, 30, 45]
                idx_ms = opcoes_m_sent.index(p_m_sent) if p_m_sent in opcoes_m_sent else 0
                minutos_sentado_extra = st.selectbox(
                    "Minutos adicionais:",
                    options=opcoes_m_sent,
                    index=idx_ms,
                    format_func=lambda m: f"{m:02d} minutos",
                )

            min_sentado = (horas_sentado * 60) + minutos_sentado_extra
            if min_sentado >= 480:
                st.markdown(
                    f"<div class='helper-pill-warn'>🪑 <b>Total Sentado: {horas_sentado}h {minutos_sentado_extra:02d}min por dia</b> "
                    f"({min_sentado} min/dia) — <b>Sedentarismo Elevado (≥ 8h/dia)</b></div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div class='helper-pill'>🪑 <b>Total Sentado: {horas_sentado}h {minutos_sentado_extra:02d}min por dia</b> "
                    f"({min_sentado} min/dia) — Dentro da faixa protetora (&lt; 8h/dia)</div>",
                    unsafe_allow_html=True,
                )

    # ------------------------------------------------------------------
    # CARD 2: MEDIDAS DO CORPO (CLÍNICO) & HÁBITOS ALIMENTARES GUIADOS
    # ------------------------------------------------------------------
    with col_f2:
        with st.container(border=True):
            st.markdown("#### 🩺 3. Medidas Corporais e Triagem Simples (Sem Exame de Glicose)")
            cm1, cm2, cm3 = st.columns(3)
            with cm1:
                altura = st.number_input("Altura (em cm)", min_value=135, max_value=210, value=p_alt, step=1, help="Ex: 1,70m = 170 cm")
            with cm2:
                peso = st.number_input("Peso atual (em kg)", min_value=35, max_value=180, value=p_peso, step=1)
            with cm3:
                cintura = st.number_input("Cintura no umbigo (cm)", min_value=55, max_value=165, value=p_cint, step=1, help="Medida com fita métrica na altura do umbigo")

            imc_calc = peso / ((altura / 100.0) ** 2)
            rce_calc = cintura / float(altura)
            cor_rce = "helper-pill-warn" if rce_calc >= 0.50 else "helper-pill"
            msg_rce = "Acima da metade da altura (Alerta Visceral ≥ 0,50)" if rce_calc >= 0.50 else "Dentro do ideal (< 0,50 da altura)"
            st.markdown(
                f"<div class='{cor_rce}'>📏 <b>Cálculo Automático:</b> IMC = <b>{imc_calc:.1f} kg/m²</b>  |  "
                f"Relação Cintura/Altura = <b>{rce_calc:.2f}</b> ({msg_rce})</div>",
                unsafe_allow_html=True,
            )

            cc1, cc2 = st.columns(2)
            with cc1:
                pressao_alta = st.selectbox(
                    "❤️ Possui Pressão Alta (≥ 140/90 mmHg)?",
                    options=[0, 1],
                    index=p_pa_idx,
                    format_func=lambda x: "Não (Pressão Normal)" if x == 0 else "Sim (Pressão Alta / Hipertenso)",
                )
            with cc2:
                hist_fam = st.selectbox(
                    "🧬 Pais ou irmãos têm Diabetes?",
                    options=[0, 1],
                    index=p_hf_idx,
                    format_func=lambda x: "Não possui histórico familiar" if x == 0 else "Sim (Histórico em 1º grau)",
                )

            hdl = st.slider(
                "🩸 Colesterol Bom — HDL (mg/dL) [Se não souber, mantenha 50 mg/dL]:",
                min_value=20,
                max_value=100,
                value=p_hdl,
                step=1,
                help="O colesterol HDL acima de 50 mg/dL atua como fator protetor metabólico.",
            )

        with st.container(border=True):
            st.markdown("#### 🥗 4. Alimentação no Dia a Dia (Estimativa Prática)")
            ref_pronta = st.slider(
                "🍔 Quantas refeições fora de casa, lanches ou delivery faz por semana?",
                min_value=0,
                max_value=21,
                value=p_fast,
                step=1,
                help="Inclui fast-food, restaurantes, salgados e refeições prontas na semana.",
            )

            ca1, ca2 = st.columns(2)
            with ca1:
                acucar = st.slider(
                    "🍬 Açúcar e Doces por dia (g/dia)",
                    0, 260, p_acuc, 5,
                    help="Referência: 1 lata de refrigerante = 35g. Meta ideal OMS: até 50g/dia.",
                )
                fibra = st.slider(
                    "🥦 Fibras: Frutas, Aveia, Feijão (g/dia)",
                    0, 50, p_fib, 1,
                    help="Meta protetora: 25g a 30g/dia (ex: 2 frutas + 1 concha de feijão + salada).",
                )
            with ca2:
                sodio = st.slider(
                    "🧂 Consumo de Sal / Sódio (mg/dia)",
                    800, 6500, p_sod, 100,
                    help="Meta saudável OMS: até 2.000 mg/dia. Embutidos e temperos prontos elevam para >3.500 mg.",
                )
                gord_sat = st.slider(
                    "🥩 Gordura Saturada / Frituras (g/dia)",
                    5, 70, p_gsat, 1,
                    help="Meta saudável: até 20g/dia. Carnes gordas, queijos amarelos e frituras elevam o valor.",
                )

            kcal = st.slider(
                "🔥 Calorias Diárias Totais Aproximadas (kcal/dia) [Média adulto: 2.000 kcal]",
                1000, 4000, p_kcal, 50,
            )

    # ==============================================================================
    # CÁLCULO DO VETOR CIENTÍFICO DE 19 VARIÁVEIS E SIMULAÇÃO WHAT-IF
    # ==============================================================================
    def montar_vetor_entrada(
        _idade, _sexo, _esc, _pir, _ins, _kcal, _acuc, _fib, _sod, _gsat, _fast,
        _met, _sent, _alt, _peso, _cint, _pa, _hdl, _hf
    ) -> pd.DataFrame:
        imc_val = _peso / ((_alt / 100.0) ** 2)
        rce_val = _cint / float(_alt)
        dens_ac = (_acuc / float(_kcal)) * 1000.0
        dens_fb = (_fib / float(_kcal)) * 1000.0
        exc_sod = 1.0 if _sod >= 2300 else 0.0

        z_fb = (_fib - params_dieta["fibra_g_dia"]["media_treino"]) / params_dieta["fibra_g_dia"]["std_treino"]
        z_ac = (_acuc - params_dieta["acucar_g_dia"]["media_treino"]) / params_dieta["acucar_g_dia"]["std_treino"]
        z_so = (_sod - params_dieta["sodio_mg_dia"]["media_treino"]) / params_dieta["sodio_mg_dia"]["std_treino"]
        z_gs = (_gsat - params_dieta["gordura_sat_g_dia"]["media_treino"]) / params_dieta["gordura_sat_g_dia"]["std_treino"]
        iqd = (z_fb - z_ac - z_so - z_gs) / 4.0

        return pd.DataFrame([{
            "idade_anos": float(_idade),
            "sexo": float(_sexo),
            "escolaridade_ord": float(_esc),
            "razao_renda_pobreza": float(_pir),
            "inseguranca_alimentar": float(_ins),
            "densidade_acucar": float(dens_ac),
            "densidade_fibra": float(dens_fb),
            "excesso_sodio": float(exc_sod),
            "indice_qualidade_dieta": float(iqd),
            "refeicao_pronta": float(_fast),
            "met_min_semana": float(_met),
            "cumpre_oms_150": 1.0 if _met >= 600 else 0.0,
            "minutos_sentado": float(_sent),
            "sedentarismo_alto": 1.0 if _sent >= 480 else 0.0,
            "imc": float(imc_val),
            "razao_cintura_estatura": float(rce_val),
            "pressao_alta": float(_pa),
            "hdl": float(_hdl),
            "historico_familiar_diabetes": float(_hf),
        }])[FEATURES_MODELO_X]

    X_atual = montar_vetor_entrada(
        idade, sexo, escolaridade, pir, inseg_alim, kcal, acucar, fibra, sodio, gord_sat, ref_pronta,
        met_sem, min_sentado, altura, peso, cintura, pressao_alta, hdl, hist_fam
    )

    # Score operacional: LR com monotonia clínica. O RF observacional inverte
    # hábitos (ex.: exercício 7% → 8%) por causalidade reversa do NHANES.
    prob_lr = float(modelos["Regressão Logística"].predict_proba(X_atual)[0, 1])
    prob_rf = float(modelos["Random Forest"].predict_proba(X_atual)[0, 1])
    prob_dt = float(modelos["Árvore de Decisão"].predict_proba(X_atual)[0, 1])
    prob_atual = prob_lr

    # Simulação What-If (paciente cumprindo 3h/sem de exercício, máx 5h sentado, dieta rica em fibras e -6cm cintura)
    X_intervencao = montar_vetor_entrada(
        idade, sexo, escolaridade, pir, inseg_alim, kcal,
        min(acucar, 45), max(fibra, 28), min(sodio, 1900), min(gord_sat, 16), min(ref_pronta, 1),
        max(met_sem, 1200), min(min_sentado, 300),
        altura, max(peso - 5, 50), max(cintura - 6, 70), 0, max(hdl, 55), hist_fam
    )
    prob_pos = float(modelos["Regressão Logística"].predict_proba(X_intervencao)[0, 1])
    reducao_relativa = ((prob_atual - prob_pos) / prob_atual * 100.0) if prob_atual > 0 else 0.0

    if prob_atual <= limiares_rf["tercil_inferior_baixo_moderado"]:
        rotulo_f, cor_f, bg_f = "BAIXO RISCO", "#10B981", "#D1FAE5"
        rec_acao = "Manter acompanhamento digital anual e incentivo à prática regular de atividade física."
    elif prob_atual <= limiares_rf["tercil_superior_moderado_alto"]:
        rotulo_f, cor_f, bg_f = "RISCO MODERADO", "#F59E0B", "#FEF3C7"
        rec_acao = "Incluir em trilha preventiva de reeducação alimentar, metas de movimento e reavaliar em 6 meses."
    else:
        rotulo_f, cor_f, bg_f = "ALTO RISCO", "#EF4444", "#FEE2E2"
        rec_acao = "Prioridade Clínica: solicitar exame laboratorial (HbA1c e Glicemia de Jejum) e iniciar acompanhamento ativo."

    if prob_pos <= limiares_rf["tercil_inferior_baixo_moderado"]:
        rotulo_pos, cor_pos, bg_pos = "BAIXO RISCO", "#10B981", "#D1FAE5"
    elif prob_pos <= limiares_rf["tercil_superior_moderado_alto"]:
        rotulo_pos, cor_pos, bg_pos = "RISCO MODERADO", "#F59E0B", "#FEF3C7"
    else:
        rotulo_pos, cor_pos, bg_pos = "ALTO RISCO", "#EF4444", "#FEE2E2"

    # Preenche os 3 cards estilo Glucomate no topo da página!
    with container_resultados_topo:
        g1, g2, g3 = st.columns([1.05, 1.05, 1.25])
        with g1:
            st.markdown(
                renderizar_medidor_arco_svg(
                    prob=prob_atual,
                    titulo_topo="Diagnóstico Preditivo Atual",
                    subtitulo_topo="Estimativa sem exames de sangue glicêmicos",
                    rotulo_faixa=rotulo_f,
                    cor_hex=cor_f,
                    cor_fundo_badge=bg_f,
                    detalhe_rodape=f"Consenso observacional: RF <b>{prob_rf*100:.1f}%</b>  •  Árvore <b>{prob_dt*100:.1f}%</b>",
                ),
                unsafe_allow_html=True,
            )
        with g2:
            st.markdown(
                renderizar_medidor_arco_svg(
                    prob=prob_pos,
                    titulo_topo="Simulação What-If (Com Prevenção)",
                    subtitulo_topo="Se atingir 3h/sem de treino + máx 5h sentado + fibras",
                    rotulo_faixa=rotulo_pos,
                    cor_hex=cor_pos,
                    cor_fundo_badge=bg_pos,
                    detalhe_rodape=f"📉 Impacto Preventivo: <b>-{reducao_relativa:.1f}% de redução relativa no risco</b>",
                ),
                unsafe_allow_html=True,
            )
        with g3:
            # Card "Reading Ranges" idêntico ao Glucomate!
            pct_rce = min(100, int((rce_calc / 0.75) * 100))
            cor_b_rce = "#EF4444" if rce_calc >= 0.53 else ("#F59E0B" if rce_calc >= 0.49 else "#10B981")

            pct_mov = min(100, int((met_sem / 1500.0) * 100))
            cor_b_mov = "#10B981" if met_sem >= 600 else ("#F59E0B" if met_sem >= 300 else "#EF4444")

            pct_sent = min(100, int((min_sentado / 720.0) * 100))
            cor_b_sent = "#EF4444" if min_sentado >= 480 else ("#F59E0B" if min_sentado >= 360 else "#10B981")

            pct_fib = min(100, int((fibra / 35.0) * 100))
            cor_b_fib = "#10B981" if fibra >= 25 else ("#F59E0B" if fibra >= 15 else "#EF4444")

            st.markdown(
                f"""
                <div class="gluco-card" style="padding: 20px 22px;">
                    <div class="gluco-card-header">
                        <span class="gluco-card-title">📊 Raio-X dos Indicadores do Paciente</span>
                        <span class="gluco-tag tag-teal">Tempo Real</span>
                    </div>
                    <div class="range-row">
                        <div class="range-top">
                            <span>📏 Cintura / Altura (Ideal &lt; 0,50)</span>
                            <span style="color:{cor_b_rce}; font-weight:800;">{rce_calc:.2f} (IMC {imc_calc:.1f})</span>
                        </div>
                        <div class="range-track"><div class="range-fill" style="width:{pct_rce}%; background:{cor_b_rce};"></div></div>
                    </div>
                    <div class="range-row">
                        <div class="range-top">
                            <span>🏃 Exercício Semanal (Meta ≥ 2h30 / 600 MET)</span>
                            <span style="color:{cor_b_mov}; font-weight:800;">{h_sem_tot}h {m_sem_tot:02d}min ({met_sem} MET)</span>
                        </div>
                        <div class="range-track"><div class="range-fill" style="width:{pct_mov}%; background:{cor_b_mov};"></div></div>
                    </div>
                    <div class="range-row">
                        <div class="range-top">
                            <span>🪑 Tempo Sentado por Dia (Ideal &lt; 8h)</span>
                            <span style="color:{cor_b_sent}; font-weight:800;">{horas_sentado}h {minutos_sentado_extra:02d}min / dia</span>
                        </div>
                        <div class="range-track"><div class="range-fill" style="width:{pct_sent}%; background:{cor_b_sent};"></div></div>
                    </div>
                    <div class="range-row">
                        <div class="range-top">
                            <span>🥦 Consumo de Fibras (Meta ≥ 25g/dia)</span>
                            <span style="color:{cor_b_fib}; font-weight:800;">{fibra} g/dia • Açúcar: {acucar}g</span>
                        </div>
                        <div class="range-track"><div class="range-fill" style="width:{pct_fib}%; background:{cor_b_fib};"></div></div>
                    </div>
                    <div style="margin-top:10px; background:#F0FDFA; border-left:4px solid #0D9488; padding:9px 12px; border-radius:8px; font-size:0.81rem; color:#0F766E;">
                        <b>Conduta Sugerida:</b> {rec_acao}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ==============================================================================
# ABA 2: INTELIGÊNCIA DE CARTEIRA (COORTE NHANES N = 5.131)
# ==============================================================================
with aba2:
    st.markdown("### 📊 Inteligência de Carteira — Coorte Analítica Auditada (n = 5.131 Adultos)")
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f"<div class='gluco-card'><span class='gluco-tag tag-teal'>Universo Real</span>"
            f"<div style='font-size:2.0rem; font-weight:800; color:#0F172A; margin-top:8px;'>{rel_limpeza['n_amostra_analitica_final']:,}</div>"
            f"<div style='font-size:0.84rem; color:#64748B;'>Adultos auditados de {rel_limpeza['n_total_demo_bruto']:,} registros brutos</div></div>",
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"<div class='gluco-card'><span class='gluco-tag tag-amber'>Prevalência na Coorte</span>"
            f"<div style='font-size:2.0rem; font-weight:800; color:#0F172A; margin-top:8px;'>{rel_limpeza['prevalencia_diabetes_amostra_pct']:.2f}%</div>"
            f"<div style='font-size:0.84rem; color:#64748B;'>{rel_limpeza['n_casos_diabetes']} diabéticos vs. {rel_limpeza['n_controles_sem_diabetes']} controles</div></div>",
            unsafe_allow_html=True,
        )
    with k3:
        n_ocultos = rel_limpeza["detalhamento_criterios_alvo"]["casos_ocultos_apenas_exame_sem_autorrelato"]
        pct_ocultos = (n_ocultos / rel_limpeza["n_casos_diabetes"]) * 100
        st.markdown(
            f"<div class='gluco-card'><span class='gluco-tag tag-red'>Ponto Cego Descoberto</span>"
            f"<div style='font-size:2.0rem; font-weight:800; color:#EF4444; margin-top:8px;'>{n_ocultos} ({pct_ocultos:.1f}%)</div>"
            f"<div style='font-size:0.84rem; color:#64748B;'>Não sabiam ter diabetes, mas tinham HbA1c ≥ 6,5%</div></div>",
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            "<div class='gluco-card'><span class='gluco-tag tag-green'>Retorno Comercial (ROI)</span>"
            "<div style='font-size:2.0rem; font-weight:800; color:#0D9488; margin-top:8px;'>73,8% Capturados</div>"
            "<div style='font-size:0.84rem; color:#64748B;'>Triando apenas 1/3 da carteira (Lift de 2,20x)</div></div>",
            unsafe_allow_html=True,
        )

    col_fig1, col_fig2 = st.columns(2)
    with col_fig1:
        st.image(str(FIGURES_DIR / "fig4_estratificacao_faixas_risco.png"), use_container_width=True)
    with col_fig2:
        st.image(str(FIGURES_DIR / "fig5_movimento_e_faixa_etaria.png"), use_container_width=True)

    st.markdown("#### 🗄️ Consultas SQL Executadas no Banco Analítico (`radar_diabetes.db`)")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("**Cruzamento: Perfil de Movimento × Qualidade da Dieta**")
        st.dataframe(pd.read_csv(TABLES_DIR / "sql2_perfis_comportamentais_dieta_movimento.csv"), use_container_width=True)
    with col_t2:
        st.markdown("**Gradiente Socioeconômico (Renda × Insegurança Alimentar)**")
        st.dataframe(pd.read_csv(TABLES_DIR / "sql4_gradiente_socioeconomico_inseguranca.csv"), use_container_width=True)

# ==============================================================================
# ABA 3: PAINEL TERRITORIAL BRASILEIRO (IBGE + DATASUS/CNES)
# ==============================================================================
with aba3:
    st.markdown("### 🗺️ Onde Alocar Equipes no Brasil — Ranking das 27 UFs (IBGE SIDRA + DATASUS)")
    st.markdown(
        "Indicadores oficiais do **IBGE (Censo 2022 e PNS)** combinados com **Internações por Diabetes no SUS (SIH/DATASUS)** "
        "e **Cobertura de Atenção Básica (CNES)** para orientar a expansão regional de programas preventivos."
    )

    f_reg = st.multiselect(
        "Filtrar por Macrorregião Brasileira:",
        options=["N", "NE", "CO", "SE", "S"],
        default=["N", "NE", "CO", "SE", "S"],
    )
    df_uf_filtrado = df_terr[df_terr["regiao"].isin(f_reg)].copy()

    col_uf1, col_uf2 = st.columns([1.15, 1])
    with col_uf1:
        st.image(str(FIGURES_DIR / "fig6_ranking_territorial_uf.png"), use_container_width=True)
    with col_uf2:
        st.markdown("**Tabela Interativa das 27 Unidades da Federação**")
        df_exibir_uf = df_uf_filtrado[[
            "ranking_vulnerabilidade", "uf", "nome_uf", "regiao",
            "indice_contexto_territorial", "prioridade_territorial",
            "internacoes_diabetes_100k", "cobertura_ab",
            "renda_mediana_uf", "prev_diabetes_uf", "pct_insuf_atividade_uf",
        ]].rename(columns={
            "ranking_vulnerabilidade": "Rank",
            "uf": "UF",
            "nome_uf": "Estado",
            "regiao": "Região",
            "indice_contexto_territorial": "Índice Territorial",
            "prioridade_territorial": "Prioridade",
            "internacoes_diabetes_100k": "Internações/100k",
            "cobertura_ab": "Cobertura AB (%)",
            "renda_mediana_uf": "Renda Mediana (R$)",
            "prev_diabetes_uf": "Prevalência (%)",
            "pct_insuf_atividade_uf": "Inatividade (%)",
        })
        st.dataframe(
            df_exibir_uf,
            use_container_width=True,
            height=460,
            hide_index=True,
        )

# ==============================================================================
# ABA 4: AUDITORIA ALGORÍTMICA & DATA LEAKAGE SHIELD
# ==============================================================================
with aba4:
    st.markdown("### 🔬 Validação Científica, Explicabilidade White-Box e Escudo Anti-Vazamento")
    ca1, ca2 = st.columns(2)
    with ca1:
        st.image(str(FIGURES_DIR / "fig1_curvas_roc.png"), use_container_width=True)
    with ca2:
        st.image(str(FIGURES_DIR / "fig3_importancia_e_odds.png"), use_container_width=True)

    st.image(str(FIGURES_DIR / "fig2_matrizes_confusao.png"), use_container_width=True)

    col_b1, col_b2 = st.columns([1.3, 1])
    with col_b1:
        st.markdown("#### 📊 Importância no Random Forest vs. Odds Ratio (Regressão Logística)")
        st.dataframe(df_imp, use_container_width=True, height=340)
    with col_b2:
        st.markdown("#### 🛡️ Escudo Contra Vazamento (`Data Leakage Shield`)")
        st.success(
            "Todas as variáveis de exames de glicose ou uso de medicamentos para diabetes foram **bloqueadas por código** "
            "no vetor preditor X e auditadas por 12 testes automatizados (`pytest: 12/12 PASSED`):"
        )
        st.code("\n".join(VARIAVEIS_BLOQUEADAS_VAZAMENTO), language="text")
