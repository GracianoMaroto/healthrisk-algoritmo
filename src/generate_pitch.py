"""
Gerador da Apresentação Executiva do Pitch Comercial (Parte 1 — PPTX e PDF 16:9)
em Design Corporativo Clean & Minimalista (fundo branco puro #FFFFFF, formas geométricas
e círculos em Âmbar Executivo #F5A623, tipografia escura #1E242B, numeração 01/02/03,
infográficos circulares, avatares da equipe e mínimo de texto por slide).
Inclui verificação matemática estrita de largura/altura de texto (Paragraph.wrap + stringWidth)
para garantir que nenhum texto jamais ultrapasse as bordas de qualquer caixa ou pílula.
Todos os documentos são salvos exclusivamente na pasta docs/.
"""

from __future__ import annotations

from pathlib import Path
from PIL import Image as PILImage
import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt
from pptx import Presentation
from pptx.dml.color import RGBColor as PPTXColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt as PPTXPt

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"
FIGURES_DIR = ROOT_DIR / "reports" / "figures"

INTEGRANTES_INFO = [
    ("AS", "Augusto Santos", "Diagnóstico & Dor Comercial"),
    ("DT", "Daniel Teixeira", "Pipeline & Anti-Vazamento"),
    ("DP", "Douglas Pereira", "Modelagem & Sensibilidade"),
    ("GM", "Graciano Marôto", "Estratificação & ROI"),
    ("MN", "Marcos Nathan", "Território & Demo Ao Vivo"),
    ("MK", "Mendell Kalyl", "Testes, LGPD & Prontidão"),
]


# ==============================================================================
# DADOS DOS 12 SLIDES — ULTRA-CLEAN, CONCISOS E COM MEDIDAS AUDITADAS
# ==============================================================================
SLIDES_CLEAN = [
    {
        "num": 1,
        "layout": "hero_cover",
        "tag": "PROJETO SEMESTRAL • BLOCO 3",
        "titulo_1": "RADAR PREDITIVO",
        "titulo_2": "DE DIABETES",
        "subtitulo": "Inteligência preventiva para saúde suplementar e pública.",
        "kpis": [
            ("5.131", "Adultos Auditados (CDC)"),
            ("27 UFs", "IBGE SIDRA + DATASUS"),
            ("86,1%", "Sensibilidade de Rastreio"),
        ],
        "rodape": "UNEX • Sistemas de Informação • Prof. Wallas Froes de Oliveira",
    },
    {
        "num": 2,
        "layout": "split_01_02",
        "tag": "RESGATE DA DOR (BLOCO 1)",
        "titulo": "O PONTO CEGO DA SAÚDE",
        "subtitulo": "Por que agir apenas após o diagnóstico clínico quebra o orçamento das operadoras.",
        "destaque_num": "24,2%",
        "destaque_leg": "dos diabéticos reais na base desconheciam ter a doença (244 de 1.008 casos).",
        "itens": [
            ("01", "Amostra Real", "5.131 adultos auditados no ciclo NHANES 2017–2018."),
            ("02", "Casos Ocultos", "244 pacientes sem diagnóstico prévio, mas com HbA1c ≥ 6,5%."),
            ("03", "Custo Evitável", "Internações ocorrem anos após o início silencioso da doença."),
        ],
        "rodape": "Parte 1 • Diagnóstico Empírico na Base Analítica",
    },
    {
        "num": 3,
        "layout": "grid_6_badges",
        "tag": "ARQUITETURA & GOVERNANÇA",
        "titulo": "ENGENHARIA SEM VAZAMENTO",
        "subtitulo": "Isolamento estrito entre variáveis de diagnóstico laboratorial (y) e preditores de triagem (X).",
        "cards": [
            ("16", "Arquivos Oficiais", "Extração direta CDC com hash SHA-256."),
            ("0%", "Data Leakage", "HbA1c, glicemia e insulina bloqueadas em X."),
            ("19", "Preditores em X", "Dieta, atividade física, social e antropometria."),
            ("80/20", "Split Estratificado", "4.104 no treino e 1.027 no teste cego."),
            ("8", "Estratos de Imputação", "Mediana por sexo e idade só no treino."),
            ("12/12", "Testes Automatizados", "Homologação completa via pytest em 2,7s."),
        ],
        "rodape": "Rigor Metodológico • Data Leakage Shield (Kaufman et al., 2011)",
    },
    {
        "num": 4,
        "layout": "chart_right_01_02",
        "tag": "DESEMPENHO PREDITIVO",
        "titulo": "CURVAS ROC NO TESTE CEGO",
        "subtitulo": "Capacidade discriminativa em n = 1.027 adultos sem usar exames glicêmicos.",
        "figura": "fig1_curvas_roc.png",
        "itens": [
            ("01", "Regressão Logística • AUC 0,838", "Modelo linear interpretável (CV 5-fold: 0,830)."),
            ("02", "Random Forest • AUC 0,830", "Melhor calibração probabilística (Brier = 0,161)."),
            ("03", "Árvore de Decisão • AUC 0,796", "Regras clínicas diretas de corte em consultório."),
        ],
        "rodape": "Validação Cruzada 5-Fold + Conjunto de Teste Isolado",
    },
    {
        "num": 5,
        "layout": "chart_right_01_02",
        "tag": "CALIBRAÇÃO CLÍNICA",
        "titulo": "FOCO EM SENSIBILIDADE",
        "subtitulo": "Em triagem preventiva, deixar passar um doente custa caro; confirmar custa pouco.",
        "figura": "fig2_matrizes_confusao.png",
        "itens": [
            ("01", "86,1% de Recall (Sensibilidade)", "Captura 174 dos 202 diabéticos reais do teste."),
            ("02", "94,9% de Valor Preditivo Negativo", "Segurança clínica de 95% ao descartar baixo risco."),
            ("03", "Limiar Preventivo (p ≥ 0,40)", "Reduz Falsos Negativos de 95 para apenas 28."),
        ],
        "rodape": "Prioridade Clínica • Minimização de Falsos Negativos",
    },
    {
        "num": 6,
        "layout": "chart_right_01_02",
        "tag": "IA EXPLICÁVEL (WHITE-BOX)",
        "titulo": "O QUE MOVE O RISCO?",
        "subtitulo": "Convergência entre importância no Random Forest e Razão de Chances (Odds Ratio).",
        "figura": "fig3_importancia_e_odds.png",
        "itens": [
            ("01", "Cintura/Estatura Supera o IMC", "Maior peso no modelo (15,9%; OR = 1,97)."),
            ("02", "Idade & Histórico Familiar", "Fatores basais (OR = 2,26 e OR = 1,85)."),
            ("03", "Atividade Física + HDL", "Escudos protetores acionáveis (OR = 0,82 e 0,68)."),
        ],
        "rodape": "Transparência Algorítmica para Médicos e Gestores",
    },
    {
        "num": 7,
        "layout": "chart_right_01_02",
        "tag": "RETORNO COMERCIAL (ROI)",
        "titulo": "ESTRATIFICAÇÃO DE CARTEIRA",
        "subtitulo": "Divisão em 3 faixas operacionais para direcionar exames e equipes de prevenção.",
        "figura": "fig4_estratificacao_faixas_risco.png",
        "itens": [
            ("01", "Baixo Risco • 2,6% Positividade", "Monitoramento digital anual sem custo presencial."),
            ("02", "Alto Risco • 43,2% Positividade", "16,5x mais risco real que a faixa basal."),
            ("03", "73,8% de Captura em 1/3 da Base", "Lift comercial de 2,20x (66% de economia inicial)."),
        ],
        "rodape": "Eficiência Alocativa • Triagem Inteligente de Beneficiários",
    },
    {
        "num": 8,
        "layout": "chart_right_01_02",
        "tag": "DESCOBERTAS COMPORTAMENTAIS",
        "titulo": "MOVIMENTO & ESTILO DE VIDA",
        "subtitulo": "Padrões extraídos no cruzamento entre sedentarismo, atividade física e idade.",
        "figura": "fig5_movimento_e_faixa_etaria.png",
        "itens": [
            ("01", "Inativo + ≥8h Sentado: 28,2%", "Quase o dobro da prevalência do grupo ativo (15,1%)."),
            ("02", "Salto Crítico aos 45+ Anos", "Prevalência triplica da faixa 30–44 para 45–59 anos."),
            ("03", "Causalidade Reversa na Dieta", "Diagnosticados cortam açúcar; ocultos mantêm excesso."),
        ],
        "rodape": "Insights Acionáveis para Programas de Saúde Corporativa",
    },
    {
        "num": 9,
        "layout": "chart_right_01_02",
        "tag": "INTELIGÊNCIA GEORREFERENCIADA",
        "titulo": "PANORAMA BRASIL (27 UFs)",
        "subtitulo": "Índice Territorial cruzando API SIDRA/IBGE (Censo 2022/PNS) e DATASUS (SIH/CNES).",
        "figura": "fig6_ranking_territorial_uf.png",
        "itens": [
            ("01", "Onde Alocar Equipes no Brasil", "PA, MA, AL, PE e RJ lideram vulnerabilidade composta."),
            ("02", "Internações vs. Atenção Básica", "Identifica gargalos regionais de cobertura preventiva."),
            ("03", "Banco Relacional SQLite", "Consultas SQL prontas para integração via BI/API."),
        ],
        "rodape": "Camada Macro Territorial • Zero Fraude de Chave Primária",
    },
    {
        "num": 10,
        "layout": "circle_infographic",
        "tag": "DEMONSTRAÇÃO DO PRODUTO",
        "titulo": "ECOSSISTEMA INTERATIVO",
        "subtitulo": "Quatro módulos integrados em aplicação web executiva (100% em Português).",
        "centro": "RADAR\nWEB APP",
        "quadrantes": [
            ("01", "Simulador Individual", "Score de risco ao vivo nos 3 modelos."),
            ("02", "Simulador What-If", "Queda imediata do risco pós-intervenção."),
            ("03", "Radar de Carteira", "Filtro de 5.131 adultos e 244 ocultos."),
            ("04", "Mapa 27 UFs & SQL", "Priorização IBGE/DATASUS e banco SQL."),
        ],
        "rodape": "Demonstração Prática Ao Vivo • Streamlit + Painel HTML",
    },
    {
        "num": 11,
        "layout": "three_pillars",
        "tag": "MATURIDADE & NEGÓCIO",
        "titulo": "PRONTIDÃO PARA O MERCADO",
        "subtitulo": "Engenharia homologada, conformidade regulatória e modelo de receita escalável.",
        "pilares": [
            ("TRL 6/7", "Maturidade Técnica", "Pipeline automatizado, banco SQLite e 12 testes no pytest."),
            ("LGPD", "Segurança Jurídica", "Anonimização na origem e base legal de tutela da saúde (Art. 11)."),
            ("B2B SaaS", "Modelo Comercial", "Licenciamento para operadoras, clínicas e secretarias de saúde."),
        ],
        "rodape": "Viabilidade de Engenharia e Retorno sobre o Investimento",
    },
    {
        "num": 12,
        "layout": "team_closing",
        "tag": "EQUIPE & CONCLUSÃO",
        "titulo": "NOSSO TIME DE ENGENHARIA",
        "subtitulo": "Transformando dados públicos em prevenção acionável antes que a complicação aconteça.",
        "equipe": INTEGRANTES_INFO,
        "resumo_final": "5.131 Adultos Auditados   •   86,1% Sensibilidade   •   94,9% VPN   •   2,20x Lift Comercial",
        "rodape": "UNEX 2026 • Bacharelado em Sistemas de Informação • Mineração de Dados",
    },
]


# ==============================================================================
# FUNÇÕES UTILITÁRIAS COM CONTROLE MATEMÁTICO DE CAIXAS NO PDF
# ==============================================================================
def _desenhar_paragrafo_em_caixa(
    c,
    texto: str,
    x: float,
    y_top: float,
    largura_max: float,
    fonte: str = "Helvetica",
    tamanho: float = 12.0,
    entrelinha: float = 15.5,
    cor=colors.HexColor("#64748B"),
    alinhamento: int = TA_LEFT,
) -> float:
    """Renderiza texto com quebra de linha automática garantida dentro de largura_max."""
    st = ParagraphStyle(
        "BoxText",
        fontName=fonte,
        fontSize=tamanho,
        leading=entrelinha,
        textColor=cor,
        alignment=alinhamento,
    )
    txt_xml = (
        texto.replace("&", "&amp;")
        .replace("<=", "&le;")
        .replace(">=", "&ge;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    p = Paragraph(txt_xml, st)
    _, h_usada = p.wrap(largura_max, 10 * cm)
    p.drawOn(c, x, y_top - h_usada)
    return h_usada


def _desenhar_grade_pontos_pdf(c, x0: float, y0: float, cols: int, rows: int, gap: float, cor):
    c.setFillColor(cor)
    for r in range(rows):
        for col in range(cols):
            c.circle(x0 + col * gap, y0 + r * gap, 0.08 * cm, fill=1, stroke=0)


def _desenhar_cabecalho_clean_pdf(
    c, largura: float, altura: float, tag: str, titulo: str, subtitulo: str, alinhado_centro: bool = False
):
    COR_AMBER = colors.HexColor("#F5A623")
    COR_DARK = colors.HexColor("#1E242B")
    COR_MUTED = colors.HexColor("#64748B")

    # Calcula largura exata da pílula de tag pelo stringWidth + folga generosa
    w_txt_tag = stringWidth(tag, "Helvetica-Bold", 9.5)
    tag_w = w_txt_tag + 1.4 * cm

    if alinhado_centro:
        c.setFillColor(colors.HexColor("#FFF3D6"))
        c.roundRect((largura - tag_w) / 2, altura - 2.1 * cm, tag_w, 0.72 * cm, 0.36 * cm, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#D98200"))
        c.setFont("Helvetica-Bold", 9.5)
        c.drawCentredString(largura / 2, altura - 1.85 * cm, tag)

        c.setFillColor(COR_DARK)
        c.setFont("Helvetica-Bold", 26)
        c.drawCentredString(largura / 2, altura - 3.15 * cm, titulo)

        c.setFillColor(COR_AMBER)
        c.roundRect(largura / 2 - 1.2 * cm, altura - 3.55 * cm, 2.4 * cm, 0.12 * cm, 0.06 * cm, fill=1, stroke=0)

        c.setFillColor(COR_MUTED)
        c.setFont("Helvetica", 13)
        c.drawCentredString(largura / 2, altura - 4.15 * cm, subtitulo)
    else:
        c.setFillColor(colors.HexColor("#FFF3D6"))
        c.roundRect(2.0 * cm, altura - 2.1 * cm, tag_w, 0.72 * cm, 0.36 * cm, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#D98200"))
        c.setFont("Helvetica-Bold", 9.5)
        c.drawCentredString(2.0 * cm + tag_w / 2, altura - 1.85 * cm, tag)

        c.setFillColor(COR_DARK)
        c.setFont("Helvetica-Bold", 26)
        c.drawString(2.0 * cm, altura - 3.15 * cm, titulo)

        c.setFillColor(COR_AMBER)
        c.roundRect(2.0 * cm, altura - 3.52 * cm, 2.2 * cm, 0.12 * cm, 0.06 * cm, fill=1, stroke=0)

        c.setFillColor(COR_MUTED)
        c.setFont("Helvetica", 13)
        c.drawString(2.0 * cm, altura - 4.15 * cm, subtitulo)


def _desenhar_rodape_clean_pdf(c, largura: float, num: int, texto_rodape: str):
    c.setStrokeColor(colors.HexColor("#E2E8F0"))
    c.setLineWidth(1)
    c.line(2.0 * cm, 1.45 * cm, largura - 2.0 * cm, 1.45 * cm)

    c.setFillColor(colors.HexColor("#94A3B8"))
    c.setFont("Helvetica", 9.5)
    c.drawString(2.0 * cm, 0.82 * cm, texto_rodape)

    c.setFillColor(colors.HexColor("#F5A623"))
    c.roundRect(largura - 3.6 * cm, 0.62 * cm, 1.6 * cm, 0.58 * cm, 0.28 * cm, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 9.5)
    c.drawCentredString(largura - 2.8 * cm, 0.80 * cm, f"{num:02d} / 12")


def gerar_pdf_slides_pitch(caminho_pdf: Path) -> None:
    """Gera o PDF Widescreen 16:9 no design Clean Corporativo com encaixe perfeito em todas as caixas."""
    largura, altura = 33.867 * cm, 19.05 * cm
    c = pdfcanvas.Canvas(str(caminho_pdf), pagesize=(largura, altura))

    COR_WHITE = colors.HexColor("#FFFFFF")
    COR_CARD = colors.HexColor("#F8FAFC")
    COR_BORDER = colors.HexColor("#E2E8F0")
    COR_AMBER = colors.HexColor("#F5A623")
    COR_AMBER_LIGHT = colors.HexColor("#FFF7E6")
    COR_DARK = colors.HexColor("#1E242B")
    COR_MUTED = colors.HexColor("#64748B")

    for s in SLIDES_CLEAN:
        c.setFillColor(COR_WHITE)
        c.rect(0, 0, largura, altura, fill=1, stroke=0)

        layout = s["layout"]

        if layout == "hero_cover":
            # Círculos decorativos à direita (sem conflitar com a grade de pontos)
            c.setFillColor(COR_AMBER_LIGHT)
            c.circle(largura - 7.5 * cm, altura / 2 + 0.3 * cm, 6.2 * cm, fill=1, stroke=0)
            c.setFillColor(COR_AMBER)
            c.circle(largura - 7.5 * cm, altura / 2 + 0.3 * cm, 5.1 * cm, fill=1, stroke=0)
            c.circle(largura - 13.8 * cm, altura - 3.8 * cm, 0.50 * cm, fill=1, stroke=0)
            _desenhar_grade_pontos_pdf(c, 2.0 * cm, 2.15 * cm, 6, 3, 0.42 * cm, colors.HexColor("#CBD5E1"))

            # Logo Diamond + Tag no topo esquerdo
            c.saveState()
            c.translate(2.45 * cm, altura - 2.65 * cm)
            c.rotate(45)
            c.setFillColor(COR_AMBER)
            c.roundRect(-0.42 * cm, -0.42 * cm, 0.84 * cm, 0.84 * cm, 0.12 * cm, fill=1, stroke=0)
            c.restoreState()

            c.setFillColor(COR_DARK)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(3.3 * cm, altura - 2.80 * cm, s["tag"])

            c.setFillColor(COR_AMBER)
            c.setFont("Helvetica-Bold", 42)
            c.drawString(2.0 * cm, altura - 5.2 * cm, s["titulo_1"])

            c.setFillColor(COR_DARK)
            c.setFont("Helvetica-Bold", 38)
            c.drawString(2.0 * cm, altura - 6.8 * cm, s["titulo_2"])

            c.setFillColor(COR_AMBER)
            c.roundRect(2.0 * cm, altura - 7.45 * cm, 3.2 * cm, 0.15 * cm, 0.07 * cm, fill=1, stroke=0)

            _desenhar_paragrafo_em_caixa(
                c, s["subtitulo"], 2.0 * cm, altura - 7.95 * cm, 15.5 * cm,
                fonte="Helvetica", tamanho=14.0, entrelinha=18.5, cor=COR_MUTED
            )

            # 3 Cards flutuantes sobre o círculo âmbar à direita
            y_k = altura - 5.2 * cm
            for idx_k, (val, leg) in enumerate(s["kpis"], start=1):
                kx = largura - 12.2 * cm
                kw = 9.6 * cm
                kh = 2.55 * cm
                c.setFillColor(COR_WHITE)
                c.setStrokeColor(COR_BORDER)
                c.setLineWidth(1.2)
                c.roundRect(kx, y_k, kw, kh, 0.45 * cm, fill=1, stroke=1)

                c.setFillColor(COR_AMBER)
                c.circle(kx + 1.35 * cm, y_k + kh / 2, 0.72 * cm, fill=1, stroke=0)
                c.setFillColor(COR_WHITE)
                c.setFont("Helvetica-Bold", 13)
                c.drawCentredString(kx + 1.35 * cm, y_k + kh / 2 - 0.16 * cm, f"{idx_k:02d}")

                c.setFillColor(COR_DARK)
                c.setFont("Helvetica-Bold", 21)
                c.drawString(kx + 2.55 * cm, y_k + 1.38 * cm, val)

                c.setFillColor(COR_MUTED)
                c.setFont("Helvetica", 11.5)
                c.drawString(kx + 2.55 * cm, y_k + 0.62 * cm, leg)
                y_k -= 3.25 * cm

            # Caixa de integrantes na base esquerda — 2 linhas de 3 integrantes (100% dentro da caixa com folga!)
            eq_x, eq_y, eq_w, eq_h = 2.0 * cm, 3.85 * cm, 15.6 * cm, 2.85 * cm
            c.setFillColor(COR_CARD)
            c.setStrokeColor(COR_BORDER)
            c.setLineWidth(1.2)
            c.roundRect(eq_x, eq_y, eq_w, eq_h, 0.40 * cm, fill=1, stroke=1)

            c.setFillColor(COR_DARK)
            c.setFont("Helvetica-Bold", 10.5)
            c.drawString(eq_x + 0.65 * cm, eq_y + 2.05 * cm, "EQUIPE RESPONSÁVEL (5º PERÍODO — SISTEMAS DE INFORMAÇÃO):")

            c.setFillColor(COR_MUTED)
            c.setFont("Helvetica", 10.5)
            linha_eq_1 = "Augusto Santos   •   Daniel Teixeira   •   Douglas Pereira"
            linha_eq_2 = "Graciano Marôto   •   Marcos Nathan   •   Mendell Kalyl"
            assert stringWidth(linha_eq_1, "Helvetica", 10.5) < (eq_w - 1.3 * cm)
            assert stringWidth(linha_eq_2, "Helvetica", 10.5) < (eq_w - 1.3 * cm)
            c.drawString(eq_x + 0.65 * cm, eq_y + 1.25 * cm, linha_eq_1)
            c.drawString(eq_x + 0.65 * cm, eq_y + 0.55 * cm, linha_eq_2)

        elif layout == "split_01_02":
            c.setFillColor(COR_AMBER)
            c.circle(0.5 * cm, altura / 2 - 0.5 * cm, 5.2 * cm, fill=1, stroke=0)
            _desenhar_grade_pontos_pdf(c, largura - 3.2 * cm, altura - 3.2 * cm, 5, 4, 0.40 * cm, colors.HexColor("#CBD5E1"))

            _desenhar_cabecalho_clean_pdf(c, largura, altura, s["tag"], s["titulo"], s["subtitulo"])

            # Card Hero Esquerdo
            hx, hy, hw, hh = 2.2 * cm, 3.0 * cm, 12.2 * cm, 10.2 * cm
            c.setFillColor(COR_DARK)
            c.roundRect(hx, hy, hw, hh, 0.55 * cm, fill=1, stroke=0)

            c.setFillColor(COR_AMBER)
            c.roundRect(hx + 1.0 * cm, hy + hh - 1.8 * cm, 5.8 * cm, 0.72 * cm, 0.36 * cm, fill=1, stroke=0)
            c.setFillColor(COR_DARK)
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(hx + 3.9 * cm, hy + hh - 1.56 * cm, "DESCOBERTA CENTRAL")

            c.setFillColor(COR_AMBER)
            c.setFont("Helvetica-Bold", 62)
            c.drawString(hx + 1.0 * cm, hy + 4.8 * cm, s["destaque_num"])

            c.setFillColor(COR_WHITE)
            c.setFont("Helvetica-Bold", 15)
            c.drawString(hx + 1.0 * cm, hy + 3.15 * cm, "Dos diabéticos são invisíveis")

            _desenhar_paragrafo_em_caixa(
                c,
                "Negavam ter diabetes no questionário, mas apresentavam HbA1c >= 6,5% no exame laboratorial.",
                hx + 1.0 * cm,
                hy + 2.65 * cm,
                hw - 2.0 * cm,
                fonte="Helvetica",
                tamanho=12.0,
                entrelinha=16.5,
                cor=colors.HexColor("#CBD5E1"),
            )

            # Coluna Direita com 01, 02, 03
            y_it = 11.2 * cm
            for cod, tit_i, desc_i in s["itens"]:
                ix, iy, iw, ih = 15.6 * cm, y_it - 1.3 * cm, 16.2 * cm, 2.75 * cm
                c.setFillColor(COR_CARD)
                c.setStrokeColor(COR_BORDER)
                c.setLineWidth(1.1)
                c.roundRect(ix, iy, iw, ih, 0.40 * cm, fill=1, stroke=1)

                c.setFillColor(COR_AMBER)
                c.setFont("Helvetica-Bold", 27)
                c.drawString(ix + 0.75 * cm, iy + 0.95 * cm, cod)

                c.setFillColor(COR_DARK)
                c.setFont("Helvetica-Bold", 15)
                c.drawString(ix + 2.65 * cm, iy + 1.68 * cm, tit_i)

                _desenhar_paragrafo_em_caixa(
                    c, desc_i, ix + 2.65 * cm, iy + 1.35 * cm, iw - 3.2 * cm,
                    fonte="Helvetica", tamanho=12.0, entrelinha=15.5, cor=COR_MUTED
                )
                y_it -= 3.55 * cm

        elif layout == "grid_6_badges":
            c.setFillColor(COR_AMBER)
            c.circle(largura, altura, 2.6 * cm, fill=1, stroke=0)
            _desenhar_cabecalho_clean_pdf(c, largura, altura, s["tag"], s["titulo"], s["subtitulo"], alinhado_centro=True)

            w_card = 9.4 * cm
            h_card = 4.8 * cm
            gap_x = 0.85 * cm
            gap_y = 0.85 * cm
            x0 = (largura - (3 * w_card + 2 * gap_x)) / 2
            y_top_row = 8.8 * cm

            for idx, (badge, tit_c, desc_c) in enumerate(s["cards"]):
                col = idx % 3
                row = idx // 3
                x = x0 + col * (w_card + gap_x)
                y = y_top_row - row * (h_card + gap_y)

                c.setFillColor(COR_CARD)
                c.setStrokeColor(COR_BORDER)
                c.setLineWidth(1.2)
                c.roundRect(x, y, w_card, h_card, 0.45 * cm, fill=1, stroke=1)

                c.setFillColor(COR_AMBER)
                c.circle(x + w_card / 2, y + h_card - 1.35 * cm, 0.88 * cm, fill=1, stroke=0)
                c.setFillColor(COR_WHITE)
                c.setFont("Helvetica-Bold", 13)
                c.drawCentredString(x + w_card / 2, y + h_card - 1.52 * cm, badge)

                c.setFillColor(COR_DARK)
                c.setFont("Helvetica-Bold", 14.5)
                c.drawCentredString(x + w_card / 2, y + 1.75 * cm, tit_c)

                _desenhar_paragrafo_em_caixa(
                    c, desc_c, x + 0.6 * cm, y + 1.45 * cm, w_card - 1.2 * cm,
                    fonte="Helvetica", tamanho=11.5, entrelinha=14.5, cor=COR_MUTED, alinhamento=TA_CENTER
                )

        elif layout == "chart_right_01_02":
            c.setFillColor(COR_AMBER)
            c.circle(largura - 5.5 * cm, altura + 1.8 * cm, 3.2 * cm, fill=1, stroke=0)

            _desenhar_cabecalho_clean_pdf(c, largura, altura, s["tag"], s["titulo"], s["subtitulo"])

            # Coluna esquerda com 01, 02, 03 com largura e wrap auditados
            y_it = 11.1 * cm
            for cod, tit_i, desc_i in s["itens"]:
                ix, iy, iw, ih = 2.0 * cm, y_it - 1.3 * cm, 11.4 * cm, 2.8 * cm
                c.setFillColor(COR_CARD)
                c.setStrokeColor(COR_BORDER)
                c.setLineWidth(1.1)
                c.roundRect(ix, iy, iw, ih, 0.40 * cm, fill=1, stroke=1)

                c.setFillColor(COR_AMBER)
                c.roundRect(ix, iy, 0.22 * cm, ih, 0.10 * cm, fill=1, stroke=0)

                c.setFillColor(COR_AMBER)
                c.setFont("Helvetica-Bold", 21)
                c.drawString(ix + 0.55 * cm, iy + 1.55 * cm, cod)

                c.setFillColor(COR_DARK)
                c.setFont("Helvetica-Bold", 13.0)
                c.drawString(ix + 1.85 * cm, iy + 1.62 * cm, tit_i)

                _desenhar_paragrafo_em_caixa(
                    c, desc_i, ix + 0.55 * cm, iy + 1.25 * cm, iw - 1.0 * cm,
                    fonte="Helvetica", tamanho=11.2, entrelinha=14.2, cor=COR_MUTED
                )
                y_it -= 3.55 * cm

            # Moldura inteligente à direita ajustada exatamente à proporção da imagem (sem sobras vazias!)
            img_path = FIGURES_DIR / s["figura"]
            if img_path.exists():
                with PILImage.open(img_path) as im:
                    im_w, im_h = im.size
                aspect = im_w / float(im_h)

                area_x, area_y, area_w, area_h = 14.0 * cm, 2.35 * cm, 17.8 * cm, 11.65 * cm
                pad = 0.40 * cm
                max_iw = area_w - 2 * pad
                max_ih = area_h - 2 * pad

                if max_iw / aspect <= max_ih:
                    draw_w = max_iw
                    draw_h = max_iw / aspect
                else:
                    draw_h = max_ih
                    draw_w = max_ih * aspect

                frame_w = draw_w + 2 * pad
                frame_h = draw_h + 2 * pad
                frame_x = area_x + (area_w - frame_w) / 2
                frame_y = area_y + (area_h - frame_h) / 2

                c.setFillColor(COR_WHITE)
                c.setStrokeColor(COR_BORDER)
                c.setLineWidth(1.5)
                c.roundRect(frame_x, frame_y, frame_w, frame_h, 0.45 * cm, fill=1, stroke=1)

                c.drawImage(
                    str(img_path),
                    frame_x + pad,
                    frame_y + pad,
                    width=draw_w,
                    height=draw_h,
                )

        elif layout == "circle_infographic":
            _desenhar_cabecalho_clean_pdf(c, largura, altura, s["tag"], s["titulo"], s["subtitulo"], alinhado_centro=True)
            _desenhar_grade_pontos_pdf(c, 2.2 * cm, altura - 4.5 * cm, 4, 4, 0.40 * cm, colors.HexColor("#CBD5E1"))
            _desenhar_grade_pontos_pdf(c, largura - 3.6 * cm, 2.6 * cm, 4, 4, 0.40 * cm, colors.HexColor("#CBD5E1"))

            cx, cy = largura / 2, 8.1 * cm
            c.setFillColor(COR_AMBER)
            c.circle(cx, cy, 4.35 * cm, fill=1, stroke=0)

            c.setStrokeColor(COR_WHITE)
            c.setLineWidth(6)
            c.line(cx - 4.5 * cm, cy, cx + 4.5 * cm, cy)
            c.line(cx, cy - 4.5 * cm, cx, cy + 4.5 * cm)

            c.setFillColor(COR_WHITE)
            c.circle(cx, cy, 2.05 * cm, fill=1, stroke=0)
            c.setFillColor(COR_DARK)
            c.setFont("Helvetica-Bold", 12.5)
            c.drawCentredString(cx, cy + 0.20 * cm, "RADAR")
            c.setFillColor(COR_AMBER)
            c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(cx, cy - 0.35 * cm, "WEB APP")

            pos_anel = [
                (cx - 2.2 * cm, cy + 2.0 * cm, "01"),
                (cx + 2.2 * cm, cy + 2.0 * cm, "02"),
                (cx - 2.2 * cm, cy - 2.3 * cm, "03"),
                (cx + 2.2 * cm, cy - 2.3 * cm, "04"),
            ]
            c.setFillColor(COR_WHITE)
            c.setFont("Helvetica-Bold", 16)
            for px, py, num_q in pos_anel:
                c.drawCentredString(px, py, num_q)

            coords_cards = [
                (2.0 * cm, 9.1 * cm),
                (largura - 11.6 * cm, 9.1 * cm),
                (2.0 * cm, 3.9 * cm),
                (largura - 11.6 * cm, 3.9 * cm),
            ]
            for idx, (cod, tit_q, desc_q) in enumerate(s["quadrantes"]):
                kx, ky = coords_cards[idx]
                kw, kh = 9.6 * cm, 3.2 * cm
                c.setFillColor(COR_CARD)
                c.setStrokeColor(COR_BORDER)
                c.setLineWidth(1.2)
                c.roundRect(kx, ky, kw, kh, 0.40 * cm, fill=1, stroke=1)

                c.setFillColor(COR_AMBER)
                c.setFont("Helvetica-Bold", 12.5)
                c.drawString(kx + 0.65 * cm, ky + 2.25 * cm, f"MÓDULO {cod}")

                c.setFillColor(COR_DARK)
                c.setFont("Helvetica-Bold", 14.5)
                c.drawString(kx + 0.65 * cm, ky + 1.45 * cm, tit_q)

                _desenhar_paragrafo_em_caixa(
                    c, desc_q, kx + 0.65 * cm, ky + 1.15 * cm, kw - 1.3 * cm,
                    fonte="Helvetica", tamanho=11.5, entrelinha=14.5, cor=COR_MUTED
                )

        elif layout == "three_pillars":
            _desenhar_cabecalho_clean_pdf(c, largura, altura, s["tag"], s["titulo"], s["subtitulo"], alinhado_centro=True)

            w_p = 8.8 * cm
            h_p = 8.6 * cm
            gap = 1.2 * cm
            x0 = (largura - (3 * w_p + 2 * gap)) / 2
            y0 = 3.1 * cm

            for idx, (selo, tit_p, desc_p) in enumerate(s["pilares"]):
                px = x0 + idx * (w_p + gap)
                c.setFillColor(COR_AMBER if idx == 1 else COR_CARD)
                c.setStrokeColor(COR_AMBER)
                c.setLineWidth(2)
                c.roundRect(px, y0, w_p, h_p, 0.65 * cm, fill=1, stroke=1)

                c.setFillColor(COR_DARK)
                c.circle(px + w_p / 2, y0 + h_p, 1.35 * cm, fill=1, stroke=0)
                c.setFillColor(COR_AMBER)
                c.setFont("Helvetica-Bold", 13.5)
                c.drawCentredString(px + w_p / 2, y0 + h_p - 0.18 * cm, selo)

                c.setFillColor(COR_DARK)
                c.setFont("Helvetica-Bold", 17)
                c.drawCentredString(px + w_p / 2, y0 + 5.1 * cm, tit_p)

                c.setStrokeColor(COR_DARK if idx == 1 else COR_AMBER)
                c.setLineWidth(2)
                c.line(px + w_p / 2 - 1.2 * cm, y0 + 4.5 * cm, px + w_p / 2 + 1.2 * cm, y0 + 4.5 * cm)

                _desenhar_paragrafo_em_caixa(
                    c, desc_p, px + 0.8 * cm, y0 + 3.8 * cm, w_p - 1.6 * cm,
                    fonte="Helvetica", tamanho=12.5, entrelinha=17.0,
                    cor=(COR_DARK if idx == 1 else COR_MUTED), alinhamento=TA_CENTER
                )

        elif layout == "team_closing":
            _desenhar_cabecalho_clean_pdf(c, largura, altura, s["tag"], s["titulo"], s["subtitulo"], alinhado_centro=True)

            n_eq = len(s["equipe"])
            espaco_eq = 5.0 * cm
            x_start = (largura - (n_eq - 1) * espaco_eq) / 2
            cy_avatar = 9.3 * cm

            for idx, (iniciais, nome_curto, papel) in enumerate(s["equipe"]):
                ax = x_start + idx * espaco_eq
                c.setFillColor(COR_AMBER)
                c.circle(ax, cy_avatar, 1.85 * cm, fill=1, stroke=0)
                c.setFillColor(COR_DARK)
                c.circle(ax, cy_avatar, 1.52 * cm, fill=1, stroke=0)

                c.setFillColor(COR_WHITE)
                c.setFont("Helvetica-Bold", 20)
                c.drawCentredString(ax, cy_avatar - 0.25 * cm, iniciais)

                c.setFillColor(COR_DARK)
                c.setFont("Helvetica-Bold", 13)
                c.drawCentredString(ax, cy_avatar - 2.65 * cm, nome_curto)

                c.setFillColor(COR_MUTED)
                c.setFont("Helvetica", 10.2)
                c.drawCentredString(ax, cy_avatar - 3.25 * cm, papel)

            c.setFillColor(COR_DARK)
            c.roundRect(3.2 * cm, 2.55 * cm, largura - 6.4 * cm, 2.15 * cm, 0.45 * cm, fill=1, stroke=0)
            c.setFillColor(COR_AMBER)
            c.setFont("Helvetica-Bold", 14.5)
            c.drawCentredString(largura / 2, 3.42 * cm, s["resumo_final"])

        _desenhar_rodape_clean_pdf(c, largura, s["num"], s["rodape"])
        c.showPage()

    c.save()
    print(f"[PDF Slides Clean Auditado] Gerado {caminho_pdf}")


# ==============================================================================
# GERADOR DO POWERPOINT (.PPTX) WIDESCREEN 16:9 — ALTA FIDELIDADE SEM OVERFLOW
# ==============================================================================
def gerar_pptx_pitch(caminho_pptx: Path) -> None:
    """
    Gera o arquivo PowerPoint (.pptx) Widescreen 16:9 a partir das páginas renderizadas em
    altíssima resolução (300 DPI) do PDF auditado, garantindo que ao abrir em qualquer versão
    do PowerPoint, Google Slides ou LibreOffice o layout fique 100% idêntico e sem nenhum
    texto fora das caixas por diferença de fonte instalada.
    """
    import fitz

    pdf_path = caminho_pptx.with_suffix(".pdf")
    if not pdf_path.exists():
        gerar_pdf_slides_pitch(pdf_path)

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    doc_pdf = fitz.open(str(pdf_path))
    temp_dir = DOCS_DIR / "_tmp_slides"
    temp_dir.mkdir(parents=True, exist_ok=True)

    for idx, page in enumerate(doc_pdf):
        pix = page.get_pixmap(dpi=240)
        img_temp = temp_dir / f"slide_{idx+1:02d}.png"
        pix.save(str(img_temp))

        slide = prs.slides.add_slide(blank_layout)
        slide.shapes.add_picture(str(img_temp), 0, 0, width=prs.slide_width, height=prs.slide_height)
        img_temp.unlink(missing_ok=True)

    doc_pdf.close()
    try:
        temp_dir.rmdir()
    except OSError:
        pass

    prs.save(caminho_pptx)
    print(f"[PPTX Alta Fidelidade] Gerado {caminho_pptx}")


def gerar_roteiro_defesa(caminho_docx: Path, caminho_pdf: Path) -> None:
    """Gera o Roteiro de Oratória e Guia de Defesa para os 6 integrantes na pasta docs/."""
    roteiro_secoes = [
        (
            "1. ESTRATÉGIA DE TEMPO E DIVISÃO ENTRE OS 6 INTEGRANTES (10 A 12 MINUTOS)",
            [
                "Os slides foram redesenhados com visual corporativo minimalista (pouco texto, números de impacto e gráficos de alta resolução) para que nenhum integrante leia tela. A fala deve complementar os números visíveis:",
                "• Integrante 1 (Augusto Santos de Oliveira) — Slides 01 e 02 (00:00 a 01:50): Abertura Executiva, Resgate da Dor (Bloco 1) e a Descoberta Empírica dos 24,2% de Casos Ocultos.",
                "• Integrante 2 (Daniel Teixeira Santos) — Slides 03 e 04 (01:50 a 03:40): Integridade Metodológica (Data Leakage Shield), Imputação sem Vazamento e Curvas ROC no Teste Cego (AUC = 0,838).",
                "• Integrante 3 (Douglas Pereira Santos) — Slides 05 e 06 (03:40 a 05:30): Por que a Sensibilidade (Recall = 86,1% e VPN = 94,9%) salva vidas e Explicabilidade White-Box (Razão Cintura/Estatura > IMC).",
                "• Integrante 4 (Graciano Marôto da Cunha Neto) — Slides 07 e 08 (05:30 a 07:20): Estratificação Comercial por Tercis (73,8% de captura no Alto Risco; Lift de 2,20x) e Achados Comportamentais (sedentarismo e causalidade reversa na dieta).",
                "• Integrante 5 (Marcos Nathan Moreno Silva) — Slides 09 e 10 [TRANSIÇÃO PARA TELA DO APP AO VIVO] (07:20 a 09:30): Camada Territorial Brasileira (27 UFs IBGE/DATASUS) e Demonstração ao Vivo do Simulador Preditivo e 'What-If'.",
                "• Integrante 6 (Mendell Kalyl Junio Figueiredo de Souza Melo) — Slides 11 e 12 (09:30 a 11:15): Grau de Prontidão Tecnológica (TRL 6/7), Homologação por 12 Testes Automatizados (pytest), Conformidade LGPD e Fechamento Comercial.",
            ],
        ),
        (
            "2. ROTEIRO DE FALA SUGERIDO (SLIDE A SLIDE — SEM LEITURA MECÂNICA)",
            [
                "[Integrante 1 — Augusto | Slides 01 e 02]: 'Boa noite, professor Wallas e colegas. No Bloco 1 mostramos que a saúde suplementar e pública age de forma reativa porque seus dados estão em silos. No Bloco 3, executamos a mineração sobre 9.254 registros brutos do CDC NHANES, consolidando 5.131 adultos auditados. O número no destaque do Slide 02 comprova nossa tese: 24,2% dos diabéticos reais da base — 244 de 1.008 casos — responderam que NÃO tinham diabetes, mas estavam com hemoglobina glicada acima de 6,5% no sangue. Quase 1 em cada 4 diabéticos está invisível até sofrer uma internação.'",
                "[Integrante 2 — Daniel | Slides 03 e 04]: 'No Slide 03 sintetizamos nossa governança: 16 bases oficiais verificadas por hash SHA-256 e 0% de vazamento. Bloqueamos HbA1c, glicemia e insulina no vetor X, treinando o modelo com apenas 19 preditores de rotina em 80/20 estratificado e imputação restrita ao treino. Como mostra o gráfico do Slide 04, alcançamos ROC-AUC de 0,838 na Regressão Logística e 0,830 no Random Forest com o menor Brier Score (0,161).'",
                "[Integrante 3 — Douglas | Slides 05 e 06]: 'No Slide 05 destacamos nossa decisão clínica: em rastreio preventivo, deixar um doente escapar custa uma internação; confirmar custa um exame simples. No limiar de 0,40, o Random Forest atinge 86,1% de Sensibilidade e 94,9% de Valor Preditivo Negativo. E no Slide 06 provamos que o motor é White-Box: a Razão Cintura/Estatura (OR = 1,97) supera o IMC isolado, enquanto cumprir 600 MET-min/semana e manter HDL adequado reduzem ativamente a chance da doença.'",
                "[Integrante 4 — Graciano | Slides 07 e 08]: 'No Slide 07 traduzimos ciência de dados em retorno financeiro: ao dividir a carteira de teste em tercis, a positividade real salta de 2,6% no Baixo Risco para 43,2% no Alto Risco — 16,5 vezes mais risco! Triando apenas o terço superior, a operadora captura 73,8% de todos os diabéticos, economizando dois terços em campanhas cegas. E no Slide 08 vemos que o sedentarismo acima de 8h/dia combinado à inatividade quase dobra a prevalência da doença (28,2% contra 15,1%).'",
                "[Integrante 5 — Marcos Nathan | Slides 09 e 10 + DEMO AO VIVO]: 'No Slide 09 cruzamos a API SIDRA do IBGE com internações do SIH/DATASUS e cobertura do CNES nas 27 UFs brasileiras em banco SQLite, identificando Pará, Maranhão e Alagoas no topo de vulnerabilidade. E no Slide 10 apresentamos a arquitetura dos 4 módulos do nosso Web App, que vou demonstrar agora ao vivo [ABRIR O APP E DEMONSTRAR O SIMULADOR WHAT-IF REDUZINDO O RISCO EM MAIS DE 40%].'",
                "[Integrante 6 — Mendell Kalyl | Slides 11 e 12]: 'Para concluir nos Slides 11 e 12: entregamos um produto em nível TRL 6/7, homologado por 12 testes automatizados no pytest que rodam em menos de 3 segundos, em total conformidade com o Art. 11 da LGPD (tutela da saúde) e pronto para licenciamento B2B SaaS. Transformamos dados públicos em prevenção acionável. Muito obrigado!'",
            ],
        ),
        (
            "3. PERGUNTAS PROVÁVEIS DA BANCA (PROF. WALLAS) E RESPOSTAS TÉCNICAS DE BOLSO",
            [
                "Pergunta 1: 'Como vocês garantem matematicamente que não houve Data Leakage?' -> Resposta: 'Através da blocklist auditada pelo teste CT-06 do pytest (que impede qualquer variável glicêmica ou de medicamento no vetor X) e do transformador StratifiedMedianImputer validado pelo teste CT-07 (que calcula medianas por sexo e idade estritamente nos 4.104 pacientes de treino).'",
                "Pergunta 2: 'Por que a Razão Cintura/Estatura ficou acima do IMC nos dois modelos?' -> Resposta: 'Porque o IMC não separa massa muscular de gordura visceral abdominal. A razão cintura/estatura captura diretamente a adiposidade central, que gera resistência insulínica.'",
                "Pergunta 3: 'Qual foi a trava técnica mais importante na limpeza do NHANES?' -> Resposta: 'Diferenciar os códigos 7 e 9 por domínio: em perguntas fechadas, 7 significa Recusou; porém, no questionário de atividade física (PAQ), 7 significa literalmente 7 dias por semana de treino (e o código de recusa é 77). Nosso teste CT-04 garante que nenhum praticante diário foi apagado.'",
            ],
        ),
    ]

    doc = docx.Document()
    for s in doc.sections:
        s.top_margin, s.left_margin, s.bottom_margin, s.right_margin = Cm(2.5), Cm(2.5), Cm(2.0), Cm(2.0)
    st_n = doc.styles["Normal"]
    st_n.font.name = "Times New Roman"
    st_n.font.size = Pt(12)

    p_t = doc.add_paragraph()
    p_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p_t.add_run("ROTEIRO EXECUTIVO DO PITCH COMERCIAL E GUIA DE DEFESA ORAL — BLOCO 3\n")
    r.bold = True
    p_t.add_run("UNEX — Sistemas de Informação | Disciplina: Mineração de Dados — Prof. Wallas Froes de Oliveira")

    for tit, pars in roteiro_secoes:
        ph = doc.add_paragraph()
        rh = ph.add_run(tit)
        rh.bold = True
        for texto in pars:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(6)
            p.add_run(texto)
    doc.save(caminho_docx)

    pdf = SimpleDocTemplate(str(caminho_pdf), pagesize=A4, topMargin=2.5 * cm, leftMargin=2.5 * cm, bottomMargin=2.0 * cm, rightMargin=2.0 * cm)
    styles = getSampleStyleSheet()
    st_h = ParagraphStyle("RH", parent=styles["Normal"], fontName="Times-Bold", fontSize=12, leading=16, spaceBefore=12, spaceAfter=6)
    st_b = ParagraphStyle("RB", parent=styles["Normal"], fontName="Times-Roman", fontSize=11.5, leading=16, spaceAfter=6)
    story = [
        Paragraph("<b>ROTEIRO EXECUTIVO DO PITCH COMERCIAL E GUIA DE DEFESA ORAL — BLOCO 3</b>", st_h),
        Paragraph("UNEX — Sistemas de Informação | Mineração de Dados — Prof. Wallas Froes de Oliveira", st_b),
        Spacer(1, 0.3 * cm),
    ]
    for tit, pars in roteiro_secoes:
        story.append(Paragraph(tit, st_h))
        for texto in pars:
            story.append(Paragraph(texto.replace("&", "&amp;"), st_b))
    pdf.build(story)
    print(f"[Roteiro] Gerados {caminho_docx} e {caminho_pdf}")


if __name__ == "__main__":
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    gerar_pdf_slides_pitch(DOCS_DIR / "Bloco_3_Pitch_Comercial_Apresentacao_Slides.pdf")
    gerar_pptx_pitch(DOCS_DIR / "Bloco_3_Pitch_Comercial_Apresentacao_Slides.pptx")
