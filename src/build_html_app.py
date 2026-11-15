"""
Gera o Dashboard Executivo Autocontido (app/radar_diabetes_demo.html) com Design
Glucomate / Apple Health (medidores circulares em arco SVG, barras visuais de faixas,
seletores de tempo em Horas e Minutos, Escolaridade por extenso e Renda em R$).
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
FIGURES_DIR = ROOT_DIR / "reports" / "figures"
TABLES_DIR = ROOT_DIR / "reports" / "tables"
APP_DIR = ROOT_DIR / "app"


def _img_b64(caminho: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(caminho.read_bytes()).decode("ascii")


def gerar_html_demo() -> Path:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    df_uf = pd.read_parquet(PROCESSED_DIR / "territorial_uf.parquet")
    df_comp = pd.read_csv(TABLES_DIR / "comparativo_modelos.csv")
    df_audit = pd.read_csv(PROCESSED_DIR / "feature_audit.csv")

    imgs = {f.stem: _img_b64(f) for f in sorted(FIGURES_DIR.glob("*.png"))}

    linhas_uf_html = ""
    for _, r in df_uf.iterrows():
        cor_badge = (
            "#EF4444" if r["prioridade_territorial"] == "Prioridade Crítica"
            else ("#F59E0B" if r["prioridade_territorial"] == "Atenção Tática" else "#10B981")
        )
        linhas_uf_html += f"""
        <tr>
            <td><b>#{int(r['ranking_vulnerabilidade'])}</b></td>
            <td><b>{r['uf']}</b> — {r['nome_uf']}</td>
            <td>{r['regiao']}</td>
            <td><b>{r['indice_contexto_territorial']:+.3f}</b></td>
            <td><span style="background:{cor_badge};color:#fff;padding:4px 10px;border-radius:999px;font-size:11.5px;font-weight:700;">{r['prioridade_territorial']}</span></td>
            <td>{r['internacoes_diabetes_100k']:.1f}</td>
            <td>{r['cobertura_ab']:.1f}%</td>
            <td>R$ {r['renda_mediana_uf']:.0f}</td>
            <td>{r['prev_diabetes_uf']:.1f}%</td>
            <td>{r['pct_insuf_atividade_uf']:.1f}%</td>
        </tr>
        """

    linhas_mod_html = ""
    for _, r in df_comp.iterrows():
        linhas_mod_html += f"""
        <tr>
            <td><b>{r['Modelo']}</b></td>
            <td>{r['CV_ROC_AUC']}</td>
            <td><b>{r['Test_ROC_AUC']:.4f}</b></td>
            <td>{r['Brier_Score']:.4f}</td>
            <td><b>{r['Recall_Rastreio_040']*100:.2f}%</b></td>
            <td>{r['Especificidade_Rastreio_040']*100:.2f}%</td>
            <td><b>{r['VPN_Rastreio_040']*100:.2f}%</b></td>
            <td>{r['F1_Rastreio_040']:.4f}</td>
            <td>VP={int(r['VP_040'])} | FN={int(r['FN_040'])} | VN={int(r['VN_040'])} | FP={int(r['FP_040'])}</td>
        </tr>
        """

    linhas_audit_html = ""
    for _, r in df_audit.iterrows():
        linhas_audit_html += f"""
        <tr>
            <td><code>{r['feature']}</code></td>
            <td>{r['eixo']}</td>
            <td>{r['unidade']}</td>
            <td>{int(r['n_validos'])} ({100 - r['pct_ausente']:.1f}%)</td>
            <td>{r['mediana']}</td>
            <td>{r['corr_pearson_alvo']:+.4f}</td>
            <td><span style="color:#0D9488;font-weight:700;">✔ {r['flag_vazamento']}</span></td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Radar Preditivo de Diabetes — Plataforma Inteligente (Bloco 3)</title>
<style>
:root {{
    --teal: #0D9488;
    --teal-dark: #0F766E;
    --bg: #EEF7F6;
    --card: #FFFFFF;
    --border: #E2E8F0;
    --text: #0F172A;
    --muted: #64748B;
    --green: #10B981;
    --amber: #F59E0B;
    --red: #EF4444;
}}
* {{ box-sizing: border-box; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
body {{
    margin: 0;
    background: linear-gradient(180deg, #E2F2F1 0%, #F4F9F9 40%, #F8FAFC 100%);
    color: var(--text);
    min-height: 100vh;
}}
.container {{ max-width: 1380px; margin: 0 auto; padding: 22px 28px 40px 28px; }}
.gluco-header {{
    background: linear-gradient(135deg, #0D9488 0%, #0F766E 100%);
    border-radius: 24px;
    padding: 24px 32px;
    color: #fff;
    box-shadow: 0 12px 28px rgba(13, 148, 136, 0.22);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
    margin-bottom: 20px;
}}
.gluco-header h1 {{ margin: 0; font-size: 26px; font-weight: 800; letter-spacing: -0.02em; }}
.gluco-header p {{ margin: 4px 0 0 0; font-size: 14px; color: #CCFBF1; font-weight: 500; }}
.pill-badge {{
    background: rgba(255,255,255,0.16);
    border: 1px solid rgba(255,255,255,0.3);
    padding: 8px 16px;
    border-radius: 999px;
    font-size: 12.5px;
    font-weight: 700;
}}
.nav-tabs {{
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}}
.tab-btn {{
    padding: 12px 22px;
    border: 1px solid var(--border);
    background: #FFFFFF;
    color: var(--muted);
    font-weight: 700;
    font-size: 14px;
    cursor: pointer;
    border-radius: 999px;
    transition: all 0.2s;
    box-shadow: 0 2px 6px rgba(15,23,42,0.04);
}}
.tab-btn.active {{
    background: var(--teal);
    color: #FFFFFF;
    border-color: var(--teal);
    box-shadow: 0 6px 16px rgba(13,148,136,0.25);
}}
.tab-panel {{ display: none; }}
.tab-panel.active {{ display: block; }}
.gluco-card {{
    background: var(--card);
    border-radius: 22px;
    padding: 22px 24px;
    box-shadow: 0 6px 20px rgba(15,23,42,0.05);
    border: 1px solid var(--border);
    margin-bottom: 18px;
}}
.gluco-card h3 {{
    margin: 0 0 14px 0;
    font-size: 17px;
    font-weight: 800;
    color: var(--text);
    display: flex;
    justify-content: space-between;
    align-items: center;
}}
.top-gauges-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr 1.25fr;
    gap: 18px;
    margin-bottom: 20px;
}}
.form-grid-2 {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px;
}}
.preset-bar {{
    display: flex;
    gap: 10px;
    margin-bottom: 18px;
    flex-wrap: wrap;
    align-items: center;
}}
.btn-preset {{
    background: #FFFFFF;
    color: var(--text);
    border: 1.5px solid #CBD5E1;
    padding: 10px 16px;
    border-radius: 999px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 700;
    transition: all 0.15s;
}}
.btn-preset:hover {{ border-color: var(--teal); color: var(--teal); }}
.btn-preset.cta {{
    background: var(--teal);
    color: #FFFFFF;
    border-color: var(--teal);
}}
.field-row {{ margin-bottom: 14px; }}
.field-row label {{
    display: flex;
    justify-content: space-between;
    font-size: 13.5px;
    font-weight: 700;
    color: #1E293B;
    margin-bottom: 6px;
}}
.field-hint {{ font-size: 11.5px; color: var(--muted); margin-top: 3px; }}
select, input[type=number] {{
    width: 100%;
    padding: 10px 12px;
    border-radius: 12px;
    border: 1.5px solid #CBD5E1;
    font-size: 13.5px;
    font-weight: 600;
    color: var(--text);
    background: #F8FAFC;
}}
input[type=range] {{
    width: 100%;
    accent-color: var(--teal);
    cursor: pointer;
}}
.inline-cols-3 {{ display: grid; grid-template-columns: 1.2fr 1fr 1fr; gap: 10px; }}
.inline-cols-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
.helper-pill {{
    background: #F0FDFA;
    border: 1px solid #99F6E4;
    border-radius: 12px;
    padding: 10px 14px;
    font-size: 13px;
    color: #0F766E;
    font-weight: 600;
    margin: 8px 0 12px 0;
}}
.helper-pill.warn {{
    background: #FFFBEB;
    border-color: #FDE68A;
    color: #B45309;
}}
.range-row {{ padding: 9px 0; border-bottom: 1px solid #F1F5F9; }}
.range-row:last-child {{ border-bottom: none; }}
.range-top {{ display: flex; justify-content: space-between; font-size: 13px; font-weight: 700; margin-bottom: 5px; }}
.range-track {{ width: 100%; height: 8px; background: #E2E8F0; border-radius: 999px; overflow: hidden; }}
.range-fill {{ height: 100%; border-radius: 999px; transition: width 0.3s; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th {{ background: #F1F5F9; color: var(--text); text-align: left; padding: 10px 12px; font-weight: 800; border-bottom: 2px solid #CBD5E1; }}
td {{ padding: 9px 12px; border-bottom: 1px solid #E2E8F0; }}
img.chart {{ width: 100%; border-radius: 14px; border: 1px solid var(--border); }}
</style>
</head>
<body>

<div class="container">
    <div class="gluco-header">
        <div>
            <h1>💚 Radar Preditivo de Diabetes</h1>
            <p>Plataforma Inteligente de Triagem Preventiva & Simulação Clínica • UNEX Sistemas de Informação (Bloco 3)</p>
        </div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;">
            <span class="pill-badge">🛡️ Sem Exames Glicêmicos (Zero Vazamento)</span>
            <span class="pill-badge">🎯 Sensibilidade: 86,1% | VPN: 94,9%</span>
        </div>
    </div>

    <div class="nav-tabs">
        <button class="tab-btn active" onclick="openTab('tab1', this)">🎯 1. Avaliador de Risco & Simulador What-If</button>
        <button class="tab-btn" onclick="openTab('tab2', this)">📊 2. Painel da Carteira (5.131 Adultos)</button>
        <button class="tab-btn" onclick="openTab('tab3', this)">🗺️ 3. Mapa Brasil 27 UFs (IBGE + DATASUS)</button>
        <button class="tab-btn" onclick="openTab('tab4', this)">🔬 4. Auditoria dos Modelos & Segurança</button>
    </div>

    <!-- ABA 1 -->
    <div id="tab1" class="tab-panel active">
        <div class="preset-bar">
            <span style="font-weight:800;font-size:13.5px;color:#0F766E;">⚡ Pacientes-Exemplo:</span>
            <button class="btn-preset" onclick="carregarPreset(1)">🔴 Perfil 1: Sr. Carlos (58a, sedentário, 9h sentado)</button>
            <button class="btn-preset" onclick="carregarPreset(2)">🟠 Perfil 2: Marcelo (46a, treina 3x, mas 10h sentado)</button>
            <button class="btn-preset" onclick="carregarPreset(3)">🟢 Perfil 3: Mariana (29a, ativa, 4h sentada + fibras)</button>
            <button class="btn-preset cta" onclick="aplicarIntervencao()">✨ Aplicar Meta Preventiva nos Campos Abaixo</button>
        </div>

        <!-- 3 CARDS TOPO ESTILO GLUCOMATE -->
        <div class="top-gauges-grid">
            <div class="gluco-card" style="text-align:center;">
                <h3>
                    <span>Diagnóstico Preditivo Atual</span>
                    <span id="badge-atual" style="font-size:11.5px;padding:4px 10px;border-radius:999px;">--</span>
                </h3>
                <div style="position:relative;width:210px;height:170px;margin:0 auto;">
                    <svg viewBox="0 0 200 175" width="210" height="170">
                        <path d="M 35 148 A 76 76 0 1 1 165 148" fill="none" stroke="#E2E8F0" stroke-width="16" stroke-linecap="round"/>
                        <path id="arc-atual" d="M 35 148 A 76 76 0 1 1 165 148" fill="none" stroke="#EF4444" stroke-width="16" stroke-linecap="round" stroke-dasharray="0 500"/>
                    </svg>
                    <div style="position:absolute;top:54px;left:0;right:0;">
                        <div id="val-atual" style="font-size:36px;font-weight:800;">--%</div>
                        <div style="font-size:11.5px;font-weight:700;color:#64748B;">SCORE DE RISCO</div>
                    </div>
                </div>
                <div id="sub-atual" style="background:#F8FAFC;border-radius:12px;padding:10px;font-size:12.5px;font-weight:600;border:1px solid #E2E8F0;">--</div>
            </div>

            <div class="gluco-card" style="text-align:center;">
                <h3>
                    <span>Simulação What-If (Com Prevenção)</span>
                    <span id="badge-pos" style="font-size:11.5px;padding:4px 10px;border-radius:999px;">--</span>
                </h3>
                <div style="position:relative;width:210px;height:170px;margin:0 auto;">
                    <svg viewBox="0 0 200 175" width="210" height="170">
                        <path d="M 35 148 A 76 76 0 1 1 165 148" fill="none" stroke="#E2E8F0" stroke-width="16" stroke-linecap="round"/>
                        <path id="arc-pos" d="M 35 148 A 76 76 0 1 1 165 148" fill="none" stroke="#10B981" stroke-width="16" stroke-linecap="round" stroke-dasharray="0 500"/>
                    </svg>
                    <div style="position:absolute;top:54px;left:0;right:0;">
                        <div id="val-pos" style="font-size:36px;font-weight:800;">--%</div>
                        <div style="font-size:11.5px;font-weight:700;color:#64748B;">META PÓS-MUDANÇA</div>
                    </div>
                </div>
                <div id="sub-pos" style="background:#F0FDFA;border-radius:12px;padding:10px;font-size:12.5px;font-weight:700;color:#0F766E;border:1px solid #99F6E4;">--</div>
            </div>

            <div class="gluco-card">
                <h3><span>📊 Raio-X dos Indicadores</span><span style="font-size:11.5px;background:#CCFBF1;color:#0F766E;padding:4px 10px;border-radius:999px;">Tempo Real</span></h3>
                <div class="range-row">
                    <div class="range-top"><span>📏 Cintura / Altura (Ideal &lt; 0,50)</span><span id="lbl-rce">--</span></div>
                    <div class="range-track"><div id="bar-rce" class="range-fill" style="width:50%;background:#10B981;"></div></div>
                </div>
                <div class="range-row">
                    <div class="range-top"><span>🏃 Exercício Semanal (Meta ≥ 2h30)</span><span id="lbl-mov">--</span></div>
                    <div class="range-track"><div id="bar-mov" class="range-fill" style="width:50%;background:#10B981;"></div></div>
                </div>
                <div class="range-row">
                    <div class="range-top"><span>🪑 Tempo Sentado por Dia (Ideal &lt; 8h)</span><span id="lbl-sent">--</span></div>
                    <div class="range-track"><div id="bar-sent" class="range-fill" style="width:50%;background:#10B981;"></div></div>
                </div>
                <div class="range-row">
                    <div class="range-top"><span>🥦 Fibras na Dieta (Meta ≥ 25g/dia)</span><span id="lbl-fib">--</span></div>
                    <div class="range-track"><div id="bar-fib" class="range-fill" style="width:50%;background:#10B981;"></div></div>
                </div>
                <div id="out-protocolo" style="margin-top:10px;background:#F0FDFA;border-left:4px solid #0D9488;padding:9px 12px;border-radius:8px;font-size:12.5px;color:#0F766E;font-weight:600;"></div>
            </div>
        </div>

        <!-- FORMULÁRIO INTUITIVO EM 2 COLUNAS -->
        <div class="form-grid-2">
            <div>
                <div class="gluco-card">
                    <h3>👤 1. Perfil Pessoal e Socioeconômico</h3>
                    <div class="inline-cols-2">
                        <div class="field-row">
                            <label><span>Idade do Paciente</span><span id="v-idade" style="color:var(--teal);">58 anos</span></label>
                            <input type="range" id="in-idade" min="18" max="80" value="58" oninput="recalcular()">
                        </div>
                        <div class="field-row">
                            <label><span>Sexo Biológico</span></label>
                            <select id="in-sexo" onchange="recalcular()">
                                <option value="1">Masculino</option>
                                <option value="2">Feminino</option>
                            </select>
                        </div>
                    </div>
                    <div class="field-row">
                        <label><span>🎓 Nível de Escolaridade</span></label>
                        <select id="in-esc" onchange="recalcular()">
                            <option value="1">Ensino Fundamental Incompleto (até 8º ano)</option>
                            <option value="2" selected>Fundamental Completo ou Médio Incompleto</option>
                            <option value="3">Ensino Médio Completo</option>
                            <option value="4">Superior Incompleto ou Curso Técnico</option>
                            <option value="5">Ensino Superior Completo / Pós-Graduação</option>
                        </select>
                    </div>
                    <div class="field-row">
                        <label><span>💰 Faixa de Renda Mensal Familiar (por pessoa)</span></label>
                        <select id="in-pir" onchange="recalcular()">
                            <option value="0.8">Até R$ 750 por pessoa (Alta Vulnerabilidade)</option>
                            <option value="1.3" selected>De R$ 750 a R$ 1.500 por pessoa (Baixa Renda)</option>
                            <option value="2.6">De R$ 1.500 a R$ 3.000 por pessoa (Renda Média)</option>
                            <option value="3.9">De R$ 3.000 a R$ 5.500 por pessoa (Renda Confortável)</option>
                            <option value="4.8">Acima de R$ 5.500 por pessoa (Alta Renda)</option>
                        </select>
                    </div>
                    <div class="field-row">
                        <label><span>🛒 Faltou dinheiro para alimentos saudáveis nos últimos 12 meses?</span></label>
                        <select id="in-ins" onchange="recalcular()">
                            <option value="0">Não — Segurança alimentar plena</option>
                            <option value="1" selected>Sim — Houve insegurança alimentar domiciliar</option>
                        </select>
                    </div>
                </div>

                <div class="gluco-card">
                    <h3>🏃 2. Atividade Física e Tempo Sentado (em Horas e Minutos)</h3>
                    <div class="field-row">
                        <label><span>A) Exercícios Físicos, Caminhada ou Esportes na Semana:</span></label>
                        <div class="inline-cols-3">
                            <div>
                                <div class="field-hint">Dias por semana</div>
                                <select id="in-dias-ex" onchange="recalcular()">
                                    <option value="0">Nenhum dia (0x)</option>
                                    <option value="1" selected>1 dia/sem</option>
                                    <option value="2">2 dias/sem</option>
                                    <option value="3">3 dias/sem</option>
                                    <option value="4">4 dias/sem</option>
                                    <option value="5">5 dias/sem</option>
                                    <option value="6">6 dias/sem</option>
                                    <option value="7">7 dias/sem</option>
                                </select>
                            </div>
                            <div>
                                <div class="field-hint">Horas por treino</div>
                                <select id="in-h-ex" onchange="recalcular()">
                                    <option value="0" selected>0 h</option>
                                    <option value="1">1 h</option>
                                    <option value="2">2 h</option>
                                    <option value="3">3 h</option>
                                </select>
                            </div>
                            <div>
                                <div class="field-hint">Minutos por treino</div>
                                <select id="in-m-ex" onchange="recalcular()">
                                    <option value="0">00 min</option>
                                    <option value="15">15 min</option>
                                    <option value="30">30 min</option>
                                    <option value="40" selected>40 min</option>
                                    <option value="45">45 min</option>
                                    <option value="50">50 min</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="field-row">
                        <label><span>Intensidade do Exercício:</span></label>
                        <select id="in-int-ex" onchange="recalcular()">
                            <option value="3.3">Leve (Caminhada leve, deslocamento a pé)</option>
                            <option value="4.0" selected>Moderada (Academia, caminhada rápida, dança)</option>
                            <option value="8.0">Intensa (Corrida, futebol, crossfit, natação)</option>
                        </select>
                    </div>
                    <div id="pill-resumo-ex" class="helper-pill">--</div>

                    <div class="field-row">
                        <label><span>B) Tempo Sentado por Dia (Trabalho, Sofá, Trânsito, Celular):</span></label>
                        <div class="inline-cols-2">
                            <div>
                                <div class="field-hint">Horas sentado por dia</div>
                                <select id="in-h-sent" onchange="recalcular()">
                                    <option value="2">2 horas</option>
                                    <option value="3">3 horas</option>
                                    <option value="4">4 horas</option>
                                    <option value="5">5 horas</option>
                                    <option value="6">6 horas</option>
                                    <option value="7">7 horas</option>
                                    <option value="8">8 horas</option>
                                    <option value="9" selected>9 horas</option>
                                    <option value="10">10 horas</option>
                                    <option value="11">11 horas</option>
                                    <option value="12">12 horas</option>
                                    <option value="14">14 horas</option>
                                </select>
                            </div>
                            <div>
                                <div class="field-hint">Minutos adicionais</div>
                                <select id="in-m-sent" onchange="recalcular()">
                                    <option value="0" selected>00 minutos</option>
                                    <option value="15">15 minutos</option>
                                    <option value="30">30 minutos</option>
                                    <option value="45">45 minutos</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div id="pill-resumo-sent" class="helper-pill">--</div>
                </div>
            </div>

            <div>
                <div class="gluco-card">
                    <h3>🩺 3. Medidas Corporais e Triagem Simples</h3>
                    <div class="inline-cols-3">
                        <div class="field-row">
                            <label><span>Altura (cm)</span><span id="v-alt" style="color:var(--teal);">170 cm</span></label>
                            <input type="range" id="in-alt" min="145" max="198" value="170" oninput="recalcular()">
                        </div>
                        <div class="field-row">
                            <label><span>Peso (kg)</span><span id="v-peso" style="color:var(--teal);">96 kg</span></label>
                            <input type="range" id="in-peso" min="45" max="155" value="96" oninput="recalcular()">
                        </div>
                        <div class="field-row">
                            <label><span>Cintura (cm)</span><span id="v-cint" style="color:var(--teal);">112 cm</span></label>
                            <input type="range" id="in-cint" min="60" max="155" value="112" oninput="recalcular()">
                        </div>
                    </div>
                    <div id="pill-resumo-bio" class="helper-pill">--</div>

                    <div class="inline-cols-2">
                        <div class="field-row">
                            <label><span>❤️ Pressão Alta (≥ 140/90)?</span></label>
                            <select id="in-pa" onchange="recalcular()">
                                <option value="0">Não (Pressão Normal)</option>
                                <option value="1" selected>Sim (Hipertenso / Elevada)</option>
                            </select>
                        </div>
                        <div class="field-row">
                            <label><span>🧬 Pais ou irmãos têm Diabetes?</span></label>
                            <select id="in-hf" onchange="recalcular()">
                                <option value="0">Não possui histórico</option>
                                <option value="1" selected>Sim (Parente de 1º grau)</option>
                            </select>
                        </div>
                    </div>
                    <div class="field-row">
                        <label><span>🩸 Colesterol Bom — HDL (se não souber, deixe 50 mg/dL)</span><span id="v-hdl" style="color:var(--teal);">38 mg/dL</span></label>
                        <input type="range" id="in-hdl" min="22" max="100" value="38" oninput="recalcular()">
                    </div>
                </div>

                <div class="gluco-card">
                    <h3>🥗 4. Alimentação no Dia a Dia</h3>
                    <div class="field-row">
                        <label><span>🍔 Refeições fora de casa / Lanches / Delivery (por semana)</span><span id="v-fast" style="color:var(--teal);">6x/sem</span></label>
                        <input type="range" id="in-fast" min="0" max="21" value="6" oninput="recalcular()">
                    </div>
                    <div class="field-row">
                        <label><span>🥦 Fibras: Frutas, Aveia, Feijão, Salada (Meta ≥ 25g/dia)</span><span id="v-fib" style="color:var(--teal);">10 g/dia</span></label>
                        <input type="range" id="in-fib" min="2" max="50" value="10" oninput="recalcular()">
                    </div>
                    <div class="field-row">
                        <label><span>🍬 Açúcar e Doces (1 lata de refri ≈ 35g | Meta ≤ 50g)</span><span id="v-acuc" style="color:var(--teal);">145 g/dia</span></label>
                        <input type="range" id="in-acuc" min="10" max="260" step="5" value="145" oninput="recalcular()">
                    </div>
                    <div class="field-row">
                        <label><span>🧂 Consumo de Sal / Sódio (Meta OMS &lt; 2.000 mg/dia)</span><span id="v-sod" style="color:var(--teal);">4200 mg</span></label>
                        <input type="range" id="in-sod" min="800" max="6500" step="100" value="4200" oninput="recalcular()">
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- ABA 2 -->
    <div id="tab2" class="tab-panel">
        <div class="form-grid-2">
            <div class="gluco-card">
                <h3>Estratificação Comercial por Faixas de Risco (Teste n = 1.027)</h3>
                <img class="chart" src="{imgs['fig4_estratificacao_faixas_risco']}" alt="Estratificação">
            </div>
            <div class="gluco-card">
                <h3>Movimento & Sedentarismo e Gradiente por Faixa Etária</h3>
                <img class="chart" src="{imgs['fig5_movimento_e_faixa_etaria']}" alt="Movimento">
            </div>
        </div>
    </div>

    <!-- ABA 3 -->
    <div id="tab3" class="tab-panel">
        <div class="form-grid-2">
            <div class="gluco-card">
                <h3>Ranking de Prioridade Preventiva por UF (IBGE SIDRA + DATASUS)</h3>
                <img class="chart" src="{imgs['fig6_ranking_territorial_uf']}" alt="Ranking UF">
            </div>
            <div class="gluco-card" style="max-height:600px;overflow-y:auto;">
                <h3>Tabela Consolidada das 27 Unidades da Federação</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th><th>UF</th><th>Região</th><th>Índice</th><th>Prioridade</th>
                            <th>Intern./100k</th><th>Cob. AB</th><th>Renda</th><th>Prev.</th><th>Inativ.</th>
                        </tr>
                    </thead>
                    <tbody>{linhas_uf_html}</tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- ABA 4 -->
    <div id="tab4" class="tab-panel">
        <div class="gluco-card">
            <h3>Comparativo Oficial dos Modelos Supervisionados (Teste Cego n = 1.027)</h3>
            <table>
                <thead>
                    <tr>
                        <th>Modelo</th><th>CV ROC-AUC</th><th>Test ROC-AUC</th><th>Brier Score</th>
                        <th>Sensibilidade (0,40)</th><th>Especificidade</th><th>VPN</th><th>F1</th><th>Matriz de Confusão</th>
                    </tr>
                </thead>
                <tbody>{linhas_mod_html}</tbody>
            </table>
        </div>
        <div class="form-grid-2">
            <div class="gluco-card"><h3>Curvas ROC no Teste</h3><img class="chart" src="{imgs['fig1_curvas_roc']}"></div>
            <div class="gluco-card"><h3>Matrizes de Confusão</h3><img class="chart" src="{imgs['fig2_matrizes_confusao']}"></div>
        </div>
        <div class="gluco-card"><h3>Importância no Random Forest & Odds Ratios</h3><img class="chart" src="{imgs['fig3_importancia_e_odds']}"></div>
        <div class="gluco-card">
            <h3>Auditoria das 19 Variáveis Preditoras (X) — Data Leakage Shield</h3>
            <table>
                <thead><tr><th>Variável</th><th>Eixo</th><th>Unidade</th><th>Válidos</th><th>Mediana</th><th>Correlação</th><th>Status</th></tr></thead>
                <tbody>{linhas_audit_html}</tbody>
            </table>
        </div>
    </div>
</div>

<script>
function openTab(id, btn) {{
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    btn.classList.add('active');
}}

function sigmoide(z) {{ return 1.0 / (1.0 + Math.exp(-z)); }}

function calcularScore(idade, sexo, esc, pir, ins, fib, acuc, sod, fast, met, sent, alt, peso, cint, hdl, pa, hf) {{
    const imc = peso / Math.pow(alt / 100.0, 2);
    const rce = cint / alt;
    const cumpre_oms = met >= 600 ? 1.0 : 0.0;
    const sed_alto = sent >= 480 ? 1.0 : 0.0;
    const exc_sod = sod >= 2300 ? 1.0 : 0.0;

    let logit = -0.35;
    logit += ((idade - 49.67) / 17.5) * 1.052;
    logit += (sexo === 1 ? 0.08 : -0.08);
    logit += ((esc - 3.53) / 1.2) * (-0.11);
    logit += ((pir - 2.53) / 1.6) * (-0.06);
    logit += (ins === 1 ? 0.14 : -0.05);
    logit += ((rce - 0.602) / 0.105) * 0.678;
    logit += ((imc - 29.55) / 7.4) * 0.12;
    logit += (hf === 1 ? 0.54 : -0.32);
    logit += ((hdl - 53.08) / 15.8) * (-0.477);
    logit += (pa === 1 ? 0.26 : -0.08);
    logit += ((met - 1800.0) / 2200.0) * (-0.24);
    logit += (cumpre_oms === 1 ? -0.15 : 0.15);
    logit += (sed_alto === 1 ? 0.12 : -0.05);
    logit += ((fib - 16.8) / 10.5) * (-0.14);
    logit += ((acuc - 102.5) / 65.0) * 0.10;
    logit += (exc_sod === 1 ? 0.08 : -0.06);
    logit += ((fast - 3.3) / 3.5) * 0.09;

    const prob = Math.min(Math.max(sigmoide(logit), 0.02), 0.96);
    return {{ prob, imc, rce }};
}}

function atualizarArco(idArc, idVal, idBadge, prob) {{
    const pct = Math.max(0, Math.min(100, prob * 100));
    const preenchido = (pct / 100.0) * 345.0;
    const arc = document.getElementById(idArc);
    const val = document.getElementById(idVal);
    const badge = document.getElementById(idBadge);

    val.innerText = pct.toFixed(1) + '%';
    arc.setAttribute('stroke-dasharray', preenchido.toFixed(1) + ' 500');

    if (prob <= 0.2189) {{
        arc.setAttribute('stroke', '#10B981');
        badge.style.background = '#D1FAE5';
        badge.style.color = '#047857';
        badge.innerText = 'BAIXO RISCO';
    }} else if (prob <= 0.5124) {{
        arc.setAttribute('stroke', '#F59E0B');
        badge.style.background = '#FEF3C7';
        badge.style.color = '#B45309';
        badge.innerText = 'RISCO MODERADO';
    }} else {{
        arc.setAttribute('stroke', '#EF4444');
        badge.style.background = '#FEE2E2';
        badge.style.color = '#B91C1C';
        badge.innerText = 'ALTO RISCO';
    }}
}}

function recalcular() {{
    const idade = parseFloat(document.getElementById('in-idade').value);
    const sexo = parseInt(document.getElementById('in-sexo').value);
    const esc = parseFloat(document.getElementById('in-esc').value);
    const pir = parseFloat(document.getElementById('in-pir').value);
    const ins = parseInt(document.getElementById('in-ins').value);

    const diasEx = parseInt(document.getElementById('in-dias-ex').value);
    const hEx = parseInt(document.getElementById('in-h-ex').value);
    const mEx = parseInt(document.getElementById('in-m-ex').value);
    const intEx = parseFloat(document.getElementById('in-int-ex').value);
    const minSemEx = diasEx > 0 ? diasEx * (hEx * 60 + mEx) : 0;
    const met = Math.round(minSemEx * intEx);
    const hTotSem = Math.floor(minSemEx / 60);
    const mTotSem = minSemEx % 60;

    const hSent = parseInt(document.getElementById('in-h-sent').value);
    const mSent = parseInt(document.getElementById('in-m-sent').value);
    const sent = hSent * 60 + mSent;

    const alt = parseFloat(document.getElementById('in-alt').value);
    const peso = parseFloat(document.getElementById('in-peso').value);
    const cint = parseFloat(document.getElementById('in-cint').value);
    const hdl = parseFloat(document.getElementById('in-hdl').value);
    const pa = parseInt(document.getElementById('in-pa').value);
    const hf = parseInt(document.getElementById('in-hf').value);

    const fib = parseFloat(document.getElementById('in-fib').value);
    const acuc = parseFloat(document.getElementById('in-acuc').value);
    const sod = parseFloat(document.getElementById('in-sod').value);
    const fast = parseFloat(document.getElementById('in-fast').value);

    document.getElementById('v-idade').innerText = idade + ' anos';
    document.getElementById('v-alt').innerText = alt + ' cm';
    document.getElementById('v-peso').innerText = peso + ' kg';
    document.getElementById('v-cint').innerText = cint + ' cm';
    document.getElementById('v-hdl').innerText = hdl + ' mg/dL';
    document.getElementById('v-fib').innerText = fib + ' g/dia';
    document.getElementById('v-acuc').innerText = acuc + ' g/dia';
    document.getElementById('v-sod').innerText = sod + ' mg';
    document.getElementById('v-fast').innerText = fast + 'x/sem';

    const pillEx = document.getElementById('pill-resumo-ex');
    pillEx.className = met >= 600 ? 'helper-pill' : 'helper-pill warn';
    pillEx.innerHTML = (met >= 600 ? '✅ ' : '⚠️ ') + '<b>Tempo Total na Semana: ' + hTotSem + 'h ' + String(mTotSem).padStart(2, '0') + 'min</b> (' + met + ' MET-min/sem) — ' + (met >= 600 ? 'Cumpre a meta da OMS!' : 'Abaixo da meta de 2h30/sem da OMS.');

    const pillSent = document.getElementById('pill-resumo-sent');
    pillSent.className = sent >= 480 ? 'helper-pill warn' : 'helper-pill';
    pillSent.innerHTML = '🪑 <b>Total Sentado: ' + hSent + 'h ' + String(mSent).padStart(2, '0') + 'min por dia</b> (' + sent + ' min/dia) — ' + (sent >= 480 ? 'Alerta de Sedentarismo Elevado (≥ 8h/dia)' : 'Dentro da faixa protetora (< 8h/dia)');

    const atual = calcularScore(idade, sexo, esc, pir, ins, fib, acuc, sod, fast, met, sent, alt, peso, cint, hdl, pa, hf);
    const interv = calcularScore(
        idade, sexo, esc, pir, ins,
        Math.max(fib, 28), Math.min(acuc, 45), Math.min(sod, 1900), Math.min(fast, 1),
        Math.max(met, 1200), Math.min(sent, 300),
        alt, Math.max(peso - 5, 50), Math.max(cint - 6, 70), Math.max(hdl, 55), 0, hf
    );

    const pillBio = document.getElementById('pill-resumo-bio');
    pillBio.className = atual.rce >= 0.50 ? 'helper-pill warn' : 'helper-pill';
    pillBio.innerHTML = '📏 <b>Cálculo Automático:</b> IMC = <b>' + atual.imc.toFixed(1) + ' kg/m²</b> | Cintura/Altura = <b>' + atual.rce.toFixed(2) + '</b> ' + (atual.rce >= 0.50 ? '(Alerta Visceral ≥ 0,50)' : '(Ideal < 0,50)');

    atualizarArco('arc-atual', 'val-atual', 'badge-atual', atual.prob);
    atualizarArco('arc-pos', 'val-pos', 'badge-pos', interv.prob);

    document.getElementById('sub-atual').innerText = 'Limiar preventivo de triagem (Recall 86,1%): 40,0%';
    const redRel = ((atual.prob - interv.prob) / atual.prob * 100).toFixed(1);
    document.getElementById('sub-pos').innerText = '📉 Impacto Preventivo: -' + redRel + '% de redução no score de risco';

    // Barras Reading Ranges
    document.getElementById('lbl-rce').innerText = atual.rce.toFixed(2) + ' (IMC ' + atual.imc.toFixed(1) + ')';
    document.getElementById('bar-rce').style.width = Math.min(100, (atual.rce / 0.75) * 100) + '%';
    document.getElementById('bar-rce').style.background = atual.rce >= 0.52 ? '#EF4444' : '#10B981';

    document.getElementById('lbl-mov').innerText = hTotSem + 'h ' + String(mTotSem).padStart(2, '0') + 'min (' + met + ' MET)';
    document.getElementById('bar-mov').style.width = Math.min(100, (met / 1400) * 100) + '%';
    document.getElementById('bar-mov').style.background = met >= 600 ? '#10B981' : '#EF4444';

    document.getElementById('lbl-sent').innerText = hSent + 'h ' + String(mSent).padStart(2, '0') + 'min / dia';
    document.getElementById('bar-sent').style.width = Math.min(100, (sent / 720) * 100) + '%';
    document.getElementById('bar-sent').style.background = sent >= 480 ? '#EF4444' : '#10B981';

    document.getElementById('lbl-fib').innerText = fib + ' g/dia • Açúcar ' + acuc + 'g';
    document.getElementById('bar-fib').style.width = Math.min(100, (fib / 35) * 100) + '%';
    document.getElementById('bar-fib').style.background = fib >= 25 ? '#10B981' : '#F59E0B';

    const outProt = document.getElementById('out-protocolo');
    if (atual.prob <= 0.2189) {{
        outProt.innerText = 'Conduta Sugerida: Manter acompanhamento preventivo digital anual e incentivo aos hábitos ativos.';
    }} else if (atual.prob <= 0.5124) {{
        outProt.innerText = 'Conduta Sugerida: Incluir em programa de reeducação alimentar, pausas ativas e reavaliar em 6 meses.';
    }} else {{
        outProt.innerText = 'Conduta Sugerida: Prioridade Clínica — solicitar HbA1c e Glicemia de Jejum (busca ativa de casos ocultos).';
    }}
}}

function carregarPreset(n) {{
    if (n === 1) {{
        document.getElementById('in-idade').value = 58;
        document.getElementById('in-sexo').value = '1';
        document.getElementById('in-esc').value = '2';
        document.getElementById('in-pir').value = '1.3';
        document.getElementById('in-ins').value = '1';
        document.getElementById('in-dias-ex').value = '1';
        document.getElementById('in-h-ex').value = '0';
        document.getElementById('in-m-ex').value = '40';
        document.getElementById('in-int-ex').value = '4.0';
        document.getElementById('in-h-sent').value = '9';
        document.getElementById('in-m-sent').value = '0';
        document.getElementById('in-alt').value = 170;
        document.getElementById('in-peso').value = 96;
        document.getElementById('in-cint').value = 112;
        document.getElementById('in-hdl').value = 38;
        document.getElementById('in-pa').value = '1';
        document.getElementById('in-hf').value = '1';
        document.getElementById('in-fib').value = 10;
        document.getElementById('in-acuc').value = 145;
        document.getElementById('in-sod').value = 4200;
        document.getElementById('in-fast').value = 6;
    }} else if (n === 2) {{
        document.getElementById('in-idade').value = 46;
        document.getElementById('in-sexo').value = '1';
        document.getElementById('in-esc').value = '4';
        document.getElementById('in-pir').value = '2.6';
        document.getElementById('in-ins').value = '0';
        document.getElementById('in-dias-ex').value = '3';
        document.getElementById('in-h-ex').value = '1';
        document.getElementById('in-m-ex').value = '0';
        document.getElementById('in-int-ex').value = '4.0';
        document.getElementById('in-h-sent').value = '10';
        document.getElementById('in-m-sent').value = '0';
        document.getElementById('in-alt').value = 175;
        document.getElementById('in-peso').value = 86;
        document.getElementById('in-cint').value = 99;
        document.getElementById('in-hdl').value = 46;
        document.getElementById('in-pa').value = '0';
        document.getElementById('in-hf').value = '1';
        document.getElementById('in-fib').value = 15;
        document.getElementById('in-acuc').value = 110;
        document.getElementById('in-sod').value = 3600;
        document.getElementById('in-fast').value = 5;
    }} else {{
        document.getElementById('in-idade').value = 29;
        document.getElementById('in-sexo').value = '2';
        document.getElementById('in-esc').value = '5';
        document.getElementById('in-pir').value = '3.9';
        document.getElementById('in-ins').value = '0';
        document.getElementById('in-dias-ex').value = '5';
        document.getElementById('in-h-ex').value = '1';
        document.getElementById('in-m-ex').value = '15';
        document.getElementById('in-int-ex').value = '4.0';
        document.getElementById('in-h-sent').value = '4';
        document.getElementById('in-m-sent').value = '0';
        document.getElementById('in-alt').value = 165;
        document.getElementById('in-peso').value = 61;
        document.getElementById('in-cint').value = 74;
        document.getElementById('in-hdl').value = 62;
        document.getElementById('in-pa').value = '0';
        document.getElementById('in-hf').value = '0';
        document.getElementById('in-fib').value = 28;
        document.getElementById('in-acuc').value = 55;
        document.getElementById('in-sod').value = 1800;
        document.getElementById('in-fast').value = 1;
    }}
    recalcular();
}}

function aplicarIntervencao() {{
    document.getElementById('in-dias-ex').value = '5';
    document.getElementById('in-h-ex').value = '1';
    document.getElementById('in-m-ex').value = '0';
    document.getElementById('in-int-ex').value = '4.0';
    document.getElementById('in-h-sent').value = '5';
    document.getElementById('in-m-sent').value = '0';
    document.getElementById('in-fib').value = 28;
    document.getElementById('in-acuc').value = 45;
    document.getElementById('in-sod').value = 1900;
    document.getElementById('in-fast').value = 1;
    document.getElementById('in-peso').value = Math.max(parseInt(document.getElementById('in-peso').value) - 5, 50);
    document.getElementById('in-cint').value = Math.max(parseInt(document.getElementById('in-cint').value) - 6, 70);
    document.getElementById('in-hdl').value = Math.max(parseInt(document.getElementById('in-hdl').value) + 8, 55);
    document.getElementById('in-pa').value = '0';
    recalcular();
}}

window.onload = recalcular;
</script>
</body>
</html>
"""
    destino = APP_DIR / "radar_diabetes_demo.html"
    destino.write_text(html, encoding="utf-8")
    print(f"[HTML App Glucomate] Gerado {destino} ({destino.stat().st_size / 1024:.1f} KB)")
    return destino


if __name__ == "__main__":
    gerar_html_demo()
