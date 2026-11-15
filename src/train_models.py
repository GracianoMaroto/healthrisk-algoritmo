"""
Módulo de Treinamento, Validação Cruzada, Calibração de Limiares e Geração de Artefatos Visuais.
Implementa as especificações do Bloco 1 (Slides 8 a 11) e Bloco 2 (Seções 3.7, 3.10 e 4.7):
- Corte 80/20 estratificado com random_state=42 fixo
- Imputação estratificada por sexo e faixa etária ajustada estritamente no treino (zero vazamento)
- Treinamento dos 3 algoritmos: Regressão Logística, Árvore de Decisão e Random Forest
- Priorização metodológica da Sensibilidade (Recall) para mitigação de Falsos Negativos
- Estratificação em faixas de risco (Baixo, Moderado, Alto) via tercis da probabilidade de treino
- Geração dos gráficos executivos e matrizes de confusão em reports/figures/
"""

from __future__ import annotations

import json
from pathlib import Path
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, export_text

from src.features import (
    FEATURES_MODELO_X,
    VARIAVEIS_BLOQUEADAS_VAZAMENTO,
    StratifiedMedianImputer,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
MODELS_DIR = ROOT_DIR / "models"
FIGURES_DIR = ROOT_DIR / "reports" / "figures"
TABLES_DIR = ROOT_DIR / "reports" / "tables"

RANDOM_STATE = 42

NOMES_AMIGAVEIS: dict[str, str] = {
    "idade_anos": "Idade (anos)",
    "sexo": "Sexo Biológico",
    "escolaridade_ord": "Escolaridade (1-5)",
    "razao_renda_pobreza": "Razão Renda/Pobreza (PIR)",
    "inseguranca_alimentar": "Insegurança Alimentar",
    "densidade_acucar": "Densidade de Açúcar (g/1000kcal)",
    "densidade_fibra": "Densidade de Fibra (g/1000kcal)",
    "excesso_sodio": "Excesso de Sódio (>=2300mg)",
    "indice_qualidade_dieta": "Índice de Qualidade da Dieta",
    "refeicao_pronta": "Refeições Fora/Fast-Food (sem)",
    "met_min_semana": "Volume Físico (MET-min/sem)",
    "cumpre_oms_150": "Cumpre Meta OMS (150 min/sem)",
    "minutos_sentado": "Tempo Sentado (min/dia)",
    "sedentarismo_alto": "Sedentarismo Alto (>=8h/dia)",
    "imc": "IMC (kg/m²)",
    "razao_cintura_estatura": "Razão Cintura/Estatura (RCE)",
    "pressao_alta": "Pressão Arterial Elevada (>=140/90)",
    "hdl": "Colesterol HDL (mg/dL)",
    "historico_familiar_diabetes": "Histórico Familiar de Diabetes",
}


def _recalcular_indice_dieta_sem_vazamento(
    df_full: pd.DataFrame, idx_train: pd.Index
) -> tuple[pd.DataFrame, dict]:
    """
    Recalcula a coluna indice_qualidade_dieta usando estritamente as médias e desvios
    padrão do subconjunto de treino (Quadro 8 do Bloco 2).
    """
    df = df_full.copy()
    cols_dieta = ["fibra_g_dia", "acucar_g_dia", "sodio_mg_dia", "gordura_sat_g_dia"]
    params_treino = {}
    z_cols = {}
    for c in cols_dieta:
        media_tr = float(df.loc[idx_train, c].mean())
        std_tr = float(df.loc[idx_train, c].std(ddof=0))
        params_treino[c] = {"media_treino": round(media_tr, 4), "std_treino": round(std_tr, 4)}
        z_cols[c] = (df[c] - media_tr) / std_tr

    df["indice_qualidade_dieta"] = (
        z_cols["fibra_g_dia"]
        - z_cols["acucar_g_dia"]
        - z_cols["sodio_mg_dia"]
        - z_cols["gordura_sat_g_dia"]
    ) / 4.0
    return df, params_treino


def avaliar_classificador(
    nome: str,
    pipeline: Pipeline,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    limiar_decisao: float = 0.40,
) -> dict:
    """
    Executa validação cruzada 5-fold no treino e avalia no conjunto de teste tanto no
    limiar padrão (0.50) quanto no limiar calibrado para triagem preventiva (0.40),
    onde a prioridade é maximizar o Recall (Sensibilidade).
    """
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    cv_scores = cross_validate(
        pipeline,
        X_train,
        y_train,
        cv=cv,
        scoring=["roc_auc", "recall", "precision", "f1"],
        n_jobs=1,
    )

    pipeline.fit(X_train, y_train)
    prob_train = pipeline.predict_proba(X_train)[:, 1]
    prob_test = pipeline.predict_proba(X_test)[:, 1]

    # Avaliação no limiar clínico de rastreio (limiar_decisao) e no limiar 0.50
    pred_padrao = (prob_test >= 0.50).astype(int)
    pred_rastreio = (prob_test >= limiar_decisao).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_test, pred_rastreio).ravel()
    tn50, fp50, fn50, tp50 = confusion_matrix(y_test, pred_padrao).ravel()

    especificidade = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    vpn = tn / (tn + fn) if (tn + fn) > 0 else 0.0
    vpp = tp / (tp + fp) if (tp + fp) > 0 else 0.0

    return {
        "modelo": nome,
        "cv_roc_auc_mean": round(float(np.mean(cv_scores["test_roc_auc"])), 4),
        "cv_roc_auc_std": round(float(np.std(cv_scores["test_roc_auc"])), 4),
        "cv_recall_mean": round(float(np.mean(cv_scores["test_recall"])), 4),
        "cv_f1_mean": round(float(np.mean(cv_scores["test_f1"])), 4),
        "test_roc_auc": round(float(roc_auc_score(y_test, prob_test)), 4),
        "test_pr_auc": round(float(average_precision_score(y_test, prob_test)), 4),
        "test_brier_score": round(float(brier_score_loss(y_test, prob_test)), 4),
        # Métricas no limiar padrão 0.50
        "limiar_050": {
            "accuracy": round(float(accuracy_score(y_test, pred_padrao)), 4),
            "recall_sensibilidade": round(float(recall_score(y_test, pred_padrao)), 4),
            "especificidade": round(float(tn50 / (tn50 + fp50)), 4),
            "precision_vpp": round(float(precision_score(y_test, pred_padrao)), 4),
            "f1_score": round(float(f1_score(y_test, pred_padrao)), 4),
            "tp": int(tp50),
            "fp": int(fp50),
            "tn": int(tn50),
            "fn": int(fn50),
        },
        # Métricas no limiar calibrado para triagem preventiva (prioridade Recall)
        "limiar_rastreio": {
            "limiar": limiar_decisao,
            "accuracy": round(float(accuracy_score(y_test, pred_rastreio)), 4),
            "recall_sensibilidade": round(float(recall_score(y_test, pred_rastreio)), 4),
            "especificidade": round(float(especificidade), 4),
            "precision_vpp": round(float(vpp), 4),
            "vpn": round(float(vpn), 4),
            "f1_score": round(float(f1_score(y_test, pred_rastreio)), 4),
            "tp": int(tp),
            "fp": int(fp),
            "tn": int(tn),
            "fn": int(fn),
        },
        "_prob_train": prob_train,
        "_prob_test": prob_test,
    }


def gerar_graficos_executivos(
    df_analytic: pd.DataFrame,
    resultados: dict[str, dict],
    y_test: pd.Series,
    df_importancia: pd.DataFrame,
    df_odds: pd.DataFrame,
    df_faixas_teste: pd.DataFrame,
    df_terr: pd.DataFrame,
) -> None:
    """Gera figuras em alta definição (300 DPI) com a paleta visual executiva do Bloco 1."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "figure.facecolor": "#FAF9F5",
        "axes.facecolor": "#FFFFFF",
        "axes.edgecolor": "#CCCCCC",
    })
    COR_AZUL = "#142D4C"
    COR_VERDE = "#008B5E"
    COR_LARANJA = "#D96B27"
    COR_VERMELHO = "#B8332A"

    # 1. Curvas ROC Comparativas dos 3 Modelos
    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=300)
    cores_mod = {
        "Regressão Logística": COR_AZUL,
        "Árvore de Decisão": COR_LARANJA,
        "Random Forest": COR_VERDE,
    }
    for nome, res in resultados.items():
        fpr, tpr, _ = roc_curve(y_test, res["_prob_test"])
        auc_val = res["test_roc_auc"]
        ax.plot(
            fpr, tpr, lw=2.5, color=cores_mod[nome],
            label=f"{nome} (ROC-AUC = {auc_val:.3f})",
        )
    ax.plot([0, 1], [0, 1], linestyle="--", color="#888888", lw=1.2, label="Classificador Aleatório (0.500)")
    ax.set_title("Curvas ROC no Conjunto de Teste (n = 1.027 | Sem Vazamento de Dados)")
    ax.set_xlabel("Taxa de Falsos Positivos (1 - Especificidade)")
    ax.set_ylabel("Taxa de Verdadeiros Positivos (Sensibilidade / Recall)")
    ax.legend(loc="lower right", frameon=True)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig1_curvas_roc.png", dpi=300)
    plt.close(fig)

    # 2. Matrizes de Confusão Lado a Lado (Limiar de Triagem Preventiva)
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.3), dpi=300)
    for ax, (nome, res) in zip(axes, resultados.items()):
        m = res["limiar_rastreio"]
        matriz = np.array([[m["tn"], m["fp"]], [m["fn"], m["tp"]]])
        annot = np.array([
            [f"VN\n{m['tn']}\n(Seguro)", f"FP\n{m['fp']}\n(Rastreio Extra)"],
            [f"FN\n{m['fn']}\n(Ponto Cego)", f"VP\n{m['tp']}\n(Capturado)"],
        ])
        sns.heatmap(
            matriz, annot=annot, fmt="", cmap="YlGnBu", cbar=False, ax=ax,
            xticklabels=["Pred: Seguro", "Pred: Risco"],
            yticklabels=["Real: Seguro", "Real: Diabetes"],
            annot_kws={"size": 10, "weight": "bold"},
        )
        ax.set_title(f"{nome}\nRecall = {m['recall_sensibilidade']*100:.1f}% | AUC = {res['test_roc_auc']:.3f}")
    fig.suptitle("Matrizes de Confusão no Teste (Limiar de Rastreio Preventivo = 0,40)", fontsize=13, fontweight="bold", y=1.03)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig2_matrizes_confusao.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # 3. Importância das Variáveis (Random Forest) e Odds Ratios (Regressão Logística)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 6), dpi=300)
    df_imp_plot = df_importancia.sort_values("importancia_rf", ascending=True).tail(12)
    ax1.barh(df_imp_plot["nome_amigavel"], df_imp_plot["importancia_rf"] * 100, color=COR_VERDE, edgecolor=COR_AZUL)
    ax1.set_title("Top 12 Variáveis no Random Forest (Importância %)", fontsize=11)
    ax1.set_xlabel("Importância na Redução de Impureza (%)")
    ax1.grid(axis="x", alpha=0.25)

    df_odds_plot = df_odds.sort_values("odds_ratio", ascending=True)
    cores_or = [COR_VERMELHO if v > 1.0 else COR_AZUL for v in df_odds_plot["odds_ratio"]]
    ax2.barh(df_odds_plot["nome_amigavel"], df_odds_plot["odds_ratio"], color=cores_or, alpha=0.88)
    ax2.axvline(1.0, color="#222222", linestyle="--", lw=1.3)
    ax2.set_title("Odds Ratio Padronizado (Regressão Logística)", fontsize=11)
    ax2.set_xlabel("Odds Ratio por 1 DP (>1 eleva risco | <1 efeito protetor)")
    ax2.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig3_importancia_e_odds.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    # 4. Estratificação Comercial em Faixas de Risco (Tercis Calibrados no Treino Aplicados ao Teste)
    fig, ax = plt.subplots(figsize=(8.5, 5), dpi=300)
    cores_faixa = [COR_VERDE, COR_LARANJA, COR_VERMELHO]
    barras = ax.bar(
        df_faixas_teste["faixa_risco"],
        df_faixas_teste["prevalencia_real_pct"],
        color=cores_faixa,
        width=0.55,
        edgecolor=COR_AZUL,
    )
    for bar, (_, row) in zip(barras, df_faixas_teste.iterrows()):
        altura = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            altura + 1.0,
            f"{altura:.1f}% de casos reais\n({int(row['n_casos_reais'])}/{int(row['n_individuos'])} indiv.)\n Captura: {row['pct_total_diabeticos_capturados']:.1f}% do total",
            ha="center", va="bottom", fontsize=9.5, fontweight="bold",
        )
    ax.set_ylim(0, max(df_faixas_teste["prevalencia_real_pct"]) + 12)
    ax.set_title("Validação Comercial: Prevalência Real de Diabetes por Faixa de Risco no Teste")
    ax.set_ylabel("Prevalência Real de Diabetes na Faixa (%)")
    ax.set_xlabel("Faixa Metodológica de Risco (Tercis Calibrados no Conjunto de Treino)")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig4_estratificacao_faixas_risco.png", dpi=300)
    plt.close(fig)

    # 5. Perfil de Movimento (Eixo 2) e Faixa Etária vs Prevalência de Diabetes
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5), dpi=300)
    ordem_mov = [
        "Ativo & Pouco Sentado",
        "Ativo & Muito Sentado",
        "Inativo & Pouco Sentado",
        "Inativo & Muito Sentado",
    ]
    df_mov = (
        df_analytic[df_analytic["perfil_movimento"].isin(ordem_mov)]
        .groupby("perfil_movimento")["diabetes"]
        .agg(["count", "mean"])
        .reindex(ordem_mov)
    )
    df_mov["pct"] = df_mov["mean"] * 100
    b1 = ax1.bar(
        range(len(df_mov)), df_mov["pct"],
        color=[COR_VERDE, "#4FA37A", COR_LARANJA, COR_VERMELHO],
        edgecolor=COR_AZUL,
    )
    ax1.set_xticks(range(len(df_mov)))
    ax1.set_xticklabels([s.replace(" & ", "\n&\n") for s in ordem_mov], fontsize=9)
    for bar, (_, r) in zip(b1, df_mov.iterrows()):
        ax1.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.6,
            f"{r['pct']:.1f}%\n(n={int(r['count'])})", ha="center", fontsize=9, fontweight="bold",
        )
    ax1.set_ylim(0, max(df_mov["pct"]) + 6)
    ax1.set_title("Eixo 2: Prevalência por Perfil de Movimento e Sedentarismo")
    ax1.set_ylabel("Prevalência de Diabetes (%)")
    ax1.grid(axis="y", alpha=0.25)

    ordem_id = ["18-29", "30-44", "45-59", "60+"]
    df_id = df_analytic.groupby("faixa_etaria")["diabetes"].agg(["count", "mean"]).reindex(ordem_id)
    df_id["pct"] = df_id["mean"] * 100
    b2 = ax2.bar(ordem_id, df_id["pct"], color=COR_AZUL, edgecolor=COR_VERDE, width=0.55)
    for bar, (_, r) in zip(b2, df_id.iterrows()):
        ax2.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.6,
            f"{r['pct']:.1f}%\n(n={int(r['count'])})", ha="center", fontsize=9, fontweight="bold",
        )
    ax2.set_ylim(0, max(df_id["pct"]) + 6)
    ax2.set_title("Gradiente Demográfico: Prevalência por Faixa Etária")
    ax2.set_xlabel("Faixa Etária (anos)")
    ax2.set_ylabel("Prevalência de Diabetes (%)")
    ax2.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig5_movimento_e_faixa_etaria.png", dpi=300)
    plt.close(fig)

    # 6. Camada Territorial Brasileira (Top 15 UFs por Índice de Vulnerabilidade — IBGE + DATASUS)
    fig, ax = plt.subplots(figsize=(10.5, 5.5), dpi=300)
    top_uf = df_terr.sort_values("indice_contexto_territorial", ascending=True).tail(15)
    cores_uf = [
        COR_VERMELHO if p == "Prioridade Crítica" else (COR_LARANJA if p == "Atenção Tática" else COR_VERDE)
        for p in top_uf["prioridade_territorial"]
    ]
    ax.barh(
        top_uf["uf"] + " - " + top_uf["nome_uf"],
        top_uf["indice_contexto_territorial"],
        color=cores_uf,
        edgecolor=COR_AZUL,
    )
    ax.axvline(0.0, color="#333333", linestyle="--", lw=1.0)
    ax.set_title("Camada Territorial (Nível B): Ranking de UFs por Vulnerabilidade (IBGE + DATASUS)", fontsize=11)
    ax.set_xlabel("Índice Composto de Vulnerabilidade Territorial (z-score: Renda, SIH/SUS, Cobertura AB, Inatividade)")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig6_ranking_territorial_uf.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def executar_treinamento() -> dict:
    """
    Executa todo o fluxo de modelagem e avaliação do Bloco 3, salva os modelos
    serializados (.joblib), tabelas de métricas e figuras de alta resolução.
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(PROCESSED_DIR / "analytic.parquet")
    df_terr = pd.read_parquet(PROCESSED_DIR / "territorial_uf.parquet")

    # Confirma blindagem contra vazamento antes do split
    assert len(set(FEATURES_MODELO_X) & set(VARIAVEIS_BLOQUEADAS_VAZAMENTO)) == 0

    # 1. Corte treino/teste 80/20 estratificado pelo alvo com random_state=42
    indices_treino, indices_teste = train_test_split(
        df.index,
        test_size=0.20,
        stratify=df["diabetes"],
        random_state=RANDOM_STATE,
    )

    # 2. Recalcula indice_qualidade_dieta ajustado estritamente nas estatísticas do treino!
    df, params_dieta_treino = _recalcular_indice_dieta_sem_vazamento(df, indices_treino)
    df["particao"] = np.where(df.index.isin(indices_treino), "treino", "teste")

    X_train = df.loc[indices_treino, FEATURES_MODELO_X].copy()
    y_train = df.loc[indices_treino, "diabetes"].copy()
    X_test = df.loc[indices_teste, FEATURES_MODELO_X].copy()
    y_test = df.loc[indices_teste, "diabetes"].copy()

    # 3. Construção dos Pipelines dos 3 Modelos (Bloco 1 Slide 8 e Bloco 2 Seção 3.7/3.10)
    pipe_lr = Pipeline([
        ("imputer", StratifiedMedianImputer(FEATURES_MODELO_X)),
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(class_weight="balanced", max_iter=1000, C=0.5, random_state=RANDOM_STATE)),
    ])

    pipe_dt = Pipeline([
        ("imputer", StratifiedMedianImputer(FEATURES_MODELO_X)),
        ("clf", DecisionTreeClassifier(
            class_weight="balanced",
            max_depth=5,
            min_samples_leaf=40,
            random_state=RANDOM_STATE,
        )),
    ])

    pipe_rf = Pipeline([
        ("imputer", StratifiedMedianImputer(FEATURES_MODELO_X)),
        ("clf", RandomForestClassifier(
            n_estimators=300,
            max_depth=8,
            min_samples_leaf=20,
            class_weight="balanced_subsample",
            random_state=RANDOM_STATE,
            n_jobs=1,
        )),
    ])

    modelos = {
        "Regressão Logística": pipe_lr,
        "Árvore de Decisão": pipe_dt,
        "Random Forest": pipe_rf,
    }

    resultados: dict[str, dict] = {}
    for nome, pipe in modelos.items():
        res = avaliar_classificador(nome, pipe, X_train, y_train, X_test, y_test, limiar_decisao=0.40)
        resultados[nome] = res
        m_ras = res["limiar_rastreio"]
        print(
            f"[Modelo] {nome:<20} | CV AUC={res['cv_roc_auc_mean']:.4f} | Test AUC={res['test_roc_auc']:.4f} "
            f"| Recall(0.40)={m_ras['recall_sensibilidade']*100:.1f}% | F1={m_ras['f1_score']:.4f}"
        )

    # Salva os modelos treinados
    joblib.dump(pipe_lr, MODELS_DIR / "logistic_regression.joblib")
    joblib.dump(pipe_dt, MODELS_DIR / "decision_tree.joblib")
    joblib.dump(pipe_rf, MODELS_DIR / "random_forest.joblib")

    # Exporta regras interpretáveis da Árvore de Decisão (White-box até nível 3)
    regras_arvore = export_text(
        pipe_dt.named_steps["clf"],
        feature_names=FEATURES_MODELO_X,
        max_depth=3,
    )
    (PROCESSED_DIR / "regras_arvore_decisao.txt").write_text(regras_arvore, encoding="utf-8")

    # 4. Extração de Importância das Variáveis (RF + DT) e Odds Ratios (LR)
    coefs_lr = pipe_lr.named_steps["clf"].coef_[0]
    imp_rf = pipe_rf.named_steps["clf"].feature_importances_
    imp_dt = pipe_dt.named_steps["clf"].feature_importances_

    df_importancia = pd.DataFrame({
        "feature": FEATURES_MODELO_X,
        "nome_amigavel": [NOMES_AMIGAVEIS[f] for f in FEATURES_MODELO_X],
        "importancia_rf": np.round(imp_rf, 4),
        "importancia_dt": np.round(imp_dt, 4),
        "coef_logistico_padronizado": np.round(coefs_lr, 4),
        "odds_ratio": np.round(np.exp(coefs_lr), 4),
    }).sort_values("importancia_rf", ascending=False)
    df_importancia.to_csv(TABLES_DIR / "importancia_e_odds_modelos.csv", index=False, encoding="utf-8")

    # 5. Calibração das Faixas de Risco (Baixo / Moderado / Alto) pelos tercis do treino (Seção 4.7 Bloco 2)
    prob_rf_train = resultados["Random Forest"]["_prob_train"]
    prob_rf_test = resultados["Random Forest"]["_prob_test"]

    q33, q67 = [float(x) for x in np.quantile(prob_rf_train, [1 / 3, 2 / 3])]

    # Aplica probabilidades e faixas ao dataset analítico completo
    df["prob_risco_rf"] = np.nan
    df.loc[indices_treino, "prob_risco_rf"] = np.round(prob_rf_train, 4)
    df.loc[indices_teste, "prob_risco_rf"] = np.round(prob_rf_test, 4)

    df["prob_risco_lr"] = np.nan
    df.loc[indices_treino, "prob_risco_lr"] = np.round(resultados["Regressão Logística"]["_prob_train"], 4)
    df.loc[indices_teste, "prob_risco_lr"] = np.round(resultados["Regressão Logística"]["_prob_test"], 4)

    df["faixa_risco"] = pd.cut(
        df["prob_risco_rf"],
        bins=[-np.inf, q33, q67, np.inf],
        labels=["Baixo Risco", "Risco Moderado", "Alto Risco"],
    ).astype(str)

    # Atualiza analytic.parquet com as predições e partição auditável
    df.to_parquet(PROCESSED_DIR / "analytic.parquet", index=False)
    df.to_csv(PROCESSED_DIR / "analytic.csv", index=False, encoding="utf-8")

    # Tabela de performance por faixa de risco no conjunto de teste
    df_test_eval = df.loc[indices_teste].copy()
    total_diab_teste = int(df_test_eval["diabetes"].sum())
    linhas_faixa = []
    for faixa in ["Baixo Risco", "Risco Moderado", "Alto Risco"]:
        sub = df_test_eval[df_test_eval["faixa_risco"] == faixa]
        n_ind = len(sub)
        n_casos = int(sub["diabetes"].sum())
        linhas_faixa.append({
            "faixa_risco": faixa,
            "n_individuos": n_ind,
            "n_casos_reais": n_casos,
            "prevalencia_real_pct": round((n_casos / n_ind) * 100, 2) if n_ind > 0 else 0.0,
            "pct_total_diabeticos_capturados": round((n_casos / total_diab_teste) * 100, 2),
            "prob_media_estimada": round(float(sub["prob_risco_rf"].mean()), 4),
        })
    df_faixas_teste = pd.DataFrame(linhas_faixa)
    df_faixas_teste.to_csv(TABLES_DIR / "validacao_faixas_risco_teste.csv", index=False, encoding="utf-8")

    # Salva tabela comparativa dos modelos
    linhas_comp = []
    for nome, res in resultados.items():
        m50 = res["limiar_050"]
        m40 = res["limiar_rastreio"]
        linhas_comp.append({
            "Modelo": nome,
            "CV_ROC_AUC": f"{res['cv_roc_auc_mean']:.4f} ± {res['cv_roc_auc_std']:.4f}",
            "Test_ROC_AUC": res["test_roc_auc"],
            "Test_PR_AUC": res["test_pr_auc"],
            "Brier_Score": res["test_brier_score"],
            "Recall_Limiar_050": m50["recall_sensibilidade"],
            "Especificidade_Limiar_050": m50["especificidade"],
            "F1_Limiar_050": m50["f1_score"],
            "Recall_Rastreio_040": m40["recall_sensibilidade"],
            "Especificidade_Rastreio_040": m40["especificidade"],
            "VPP_Rastreio_040": m40["precision_vpp"],
            "VPN_Rastreio_040": m40["vpn"],
            "F1_Rastreio_040": m40["f1_score"],
            "VP_040": m40["tp"],
            "FP_040": m40["fp"],
            "VN_040": m40["tn"],
            "FN_040": m40["fn"],
        })
    df_comp = pd.DataFrame(linhas_comp)
    df_comp.to_csv(TABLES_DIR / "comparativo_modelos.csv", index=False, encoding="utf-8")

    # Gera figuras executivas
    gerar_graficos_executivos(
        df, resultados, y_test, df_importancia, df_importancia, df_faixas_teste, df_terr
    )

    # Remove vetores brutos antes de serializar JSON
    res_limpo = {
        k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")}
        for k, v in resultados.items()
    }
    resumo_json = {
        "amostra": {
            "n_total": int(len(df)),
            "n_treino": int(len(X_train)),
            "n_teste": int(len(X_test)),
            "casos_treino": int(y_train.sum()),
            "casos_teste": int(y_test.sum()),
            "random_state": RANDOM_STATE,
        },
        "parametros_indice_dieta_treino": params_dieta_treino,
        "limiares_tercis_probabilidade_rf": {
            "tercil_inferior_baixo_moderado": round(q33, 4),
            "tercil_superior_moderado_alto": round(q67, 4),
            "limiar_triagem_sensibilidade": 0.40,
        },
        "modelos": res_limpo,
        "validacao_faixas_risco_teste": linhas_faixa,
        "top_10_features_rf": df_importancia.head(10).to_dict(orient="records"),
    }

    (PROCESSED_DIR / "model_metrics.json").write_text(
        json.dumps(resumo_json, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (MODELS_DIR / "risk_thresholds.json").write_text(
        json.dumps(resumo_json["limiares_tercis_probabilidade_rf"], indent=2), encoding="utf-8"
    )
    return resumo_json


if __name__ == "__main__":
    executar_treinamento()
