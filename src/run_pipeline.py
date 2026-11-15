"""
Script Orquestrador Completo da Mineração de Dados — Bloco 3.
Executa em sequência auditável:
1. Extração de microdados NHANES 2017-2018 (CDC) e indicadores territoriais (IBGE SIDRA + DATASUS)
2. Integração relacional por SEQN, limpeza clínica e isolamento do alvo (Data Leakage Shield)
3. Engenharia de features nos 3 eixos (Alimentação, Movimento, Território/Social) + Cofatores
4. Treinamento, validação cruzada e avaliação de Regressão Logística, Árvore de Decisão e Random Forest
5. Consolidação relacional em SQLite e geração de relatórios analíticos e gráficos executivos
"""

from __future__ import annotations

import time
from src.extract_nhanes import extrair_nhanes
from src.extract_datasus import extrair_datasus_e_consolidar_territorio
from src.clean import executar_limpeza
from src.features import construir_features
from src.train_models import executar_treinamento
from src.sql_analytics import executar_camada_sql


def main() -> None:
    inicio = time.time()
    print("=" * 80)
    print("INICIANDO PIPELINE DE MINERAÇÃO DE DADOS — BLOCO 3 (UNEX - SISTEMAS DE INFORMAÇÃO)")
    print("=" * 80)

    print("\n[ETAPA 1/5] Extração e Verificação de Contratos (NHANES 2017-2018 + IBGE + DATASUS)...")
    frames_nhanes, _ = extrair_nhanes(forcar_download=False)
    extrair_datasus_e_consolidar_territorio()

    print("\n[ETAPA 2/5] Limpeza Clínica, Decodificação de Sentinelas e Isolamento do Alvo...")
    df_limpo, _ = executar_limpeza(frames_nhanes)

    print("\n[ETAPA 3/5] Engenharia de Features e Auditoria Anti-Vazamento (Data Leakage Shield)...")
    construir_features(df_limpo)

    print("\n[ETAPA 4/5] Treinamento de Classificadores, Calibração de Faixas e Geração de Figuras...")
    executar_treinamento()

    print("\n[ETAPA 5/5] Execução de Consultas Analíticas em SQL (SQLite)...")
    executar_camada_sql()

    duracao = time.time() - inicio
    print("\n" + "=" * 80)
    print(f"PIPELINE CONCLUÍDO COM SUCESSO EM {duracao:.2f} SEGUNDOS.")
    print("=" * 80)


if __name__ == "__main__":
    main()
