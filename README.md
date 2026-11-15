# Radar Preditivo de Vulnerabilidade ao Diabetes — Bloco 3
**UNEX — Centro Universitário de Excelência | Bacharelado em Sistemas de Informação (5º Período)**  
**Disciplina:** Mineração de Dados — **Orientador:** Prof. Wallas Froes de Oliveira  

**Integrantes:**
- Augusto Santos de Oliveira
- Daniel Teixeira Santos
- Douglas Pereira Santos
- Graciano Marôto da Cunha Neto
- Marcos Nathan Moreno Silva
- Mendell Kalyl Junio Figueiredo de Souza Melo

---

## 1. Visão Geral do Projeto
Este repositório implementa integralmente o **Bloco 3 (Execução da Mineração, Resultados, Validação e Pitch Comercial)** do projeto semestral de Mineração de Dados, materializando o planejamento arquitetural definido nos Blocos 1 e 2:

1. **Camada Individual Clínica-Comportamental (CDC/NCHS NHANES 2017–2018):** Extração automatizada dos 16 módulos `.XPT` originais ($N = 9.254$ registros brutos), junção `1:1` auditada pela chave `SEQN`, decodificação específica de códigos sentinelas por codebook e filtragem do universo adulto não gestante com antropometria válida ($n = 5.131$, sendo $1.008$ casos de diabetes — $19,65\%$).
2. **Escudo Contra Vazamento de Dados (*Data Leakage Shield*):** Bloqueio estrito de `LBXGH` (HbA1c), `LBXGLU` (glicemia de jejum), `DIQ010` (diagnóstico médico prévio), `DIQ050` (insulina) e `DIQ070` (hipoglicemiantes orais) no vetor preditor $X$ (composto por 19 variáveis distribuídas nos eixos de Hábitos Alimentares, Atividade Física/Sedentarismo, Contexto Socioeconômico e Cofatores Clínicos de Rotina).
3. **Camada Territorial Brasileira (IBGE API SIDRA + DATASUS SIH/CNES):** Consolidação das 27 Unidades da Federação (`territorial_uf.parquet`) com o `indice_contexto_territorial` para orientar a alocação geográfica de recursos preventivos sem cruzamento indevido de chaves individuais.
4. **Modelagem Supervisionada com Prioridade em Sensibilidade (Recall):** Treinamento e avaliação cruzada (5-fold) de **Regressão Logística** ($\text{ROC-AUC} = 0,8376$, $\text{Recall}_{0,40} = 85,6\%$), **Árvore de Decisão** ($\text{ROC-AUC} = 0,7956$, $\text{Recall}_{0,40} = 83,7\%$) e **Random Forest** ($\text{ROC-AUC} = 0,8301$, $\text{Recall}_{0,40} = 86,1\%$, $\text{VPN} = 94,9\%$).

---

## 2. Estrutura de Diretórios
```text
Bloco 3 - Wallas/
├── app/
│   ├── app_radar_diabetes.py       # Aplicação web B2B interativa (Streamlit)
│   └── radar_diabetes_demo.html    # Dashboard executivo HTML/JS autocontido (abertura instantânea)
├── data/
│   ├── raw/                        # Microdados XPT originais do NHANES, IBGE, DATASUS e manifest_extracao.json (SHA-256)
│   ├── interim/                    # Base integrada por SEQN pós-limpeza clínica (nhanes_limpo.parquet)
│   └── processed/                  # analytic.parquet, territorial_uf.parquet, radar_diabetes.db, data_dictionary.csv, leakage_blocklist.txt
├── docs/                           # Documentação Técnica (Parte 2), Relatório de Resultados e Apresentação Pitch (Parte 1) em DOCX, PDF e PPTX
├── models/                         # Modelos serializados (.joblib) e limiares de tercis calibrados no treino
├── reports/
│   ├── figures/                    # Gráficos de alta definição (300 DPI) gerados pela execução
│   └── tables/                     # Tabelas analíticas de métricas e consultas SQL
├── src/
│   ├── extract_nhanes.py           # Extração NHANES 2017-2018 com contrato SHA-256
│   ├── extract_ibge.py             # Extração API IBGE Localidades + SIDRA (Censo/PNS)
│   ├── extract_datasus.py          # Consolidação DATASUS (SIH/CNES) e Índice Territorial
│   ├── clean.py                    # Integração SEQN, sentinelas, limites clínicos e definição de y
│   ├── features.py                 # Engenharia dos 3 eixos, StratifiedMedianImputer e Data Leakage Shield
│   ├── train_models.py             # Treinamento 80/20 estratificado, calibração de Recall e figuras
│   ├── sql_analytics.py            # Consultas analíticas SQL sobre SQLite (radar_diabetes.db)
│   └── run_pipeline.py             # Orquestrador ponta a ponta
├── tests/
│   └── test_pipeline.py            # Suíte com 12 testes automatizados de homologação (pytest)
├── INICIAR_APP_RADAR.bat           # Atalho Windows para iniciar a aplicação Streamlit
└── requirements.txt                # Dependências do ambiente Python
```

---

## 3. Execução Rápida (Guia de Reprodução)

```powershell
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Executar o pipeline completo de mineração (extração, limpeza, features, modelos e SQL)
python -m src.run_pipeline

# 3. Executar a suíte de testes automatizados de homologação (12 cenários)
python -m pytest -v

# 4. Iniciar a aplicação interativa de demonstração (Pitch Comercial)
python -m streamlit run app/app_radar_diabetes.py
```
