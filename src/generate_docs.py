"""
Gerador da Documentação Técnica e Relatório de Resultados do Bloco 3 (DOCX e PDF)
no padrão exato do documento do Bloco 2 da UNEX (Times New Roman, capa institucional,
sumário paginado, quadros numerados, blocos de código auditáveis, figuras em 300 DPI
e referências normatizadas ABNT NBR 6023).
"""

from __future__ import annotations

from pathlib import Path
import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image as RLImage,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"
FIGURES_DIR = ROOT_DIR / "reports" / "figures"

INTEGRANTES = [
    "Augusto Santos de Oliveira",
    "Daniel Teixeira Santos",
    "Douglas Pereira Santos",
    "Graciano Marôto da Cunha Neto",
    "Marcos Nathan Moreno Silva",
    "Mendell Kalyl Junio Figueiredo de Souza Melo",
]


# ==============================================================================
# ESTRUTURA DE CONTEÚDO INTEGRAL DA DOCUMENTAÇÃO TÉCNICA E RESULTADOS (BLOCO 3)
# ==============================================================================
SECOES_DOCUMENTO = [
    {
        "num": "1",
        "titulo": "ARQUITETURA DE IMPLEMENTAÇÃO E EXECUÇÃO DO PIPELINE",
        "subsecoes": [
            {
                "num": "1.1",
                "titulo": "Resgate do problema de negócio e herança metodológica dos Blocos 1 e 2",
                "blocos": [
                    ("p", "O presente documento consolida a execução prática do Bloco 3 do projeto semestral de Mineração de Dados, dando materialidade ao diagnóstico comercial validado no Bloco 1 e à arquitetura de extração, limpeza e engenharia de atributos especificada no Bloco 2. O problema de negócio investigado permanece ancorado na transição do paradigma reativo para a abordagem preditiva no manejo do diabetes mellitus: transformar bases públicas heterogêneas, historicamente isoladas em silos, em um radar de vulnerabilidade capaz de orientar a alocação preventiva de recursos em operadoras de saúde, clínicas de atenção primária e programas corporativos (BRASIL, 2013; ORGANIZAÇÃO MUNDIAL DA SAÚDE, 2016)."),
                    ("p", "Conforme estabelecido na seção 1.3 do documento anterior, o Bloco 2 encerrou seu escopo no planejamento rigoroso do dado modelável, sem executar treinamento ou reportar métricas. Neste Bloco 3, o pipeline completo foi implementado em linguagem Python 3 e SQL (SQLite), processando os microdados reais do ciclo 2017–2018 do National Health and Nutrition Examination Survey (NHANES/CDC) na camada individual e os indicadores oficiais do Instituto Brasileiro de Geografia e Estatística (API SIDRA/IBGE e Pesquisa Nacional de Saúde) combinados ao DATASUS (SIH/SUS e CNES) na camada territorial brasileira (CENTERS FOR DISEASE CONTROL AND PREVENTION, 2018; INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA, 2020)."),
                    ("p", "Toda a implementação obedece ao princípio metodológico do Data Leakage Shield (escudo contra vazamento de dados), formalizado por Kaufman et al. (2011): variáveis que definem diretamente o diagnóstico laboratorial ou medicamentoso do desfecho — glicohemoglobina (LBXGH/HbA1c), glicemia plasmática de jejum (LBXGLU), autorrelato médico prévio (DIQ010), uso de insulina (DIQ050) e uso de hipoglicemiantes orais (DIQ070) — foram isoladas exclusivamente para a construção do vetor alvo binário (y) e bloqueadas por asserção automatizada na matriz de atributos preditores (X). O modelo aprende a estimar vulnerabilidade a partir de hábitos alimentares, volume de atividade física, comportamento sedentário, condições socioeconômicas e medidas clínicas de triagem básica."),
                ],
            },
            {
                "num": "1.2",
                "titulo": "Estrutura modular do código e organização de diretórios",
                "blocos": [
                    ("p", "Para garantir manutenção, auditabilidade e separação de responsabilidades segundo o modelo CRISP-DM (CHAPMAN et al., 2000), o software foi estruturado em pacotes modulares desacoplados. A árvore de diretórios abaixo reflete o estado real implementado na máquina de homologação:"),
                    ("code", """Bloco 3 - Wallas/
|-- app/
|   |-- app_radar_diabetes.py       # App web executivo em Streamlit (4 abas)
|   +-- radar_diabetes_demo.html    # Dashboard HTML/JS autocontido
|-- data/
|   |-- raw/                        # XPT/CSV intocados + manifest_extracao.json
|   |-- interim/                    # Base integrada SEQN (nhanes_limpo.parquet)
|   +-- processed/                  # analytic.parquet, territorial_uf, SQLite
|-- docs/                           # Documentacao Tecnica e Slides (DOCX/PDF/PPTX)
|-- models/                         # Pipelines (.joblib) e limiares (.json)
|-- reports/
|   |-- figures/                    # 6 figuras analiticas em 300 DPI
|   +-- tables/                     # Tabelas de metricas, tercis e queries SQL
|-- src/
|   |-- extract_nhanes.py           # Extracao CDC NHANES + hash SHA-256
|   |-- extract_ibge.py             # Consumo REST API IBGE Localidades/SIDRA
|   |-- extract_datasus.py          # Consolidacao SIH/CNES e Indice Territorial
|   |-- clean.py                    # Join 1:1 SEQN, sentinelas e limites clinicos
|   |-- features.py                 # 19 features X, Imputer e Leakage Blocklist
|   |-- train_models.py             # Treino 80/20 estratificado, CV 5-fold e ROC
|   |-- sql_analytics.py            # Carga e execucao de consultas SQL (SQLite)
|   +-- run_pipeline.py             # Orquestrador ponta a ponta da mineracao
|-- tests/
|   +-- test_pipeline.py            # Suite com 12 testes automatizados (pytest)
|-- INICIAR_APP_RADAR.bat           # Inicializador rapido para demonstracao
+-- requirements.txt                # Especificacao das dependencias Python"""),
                    ("p", "O Quadro 1 sintetiza a responsabilidade técnica de cada módulo de código-fonte implementado no pacote src/ e os artefatos persistidos em disco."),
                    ("table", "Quadro 1 – Mapeamento arquitetural dos módulos implementados no Bloco 3", [
                        ["Módulo Python", "Entrada Principal", "Processamento Executado", "Artefato de Saída"],
                        ["src/extract_nhanes.py", "Repositório HTTP CDC (16 arquivos .XPT)", "Download resiliente, leitura SAS XPORT e cálculo de hash SHA-256", "data/raw/nhanes/*.parquet e manifest_extracao.json"],
                        ["src/extract_ibge.py", "API REST IBGE v1 e SIDRA (Agregado 4714 / PNS)", "Extração das 27 UFs, população, renda, escolaridade e indicadores PNS", "data/raw/ibge/ibge_uf_indicadores.parquet"],
                        ["src/extract_datasus.py", "Indicadores SIH/SUS (CID E10-E14) e CNES AB", "Cálculo de internações/100k hab. e z-score composto de vulnerabilidade", "data/processed/territorial_uf.parquet"],
                        ["src/clean.py", "16 DataFrames brutos do NHANES 2017–2018", "Merge 1:1 por SEQN, filtro adulto não gestante, sentinelas -> NaN, alvo y", "data/interim/nhanes_limpo.parquet e JSON de qualidade"],
                        ["src/features.py", "nhanes_limpo.parquet (n = 5.131 adultos)", "Construção das 19 features de X nos 3 eixos e validação anti-vazamento", "analytic.parquet, data_dictionary.csv, feature_audit.csv"],
                        ["src/train_models.py", "analytic.parquet (partição 80/20 estratificada)", "Treino de LR, DT e RF com imputação estratificada sem vazamento e gráficos", "models/*.joblib, model_metrics.json, reports/figures/*.png"],
                        ["src/sql_analytics.py", "analytic.parquet e territorial_uf.parquet", "Carga relacional em SQLite e execução de 4 consultas analíticas SQL", "radar_diabetes.db e reports/tables/sql*.csv"],
                    ]),
                ],
            },
            {
                "num": "1.3",
                "titulo": "Contratos de extração e rastreabilidade criptográfica (SHA-256)",
                "blocos": [
                    ("p", "Em cumprimento estrito à seção 2.7 do Bloco 2, nenhum arquivo bruto foi editado manualmente. O módulo src/extract_nhanes.py realiza a requisição direta aos servidores do National Center for Health Statistics (NCHS/CDC), valida a assinatura binária SAS XPORT (HEADER RECORD) e registra automaticamente o contrato de extração contendo URL, carimbo de tempo UTC, tamanho em bytes, hash criptográfico SHA-256, contagem de linhas e contagem de chaves SEQN únicas. O Quadro 2 apresenta o manifesto real gerado pela execução na máquina."),
                    ("table", "Quadro 2 – Manifesto de extração real e hashes SHA-256 dos 16 arquivos NHANES 2017–2018", [
                        ["Componente", "Arquivo Original", "Linhas", "SEQN Únicos", "Tamanho (Bytes)", "Hash SHA-256 (Primeiros 24 caracteres)"],
                        ["Demographics", "DEMO_J.XPT", "9.254", "9.254", "3.489.200", "c0b46e0345ea882765117f31..."],
                        ["Body Measures", "BMX_J.XPT", "8.704", "8.704", "1.464.000", "8d675e42d882f262a2886f83..."],
                        ["Blood Pressure", "BPX_J.XPT", "8.704", "8.704", "1.464.000", "f98f1d9a4c18c264982f684e..."],
                        ["Total Cholesterol", "TCHOL_J.XPT", "7.435", "7.435", "180.480", "0291a6a4f6d84567b7f5348b..."],
                        ["HDL Cholesterol", "HDL_J.XPT", "7.435", "7.435", "180.480", "9f4eb41b89f0c947d1d6390b..."],
                        ["Triglycerides/LDL", "TRIGLY_J.XPT", "3.036", "3.036", "244.480", "3995696f9686f5b93b899f58..."],
                        ["Glycohemoglobin", "GHB_J.XPT", "6.401", "6.401", "104.240", "35f07094573a8670a5c8fb5b..."],
                        ["Fasting Glucose", "GLU_J.XPT", "3.036", "3.036", "98.800", "5b38897d0d7b8c6b9b498448..."],
                        ["Diabetes Quest.", "DIQ_J.XPT", "8.897", "8.897", "3.844.560", "1ecbf5360dfcc7b64a0202e6..."],
                        ["Dietary Totals D1", "DR1TOT_J.XPT", "8.704", "8.704", "11.701.200", "390ae5205acfc6638b6101c1..."],
                        ["Diet Behavior", "DBQ_J.XPT", "9.254", "9.254", "3.415.120", "1c365d7f469682034f570d75..."],
                        ["Physical Activity", "PAQ_J.XPT", "5.856", "5.856", "800.400", "048120aa3a5c013712e7c9f4..."],
                        ["Smoking", "SMQ_J.XPT", "6.724", "6.724", "2.005.120", "73c3708e540c0357c91b1846..."],
                        ["Alcohol Use", "ALQ_J.XPT", "5.533", "5.533", "444.560", "53006d40776479890b7b7d72..."],
                        ["Medical Cond.", "MCQ_J.XPT", "8.897", "8.897", "5.341.040", "79c50c805a37365d7a3a645a..."],
                        ["Food Security", "FSQ_J.XPT", "9.254", "9.254", "3.637.360", "b601f31463be0098a30e27e4..."],
                    ]),
                ],
            },
            {
                "num": "1.4",
                "titulo": "Implementação da limpeza clínica, tratamento de sentinelas e engenharia sem vazamento",
                "blocos": [
                    ("p", "Durante a implementação dos módulos src/clean.py e src/features.py, o planejamento conceitual do Bloco 2 exigiu decisões técnicas de engenharia para lidar com nuances reais dos microdados do CDC. Destacam-se quatro mecanismos críticos implementados no código:"),
                    ("p", "a) Seleção explícita de colunas antes da junção por SEQN: arquivos laboratoriais de subamostra, como GLU_J e TRIGLY_J, compartilham a coluna administrativa de peso amostral WTSAF2YR. Um merge ingênuo de todas as colunas geraria sufixos duplicados (_x e _y), violando a regra da seção 3.4d do Bloco 2. A solução implementada seleciona explicitamente o dicionário COLUNAS_SELECIONADAS de cada módulo antes do join one_to_one."),
                    ("p", "b) Decodificação cirúrgica de sentinelas por domínio de variável: no NHANES, os códigos 7 e 9 representam 'Recusou' e 'Não sabe' em perguntas categóricas fechadas (como DIQ010, DMDEDUC2 e MCQ300C). Contudo, nas variáveis de frequência semanal de atividade física (PAQ610, PAQ625, PAQ640, PAQ655 e PAQ670), o valor 7 significa literalmente '7 dias por semana', enquanto os sentinelas de recusa/não sabe são 77 e 99. De modo análogo, no módulo alimentar DBQ (DBD895 e DBD900), o código 5555 indica 'mais de 21 refeições fora de casa por semana', e no módulo de pressão arterial (BPXDI1–BPXDI3) leituras diastólicas iguais a zero representam ausência de ausculta do quinto som de Korotkoff. O código implementado separa os conjuntos de bloqueio por família de variáveis, preservando os praticantes diários de exercício e convertendo leituras fisiologicamente impossíveis em NaN."),
                    ("p", "c) Transformador StratifiedMedianImputer acoplado ao Pipeline do scikit-learn: conforme exigido na seção 3.7 (Quadro 6) do Bloco 2, valores ausentes moderados não poderiam receber imputação global antes da divisão treino/teste. Foi implementada uma classe herdando de BaseEstimator e TransformerMixin que, durante o método fit(X_train), calcula a mediana de cada atributo dentro de 8 estratos cruzados de sexo e faixa etária (18–29, 30–44, 45–59 e 60+ anos) exclusivamente sobre os 4.104 registros de treino, aplicando tais parâmetros congelados aos 1.027 registros de teste durante o método transform(X_test)."),
                    ("code", """class StratifiedMedianImputer(BaseEstimator, TransformerMixin):
    def __init__(self, feature_names: list[str]):
        self.feature_names = feature_names

    def _criar_estrato(self, df: pd.DataFrame) -> pd.Series:
        faixa = pd.cut(df["idade_anos"], bins=[0, 29, 44, 59, 150],
                       labels=["18-29", "30-44", "45-59", "60+"]).astype(str)
        sexo_str = df["sexo"].fillna(1).astype(int).astype(str)
        return sexo_str + "_" + faixa

    def fit(self, X: pd.DataFrame | np.ndarray, y=None):
        df = pd.DataFrame(X, columns=self.feature_names).copy()
        estrato = self._criar_estrato(df)
        self.medianas_estrato_, self.medianas_globais_ = {}, {}
        for col in self.feature_names:
            self.medianas_globais_[col] = float(df[col].median())
            med_grupo = df.groupby(estrato)[col].median().to_dict()
            self.medianas_estrato_[col] = {
                k: float(v) if pd.notna(v) else self.medianas_globais_[col]
                for k, v in med_grupo.items()
            }
        return self"""),
                    ("p", "d) Padronização estrita do indice_qualidade_dieta no conjunto de treino: a variável composta definida no Quadro 8 do Bloco 2 — média de z-scores (+z_fibra - z_açúcar - z_sódio - z_gordura_saturada) — foi recalculada utilizando exclusivamente as médias e desvios-padrão apurados na partição de treinamento (fibra: média 16,76 g, DP 11,06 g; açúcar: média 102,56 g, DP 66,08 g; sódio: média 3.448,01 mg, DP 1.881,63 mg; gordura saturada: média 27,29 g, DP 17,80 g)."),
                ],
            },
        ],
    },
    {
        "num": "2",
        "titulo": "GUIA DE REPRODUÇÃO E CONFIGURAÇÃO DO AMBIENTE",
        "subsecoes": [
            {
                "num": "2.1",
                "titulo": "Requisitos de hardware, sistema operacional e stack tecnológica",
                "blocos": [
                    ("p", "A solução foi projetada para ser integralmente reproduzível em qualquer estação de trabalho Windows, Linux ou macOS sem dependência de infraestrutura proprietária em nuvem ou chaves de API pagas. O ambiente de homologação utilizou sistema operacional Windows 11 (64 bits) e interpretador Python 3.14 (compatível com Python 3.10 ou superior). As bibliotecas utilizadas restringem-se ao ecossistema científico aberto da disciplina: pandas e numpy para manipulação vetorial, pyarrow para persistência colunar em Parquet, scikit-learn para modelagem supervisionada, matplotlib e seaborn para geração gráfica, sqlite3 para a camada analítica SQL, pytest para homologação automatizada e streamlit para a interface executiva."),
                ],
            },
            {
                "num": "2.2",
                "titulo": "Passo a passo para reprodução integral do zero",
                "blocos": [
                    ("p", "Qualquer desenvolvedor, auditor ou gestor técnico pode reproduzir a extração, o processamento, o treinamento dos modelos, a validação por testes e a aplicação interativa executando os quatro passos sequenciais abaixo no terminal PowerShell ou Bash a partir da pasta raiz do projeto:"),
                    ("code", """# Passo 1: Acessar o diretorio do projeto e instalar as dependencias
cd "C:\\Users\\mende\\OneDrive\\Documentos\\Estudos\\Bloco 3 - Wallas"
pip install -r requirements.txt

# Passo 2: Executar o pipeline completo de mineracao (Etapas 1 a 5)
python -m src.run_pipeline

# Passo 3: Executar a suite de 12 testes automatizados de homologacao
python -m pytest -v

# Passo 4: Iniciar a aplicacao web interativa para demonstracao (Pitch)
python -m streamlit run app/app_radar_diabetes.py"""),
                    ("p", "O tempo médio de execução completa do comando python -m src.run_pipeline é de aproximadamente 13 segundos quando os arquivos brutos já se encontram em cache local (data/raw/nhanes/) e de cerca de 25 a 40 segundos em caso de download inédito diretamente dos servidores do CDC e da API do IBGE."),
                ],
            },
            {
                "num": "2.3",
                "titulo": "Verificação dos artefatos gerados após a execução",
                "blocos": [
                    ("p", "Ao término do script orquestrador (src/run_pipeline.py), o sistema registra no console o log de progresso das cinco etapas e persiste os seguintes arquivos verificáveis em disco: a) data/processed/analytic.parquet (5.131 linhas e 93 colunas, incluindo probabilidades preditas e faixa de risco); b) data/processed/territorial_uf.parquet (27 UFs brasileiras ranqueadas); c) data/processed/radar_diabetes.db (banco relacional SQLite contendo as tabelas fato_nhanes_analitico, territorial_uf, dim_ibge_uf e fato_datasus); d) data/processed/model_metrics.json e feature_audit.csv; e) models/logistic_regression.joblib, decision_tree.joblib e random_forest.joblib; e f) seis figuras em 300 DPI na pasta reports/figures/."),
                ],
            },
        ],
    },
    {
        "num": "3",
        "titulo": "METODOLOGIA E RESULTADOS DOS TESTES DE HOMOLOGAÇÃO",
        "subsecoes": [
            {
                "num": "3.1",
                "titulo": "Arquitetura de validação e cenários de teste automatizados",
                "blocos": [
                    ("p", "Em projetos de ciência de dados aplicados à saúde, um código que executa sem levantar exceções sintáticas do interpretador Python ainda pode conter falhas silenciosas graves, como duplicação de pacientes em junções relacionais, contaminação do conjunto de teste pela mediana global ou perda acidental de categorias válidas durante a limpeza de códigos sentinelas. Por essa razão, a homologação do Bloco 3 foi estruturada como uma suíte formal de testes automatizados (tests/test_pipeline.py) executada pelo framework pytest."),
                    ("p", "Foram implementados 12 casos de teste (CT-01 a CT-12) cobrindo todo o ciclo de vida do dado, desde a integridade criptográfica do download bruto até a monotonia clínica das faixas de risco entregues na interface do usuário. O Quadro 3 detalha cada cenário validado e o resultado obtido."),
                    ("table", "Quadro 3 – Especificação e resultados dos 12 cenários de teste executados via pytest", [
                        ["ID", "Cenário de Teste (Função)", "Critério de Aceite / Asserção Técnica", "Status Real"],
                        ["CT-01", "test_01_contratos_extracao_sha256", "Existência dos 16 módulos NHANES no manifesto com hash SHA-256 de 64 caracteres e n_linhas > 0", "APROVADO (PASSED)"],
                        ["CT-02", "test_02_integridade_relacional_seqn", "Chave id_participante 100% única (n = 5.131) e zero colunas duplicadas (_x / _y) após os 15 left joins", "APROVADO (PASSED)"],
                        ["CT-03", "test_03_universo_adulto_gestantes", "100% dos registros com idade_anos >= 18 e 0 registros com RIDEXPRG == 1 (gestantes excluídas)", "APROVADO (PASSED)"],
                        ["CT-04", "test_04_decodificacao_sentinelas", "Remoção total de códigos 7/9/77/99 em categóricas e preservação do valor 7 dias/semana no PAQ610", "APROVADO (PASSED)"],
                        ["CT-05", "test_05_limites_clinicos_logicos", "Altura [120, 210] cm, peso [30, 250] kg, cintura [50, 180] cm, PAS > PAD e energia [500, 6000] kcal", "APROVADO (PASSED)"],
                        ["CT-06", "test_06_escudo_contra_vazamento", "Interseção vazia entre X (19 features) e blocklist (HbA1c, glicemia, insulina, DIQ010) e |r| < 0,50", "APROVADO (PASSED)"],
                        ["CT-07", "test_07_imputador_sem_vazamento", "Injeção de outlier extremo (9999) no teste não altera a mediana estratificada aprendida no treino", "APROVADO (PASSED)"],
                        ["CT-08", "test_08_engenharia_features_eixos", "Exatidão algébrica de razao_cintura_estatura e do indicador binário cumpre_oms_150 (>= 600 MET-min)", "APROVADO (PASSED)"],
                        ["CT-09", "test_09_isolamento_territorial_uf", "Presença exata das 27 UFs em territorial_uf.parquet sem cruzamento de chave SEQN individual", "APROVADO (PASSED)"],
                        ["CT-10", "test_10_desempenho_e_recall", "Carregamento dos 3 arquivos .joblib com ROC-AUC >= 0,78, Recall >= 80% e VPN >= 92% no teste", "APROVADO (PASSED)"],
                        ["CT-11", "test_11_monotonia_faixas_tercis", "Prevalência real estritamente crescente: Baixo (2,62%) < Moderado (12,98%) < Alto Risco (43,19%)", "APROVADO (PASSED)"],
                        ["CT-12", "test_12_camada_sql_sqlite", "Banco radar_diabetes.db íntegro com 5.131 linhas na fato individual e 27 UFs na dimensão territorial", "APROVADO (PASSED)"],
                    ]),
                ],
            },
            {
                "num": "3.2",
                "titulo": "Registro real de execução e evidências de mitigação de falhas",
                "blocos": [
                    ("p", "A execução da suíte de homologação na máquina local confirmou 100% de aprovação nos 12 testes em 2,69 segundos, conforme saída literal do terminal reproduzida abaixo:"),
                    ("code", """platform win32 -- Python 3.14.6, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\\Users\\mende\\OneDrive\\Documentos\\Estudos\\Bloco 3 - Wallas
collected 12 items

tests/test_pipeline.py::test_01_contratos_extracao_sha256 PASSED                  [  8%]
tests/test_pipeline.py::test_02_integridade_relacional_seqn_one_to_one PASSED     [ 16%]
tests/test_pipeline.py::test_03_universo_adulto_e_exclusao_gestantes PASSED       [ 25%]
tests/test_pipeline.py::test_04_decodificacao_sentinelas_nhanes PASSED            [ 33%]
tests/test_pipeline.py::test_05_limites_clinicos_e_inconsistencias_logicas PASSED [ 41%]
tests/test_pipeline.py::test_06_escudo_contra_vazamento_data_leakage_shield PASSED[ 50%]
tests/test_pipeline.py::test_07_imputador_estratificado_sem_vazamento PASSED      [ 58%]
tests/test_pipeline.py::test_08_engenharia_features_tres_eixos PASSED             [ 66%]
tests/test_pipeline.py::test_09_isolamento_camada_territorial_uf PASSED           [ 75%]
tests/test_pipeline.py::test_10_desempenho_modelos_e_prioridade_recall PASSED     [ 83%]
tests/test_pipeline.py::test_11_monotonia_faixas_risco_tercis PASSED              [ 91%]
tests/test_pipeline.py::test_12_camada_sql_sqlite_integridade PASSED              [100%]

=========================== 12 passed in 2.69s ==========================="""),
                    ("p", "O processo de testes também cumpriu papel ativo na identificação e mitigação de quatro falhas reais durante o ciclo de desenvolvimento:"),
                    ("p", "1. Mitigação de escopo de serialização (Pickle/Joblib Namespace): na primeira rodada de execução do teste CT-10, o carregamento dos arquivos .joblib pelo pytest falhou com AttributeError: module '__main__' has no attribute 'StratifiedMedianImputer'. A causa raiz foi que, ao executar train_models.py diretamente como script principal (__main__), o serializador gravava a referência da classe customizada sob o namespace __main__, tornando-a inacessível quando importada por outros módulos (como a suíte de testes e o aplicativo Streamlit). A falha foi mitigada movendo a definição da classe StratifiedMedianImputer para o módulo base src/features.py e importando-a explicitamente em src/train_models.py."),
                    ("p", "2. Mitigação de perda de dados válidos no PAQ (código 7): a aplicação direta do conjunto SENTINELAS = {7, 9, 77, 99} sobre todas as colunas do questionário de atividade física apagava os participantes que praticavam atividade física 7 dias por semana. O teste CT-04 validou a separação entre variáveis categóricas binárias (bloqueio {7, 9}) e variáveis de contagem de dias semanais (bloqueio {77, 99})."),
                    ("p", "3. Mitigação de distorção em calorias e pressão diastólica: foram detectados e convertidos para NaN exatamente 91 registros com ingestão energética implausível no recordatório de 24h (< 500 kcal ou > 6.000 kcal), 45 registros com açúcar dietético acima de 400 g/dia, 2 registros com IMC extremo (> 80 kg/m²) e 53 registros com pressão arterial inconsistente (incluindo leituras diastólicas zeradas no exame físico)."),
                ],
            },
        ],
    },
    {
        "num": "4",
        "titulo": "RELATÓRIO DE RESULTADOS, MÉTRICAS E VALIDAÇÃO DOS MODELOS",
        "subsecoes": [
            {
                "num": "4.1",
                "titulo": "Funil amostral e a descoberta crítica dos casos ocultos de diabetes",
                "blocos": [
                    ("p", "A integração relacional dos 16 arquivos do NHANES 2017–2018 partiu do universo bruto de 9.254 participantes entrevistados pelo CDC. Aplicando-se sequencialmente os critérios de elegibilidade metodológica definidos na seção 1.4 e 3.4 do Bloco 2, foram excluídos 3.398 indivíduos menores de 18 anos e 55 gestantes (variável RIDEXPRG == 1), resultando em 5.801 adultos não gestantes. Destes, 670 não possuíam medidas antropométricas completas de exame físico (peso, estatura e circunferência da cintura no Mobile Examination Center), consolidando a amostra analítica final em n = 5.131 participantes adultos."),
                    ("p", "Na amostra analítica (n = 5.131), a aplicação da regra composta do desfecho binário (seção 3.9 do Bloco 2) identificou 1.008 indivíduos com diabetes mellitus (prevalência amostral de 19,65%) e 4.123 controles sem a condição (80,35%). A decomposição da origem diagnóstica desses 1.008 casos revelou o primeiro grande insight estratégico do projeto: enquanto 764 participantes sabiam possuir a condição por diagnóstico médico prévio (DIQ010 == 1), 244 indivíduos (exatos 24,21% de todos os diabéticos da coorte) responderam não possuir diabetes no questionário, mas apresentaram glicohemoglobina HbA1c >= 6,5% ou glicemia de jejum >= 126 mg/dL no exame laboratorial."),
                    ("p", "Em termos de negócio, esse dado comprova empiricamente a dor central denunciada no Bloco 1: quase 1 em cada 4 portadores de diabetes encontra-se em estado de ponto cego clínico (subdiagnóstico), circulando na carteira de planos de saúde ou na rede básica sem qualquer manejo preventivo até a ocorrência de complicação aguda."),
                ],
            },
            {
                "num": "4.2",
                "titulo": "Auditoria estatística do vetor preditor X e análise crítica dos três eixos",
                "blocos": [
                    ("p", "O Quadro 4 apresenta o resultado completo da auditoria estatística das 19 variáveis preditoras (vetor X) sobre os 5.131 participantes, conforme exigido na seção 4.8 do Bloco 2. Conforme planejado na seção 3.7 (Quadro 6), variáveis de subamostra de jejum com taxa de ausência superior a 40% (triglicerídeos e colesterol LDL, que apresentaram 53,2% de ausência na amostra adulta) foram mantidas apenas no dicionário de dados e excluídas da modelagem."),
                    ("table", "Quadro 4 – Auditoria estatística das 19 features preditoras (X) e correlação com o desfecho (n = 5.131)", [
                        ["Feature (Vetor X)", "Eixo Temático", "Unidade", "n Válido", "% Ausente", "Mediana", "r Pearson", "Status Vazamento"],
                        ["idade_anos", "Demográfico", "anos", "5.131", "0,00%", "51,00", "+0,3243", "NÃO (Auditada)"],
                        ["razao_cintura_estatura", "Cofator Clínico", "razão", "5.131", "0,00%", "0,596", "+0,2745", "NÃO (Auditada)"],
                        ["historico_familiar_diabetes", "Cofator Clínico", "binária (0/1)", "4.819", "6,08%", "0,00", "+0,2218", "NÃO (Auditada)"],
                        ["imc", "Cofator Clínico", "kg/m²", "5.131", "0,00%", "28,40", "+0,1886", "NÃO (Auditada)"],
                        ["hdl", "Cofator Clínico", "mg/dL", "4.854", "5,40%", "50,00", "-0,1637", "NÃO (Auditada)"],
                        ["met_min_semana", "Eixo 2 (Movimento)", "MET-min/sem", "5.130", "0,02%", "1.440,0", "-0,1500", "NÃO (Auditada)"],
                        ["cumpre_oms_150", "Eixo 2 (Movimento)", "binária (0/1)", "5.130", "0,02%", "1,00", "-0,1411", "NÃO (Auditada)"],
                        ["pressao_alta", "Cofator Clínico", "binária (0/1)", "4.945", "3,63%", "0,00", "+0,1078", "NÃO (Auditada)"],
                        ["escolaridade_ord", "Eixo 3 (Social)", "ordinal (1-5)", "4.876", "4,97%", "4,00", "-0,0988", "NÃO (Auditada)"],
                        ["indice_qualidade_dieta", "Eixo 1 (Dieta)", "z-score", "4.705", "8,30%", "0,095", "+0,0833", "NÃO (Auditada)"],
                        ["densidade_fibra", "Eixo 1 (Dieta)", "g/1000 kcal", "4.661", "9,16%", "7,224", "+0,0727", "NÃO (Auditada)"],
                        ["refeicao_pronta", "Eixo 1 (Dieta)", "ref./semana", "5.123", "0,16%", "2,00", "-0,0704", "NÃO (Auditada)"],
                        ["inseguranca_alimentar", "Eixo 3 (Social)", "binária (0/1)", "4.888", "4,74%", "0,00", "+0,0517", "NÃO (Auditada)"],
                        ["densidade_acucar", "Eixo 1 (Dieta)", "g/1000 kcal", "4.631", "9,74%", "47,355", "-0,0453", "NÃO (Auditada)"],
                        ["sexo", "Demográfico", "1=M, 2=F", "5.131", "0,00%", "2,00", "-0,0396", "NÃO (Auditada)"],
                        ["excesso_sodio", "Eixo 1 (Dieta)", "binária (0/1)", "4.747", "7,48%", "1,00", "-0,0317", "NÃO (Auditada)"],
                        ["minutos_sentado", "Eixo 2 (Movimento)", "min/dia", "5.093", "0,74%", "300,0", "+0,0194", "NÃO (Auditada)"],
                        ["sedentarismo_alto", "Eixo 2 (Movimento)", "binária (0/1)", "5.093", "0,74%", "0,00", "+0,0172", "NÃO (Auditada)"],
                        ["razao_renda_pobreza", "Eixo 3 (Social)", "razão (0-5)", "4.485", "12,59%", "2,11", "-0,0078", "NÃO (Auditada)"],
                    ]),
                    ("p", "A leitura crítica do Quadro 4 evidencia três fenômenos epidemiológicos fundamentais que distinguem uma análise humana rigorosa de uma interpretação mecânica:"),
                    ("p", "1. Superioridade da Razão Cintura/Estatura (RCE) sobre o IMC isolado: a correlação da RCE com o diabetes (r = +0,2745; Spearman = +0,2768) supera substancialmente a do IMC tradicional (r = +0,1886). Isso confirma empiricamente a literatura clínica da Organização Mundial da Saúde (WORLD HEALTH ORGANIZATION, 2011) citada no Bloco 2: a adiposidade visceral centralizada no abdômen é o verdadeiro motor da resistência insulínica, enquanto o IMC falha ao não distinguir massa magra de gordura abdominal."),
                    ("p", "2. Efeito protetor robusto do movimento (Eixo 2): o cumprimento da diretriz da OMS de 150 minutos semanais de atividade moderada (>= 600 MET-min/semana) apresenta associação negativa consistente com a doença (r = -0,1411). Quando cruzado com o comportamento sedentário na consulta SQL 2 (Figura 5), observa-se que indivíduos simultaneamente inativos e muito sentados (>= 8h/dia) atingem prevalência de diabetes de 28,2%, quase o dobro daqueles fisicamente ativos e pouco sentados (15,1%)."),
                    ("p", "3. Causalidade reversa no recordatório alimentar transversal de 24 horas (Eixo 1): nota-se no Quadro 4 que densidade_acucar apresenta leve correlação negativa (-0,0453) e densidade_fibra leve correlação positiva (+0,0727) com o alvo global. Por que isso ocorre? Porque o NHANES é um estudo transversal onde 75,8% dos diabéticos (764 de 1.008) já haviam recebido diagnóstico médico prévio (DIQ010 == 1) e, portanto, já estavam sob restrição dietética de açúcar orientada por médicos ou nutricionistas no dia do recordatório! Quando isolamos os 244 casos ocultos (indivíduos com diabetes ativo no sangue que ainda não sabiam do diagnóstico), o consumo médio de açúcar e de calorias fora de casa é superior ao dos controles normoglicêmicos, e a ingestão de fibras em indivíduos com baixa renda e insegurança alimentar agrava o risco. Essa constatação valida a decisão tomada no Bloco 2 de combinar dieta, movimento, contexto social e antropometria em vez de depender exclusivamente de um único recordatório alimentar de 24 horas."),
                ],
            },
            {
                "num": "4.3",
                "titulo": "Desempenho comparativo dos classificadores e priorização da Sensibilidade (Recall)",
                "blocos": [
                    ("p", "A amostra analítica (n = 5.131) foi particionada em 80% para treinamento (n = 4.104, contendo 806 casos positivos) e 20% para teste cego (n = 1.027, contendo 202 casos positivos), mantendo a estratificação exata de 19,65% de prevalência em ambas as partições (random_state = 42). Os três algoritmos planejados no Bloco 1 (Regressão Logística, Árvore de Decisão e Random Forest) foram submetidos a validação cruzada estratificada de 5 dobras (5-fold CV) no treino e avaliados no conjunto de teste tanto no ponto de corte padrão (0,50) quanto no limiar calibrado de rastreio preventivo (0,40). O Quadro 5 resume as métricas oficiais."),
                    ("table", "Quadro 5 – Desempenho comparativo dos modelos no conjunto de teste (n = 1.027 | 202 casos reais)", [
                        ["Métrica de Avaliação", "Regressão Logística (Baseline)", "Árvore de Decisão (White-Box)", "Random Forest (Motor Ensemble)"],
                        ["ROC-AUC (Validação Cruzada 5-Fold Treino)", "0,8298 ± 0,0049", "0,7956 ± 0,0085", "0,8282 ± 0,0034"],
                        ["ROC-AUC (Conjunto de Teste Cego)", "0,8376", "0,7956", "0,8301"],
                        ["PR-AUC (Precision-Recall AUC no Teste)", "0,5904", "0,4729", "0,5503"],
                        ["Brier Score (Calibração — menor é melhor)", "0,1745", "0,1937", "0,1610 (Melhor)"],
                        ["Sensibilidade / Recall (Limiar Padrão 0,50)", "78,22% (158/202)", "77,72% (157/202)", "75,25% (152/202)"],
                        ["Especificidade (Limiar Padrão 0,50)", "72,00% (594/825)", "67,88% (560/825)", "74,18% (612/825)"],
                        ["Sensibilidade / Recall (Limiar Rastreio 0,40)", "85,64% (173/202)", "83,66% (169/202)", "86,14% (174/202)"],
                        ["Especificidade (Limiar Rastreio 0,40)", "62,79% (518/825)", "55,52% (458/825)", "63,64% (525/825)"],
                        ["Valor Preditivo Negativo — VPN (Limiar 0,40)", "94,70%", "93,28%", "94,94% (Melhor)"],
                        ["F1-Score (Limiar Rastreio 0,40)", "0,5073", "0,4580", "0,5148 (Melhor)"],
                        ["Falsos Negativos no Teste (Ponto Cego Crítico)", "29 casos perdidos", "33 casos perdidos", "28 casos perdidos (Mínimo)"],
                    ]),
                    ("p", "Os resultados do Quadro 5 e das Figuras 1 e 2 demonstram excelente capacidade discriminatória para um modelo livre de exames glicêmicos: tanto a Regressão Logística (ROC-AUC = 0,8376) quanto o Random Forest (ROC-AUC = 0,8301 e menor erro quadrático probabilístico Brier Score = 0,1610) superam a marca de 0,83 no conjunto de teste cego, sem qualquer indício de sobreajuste (overfitting) em relação à validação cruzada de treino."),
                    ("figure", "fig1_curvas_roc.png", "Figura 1 – Curvas ROC comparativas dos três classificadores no conjunto de teste (n = 1.027). Fonte: Elaboração própria ( saída de src/train_models.py )."),
                    ("p", "Mais importante do que a área global sob a curva é a decisão operacional sobre a matriz de confusão (Figura 2). Conforme defendido no Slide 9 do Bloco 1, em triagem preventiva de saúde o erro catastrófico é o Falso Negativo (classificar um portador real de diabetes como 'seguro', omitindo o rastreio laboratorial), enquanto o Falso Positivo implica apenas o custo marginal de um exame de sangue de baixo custo e educação em saúde. Ao calibrar o limiar decisório para 0,40, o Random Forest alcança Sensibilidade (Recall) de 86,14% (capturando 174 dos 202 diabéticos e reduzindo os Falsos Negativos para apenas 28 em 1.027 pacientes) e atinge um Valor Preditivo Negativo (VPN) de 94,94% — garantindo ao gestor que 95% dos indivíduos classificados abaixo do limiar de alerta realmente não possuem a doença."),
                    ("figure", "fig2_matrizes_confusao.png", "Figura 2 – Matrizes de confusão lado a lado no conjunto de teste para o limiar preventivo de 0,40. Fonte: Elaboração própria."),
                ],
            },
            {
                "num": "4.4",
                "titulo": "Explicabilidade clínica (White-Box): importância de variáveis e Odds Ratios",
                "blocos": [
                    ("p", "Para atender à exigência da equipe de produto e dos gestores médicos de 'não vender um score caixa-preta' (Quadro 1 do Bloco 2), a Figura 3 confronta a importância relativa das variáveis no Random Forest (redução média de impureza de Gini) com as Razões de Chances (Odds Ratios padronizados por 1 desvio-padrão) da Regressão Logística."),
                    ("figure", "fig3_importancia_e_odds.png", "Figura 3 – Ranking de importância relativa no Random Forest e Odds Ratios padronizados na Regressão Logística. Fonte: Elaboração própria."),
                    ("p", "A convergência entre os três modelos é notável: os cinco principais determinantes da predição são idade_anos (33,96% da importância no RF; Odds Ratio = 2,86 por desvio-padrão), razao_cintura_estatura (15,90% no RF; Odds Ratio = 1,97), historico_familiar_diabetes (9,67% no RF; Odds Ratio = 1,71), colesterol hdl (8,80% no RF; Odds Ratio protetor = 0,62) e imc (6,96% no RF), seguidos diretamente pelo volume de atividade física met_min_semana (4,88% no RF; Odds Ratio protetor = 0,82) e pelos indicadores de qualidade e composição da dieta (indice_qualidade_dieta, densidade_fibra e densidade_acucar, que somados respondem por 10,01% da capacidade explicativa da floresta)."),
                    ("p", "Adicionalmente, a inspeção das regras de decisão exportadas pela Árvore de Decisão (data/processed/regras_arvore_decisao.txt) fornece um fluxograma clínico transparente para triagem rápida em atenção básica: pacientes com idade <= 44,5 anos e razão cintura/estatura <= 0,58 apresentam risco residual mínimo; em contrapartida, indivíduos com idade > 44,5 anos, razão cintura/estatura > 0,58 e histórico familiar positivo ou HDL reduzido (< 46,5 mg/dL) migram diretamente para os nós folhas de alta vulnerabilidade."),
                ],
            },
            {
                "num": "4.5",
                "titulo": "Validação das faixas comerciais de risco e consultas analíticas SQL",
                "blocos": [
                    ("p", "Cumprindo o planejamento da seção 4.7 do Bloco 2, os limiares das três faixas metodológicas de risco foram calibrados exclusivamente pelos tercis da probabilidade estimada pelo Random Forest no conjunto de treino: Baixo Risco (probabilidade <= 0,2189), Risco Moderado (0,2189 < probabilidade <= 0,5124) e Alto Risco (probabilidade > 0,5124). Quando esses cortes congelados são aplicados aos 1.027 indivíduos do conjunto de teste cego (Quadro 6 e Figura 4), comprova-se o alto poder de concentração comercial da ferramenta."),
                    ("table", "Quadro 6 – Validação das faixas de risco no conjunto de teste cego (n = 1.027 | 202 casos reais)", [
                        ["Faixa Metodológica (Tercis Treino)", "Corte de Probabilidade", "Indivíduos no Teste", "Casos Reais de Diabetes", "Prevalência Real na Faixa", "% do Total de Diabéticos Capturados"],
                        ["1. Baixo Risco (Tercil Inferior)", "p <= 0,2189", "343 (33,4%)", "9 casos", "2,62%", "4,46%"],
                        ["2. Risco Moderado (Tercil Médio)", "0,2189 < p <= 0,5124", "339 (33,0%)", "44 casos", "12,98%", "21,78%"],
                        ["3. Alto Risco (Tercil Superior)", "p > 0,5124", "345 (33,6%)", "149 casos", "43,19%", "73,76%"],
                        ["Soma: Moderado + Alto Risco", "p > 0,2189", "684 (66,6%)", "193 casos", "28,22%", "95,54%"],
                    ]),
                    ("figure", "fig4_estratificacao_faixas_risco.png", "Figura 4 – Prevalência real e captura acumulada de casos de diabetes por faixa de risco no conjunto de teste. Fonte: Elaboração própria."),
                    ("p", "Observe a precisão dessa estratificação no Quadro 6: um indivíduo alocado pelo algoritmo na faixa de Alto Risco possui probabilidade real de 43,19% de ter diabetes, o que representa um risco relativo 16,48 vezes maior do que um indivíduo classificado na faixa de Baixo Risco (apenas 2,62% de prevalência). Abordando exclusivamente o tercil superior (33,6% da carteira), o gestor captura 73,76% de todos os diabéticos; caso estenda programas educativos também à faixa de Risco Moderado, captura 95,54% (193 de 202 casos) economizando um terço inteiro de exames laboratoriais desnecessários."),
                    ("figure", "fig5_movimento_e_faixa_etaria.png", "Figura 5 – Prevalência de diabetes segundo as 4 classes de perfil de movimento (Eixo 2) e faixa etária. Fonte: Elaboração própria."),
                    ("p", "Na camada territorial brasileira (Nível B — Figura 6), a execução da consulta SQL 3 sobre o banco radar_diabetes.db cruzou os dados da API SIDRA do IBGE (renda mediana domiciliar, população Censo 2022 e prevalência de inatividade física da PNS) com os registros do DATASUS (taxa de internações hospitalares por diabetes CID E10–E14 por 100 mil habitantes no SIH/SUS e cobertura de Atenção Básica no CNES) para as 27 Unidades da Federação. O Índice de Contexto Territorial aponta que estados das regiões Norte e Nordeste — liderados por Pará (índice +0,928; 91,38 internações/100k; cobertura AB de 70,3%), Maranhão (+0,838; 101,67 internações/100k; renda mediana de R$ 945) e Alagoas (+0,813; 46,2% de insuficiência de atividade física) — concentram a maior vulnerabilidade estrutural e demandam prioridade crítica na expansão de rastreio preventivo."),
                    ("figure", "fig6_ranking_territorial_uf.png", "Figura 6 – Ranking das Unidades da Federação pelo Índice Composto de Contexto Territorial (IBGE + DATASUS). Fonte: Elaboração própria."),
                ],
            },
        ],
    },
    {
        "num": "5",
        "titulo": "VALOR AGREGADO AO NEGÓCIO/APP E DEFESA COMERCIAL (PITCH)",
        "subsecoes": [
            {
                "num": "5.1",
                "titulo": "Agregação de valor de UX/IA para a tomada de decisão do gestor",
                "blocos": [
                    ("p", "Os resultados minerados não encerram seu ciclo em notebooks estáticos: eles foram embarcados em uma aplicação executiva funcional (app/app_radar_diabetes.py em Streamlit e app/radar_diabetes_demo.html em arquitetura web autocontida) desenhada especificamente para responder às três dores de mercado mapeadas no Bloco 1:"),
                    ("p", "1. Solução para a Dor 1 (Dados Fragmentados -> Visão Integrada em Duas Camadas): o sistema unifica na mesma interface a avaliação clínico-comportamental individual (treinada nos 5.131 adultos do NHANES) e o painel geográfico brasileiro das 27 UFs (IBGE + DATASUS). O gestor de uma operadora nacional ou do SUS visualiza tanto onde abrir frentes regionais de prevenção quanto quem priorizar na carteira local."),
                    ("p", "2. Solução para a Dor 2 (Ação Tardia -> Radar de Casos Ocultos com Recall de 86,1%): como demonstrado na seção 4.1, 24,2% dos diabéticos desconhecem sua condição. O motor preditivo opera sem exigir exame de sangue prévio, identificando o paciente vulnerável pela combinação de circunferência abdominal/estatura, idade, sedentarismo, padrão alimentar e histórico familiar antes da internação hospitalar."),
                    ("p", "3. Solução para a Dor 3 (Baixa Acionabilidade -> Simulador 'What-If' de Intervenção Comportamental): em vez de entregar apenas um número estático, a interface de UX/IA inclui um simulador dinâmico ('E se?') que recalcula instantaneamente a queda projetada na probabilidade de risco quando o paciente passa a cumprir os 150 minutos semanais recomendados pela OMS (>= 600 MET-min/semana), reduz o tempo diário sentado para menos de 6 horas, atinge a meta de 25 g/dia de fibras e reduz 5% a 7% da circunferência abdominal. Em perfis de risco moderado a alto, a simulação demonstra reduções relativas de 35% a 52% na probabilidade estimada, transformando estatística em argumento de engajamento clínico."),
                ],
            },
            {
                "num": "5.2",
                "titulo": "Retorno comercial (ROI) e grau de prontidão tecnológica (TRL)",
                "blocos": [
                    ("p", "Sob a ótica financeira (ROI), considere uma carteira corporativa ou municipal de 10.000 adultos. Em uma abordagem reativa ou de testagem cega em massa, seria necessário custear 10.000 kits diagnósticos de HbA1c e consultas de triagem para encontrar os casos positivos. Utilizando a estratificação do Radar Preditivo, o gestor convoca prioritariamente o tercil de Alto Risco (3.360 indivíduos) e captura imediatamente 73,8% de todos os portadores de diabetes da população — um ganho de eficiência operacional (Lift) de 2,20 vezes sobre o rastreio aleatório, reduzindo em 66% o desembolso imediato com exames laboratoriais na fase inicial da campanha e evitando internações cujo custo médio no SUS e na saúde suplementar supera em dezenas de vezes o valor do rastreio preventivo."),
                    ("p", "Quanto ao grau de prontidão e maturidade do produto (Technology Readiness Level), o software encontra-se em nível TRL 6/7 (protótipo de sistema funcional validado com microdados reais de 5.131 indivíduos e homologado por 12 testes automatizados). Para entrada em produção comercial com dados reais de pacientes brasileiros sob a Lei Geral de Proteção de Dados (BRASIL, 2018 — LGPD, Art. 11, tutela da saúde e consentimento específico), o único passo adicional requerido é a recalibração local dos limiares probabilísticos (Platt Scaling / Isotonic Regression) sobre uma amostra piloto da própria operadora ou secretaria municipal contratante."),
                ],
            },
        ],
    },
]

REFERENCIAS_ABNT = [
    "AMERICAN DIABETES ASSOCIATION. Standards of care in diabetes—2024. Diabetes Care, Arlington, v. 47, suppl. 1, p. S1-S321, jan. 2024.",
    "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. ABNT NBR 6023: informação e documentação — referências — elaboração. Rio de Janeiro: ABNT, 2018.",
    "BRASIL. Lei nº 13.709, de 14 de agosto de 2018. Lei Geral de Proteção de Dados Pessoais (LGPD). Brasília, DF: Presidência da República, 2018.",
    "BRASIL. Ministério da Saúde. Cadastro Nacional de Estabelecimentos de Saúde – CNES. Brasília, DF: MS, 2023. Disponível em: https://cnes.datasus.gov.br/. Acesso em: 15 nov. 2026.",
    "BRASIL. Ministério da Saúde. Departamento de Informática do SUS. DATASUS — Morbidade Hospitalar do SUS (SIH/SUS). Brasília, DF: MS, 2023. Disponível em: https://datasus.saude.gov.br/. Acesso em: 15 nov. 2026.",
    "BRASIL. Ministério da Saúde. Secretaria de Atenção à Saúde. Estratégias para o cuidado da pessoa com doença crônica: diabetes mellitus. Brasília, DF: MS, 2013. (Cadernos de Atenção Básica, n. 36).",
    "BREIMAN, L. Random forests. Machine Learning, Dordrecht, v. 45, n. 1, p. 5-32, out. 2001.",
    "CENTERS FOR DISEASE CONTROL AND PREVENTION. National Center for Health Statistics. National Health and Nutrition Examination Survey (NHANES), 2017–2018 Data Documentation, Codebook, and Frequencies. Hyattsville: NCHS, 2018. Disponível em: https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?BeginYear=2017. Acesso em: 15 nov. 2026.",
    "CHAPMAN, P. et al. CRISP-DM 1.0: step-by-step data mining guide. Chicago: SPSS Inc., 2000.",
    "FAYYAD, U.; PIATETSKY-SHAPIRO, G.; SMYTH, P. From data mining to knowledge discovery in databases. AI Magazine, Menlo Park, v. 17, n. 3, p. 37-54, 1996.",
    "HAN, J.; KAMBER, M.; PEI, J. Data mining: concepts and techniques. 3. ed. Waltham: Morgan Kaufmann, 2012.",
    "HOSMER, D. W.; LEMESHOW, S.; STURDIVANT, R. X. Applied logistic regression. 3. ed. Hoboken: John Wiley & Sons, 2013.",
    "INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA. API de Serviços de Dados e SIDRA — Censo Demográfico 2022. Rio de Janeiro: IBGE, 2023. Disponível em: https://servicodados.ibge.gov.br/api/docs/agregados. Acesso em: 15 nov. 2026.",
    "INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA. Pesquisa Nacional de Saúde 2019: percepção do estado de saúde, estilos de vida, doenças crônicas e saúde bucal. Rio de Janeiro: IBGE, 2020.",
    "KAUFMAN, S. et al. Leakage in data mining: formulation, detection, and avoidance. In: ACM SIGKDD INTERNATIONAL CONFERENCE ON KNOWLEDGE DISCOVERY AND DATA MINING, 17., 2011, San Diego. Proceedings [...]. New York: ACM, 2011. p. 556-563.",
    "ORGANIZAÇÃO MUNDIAL DA SAÚDE. Global report on diabetes. Geneva: WHO, 2016.",
    "ORGANIZAÇÃO MUNDIAL DA SAÚDE. WHO guidelines on physical activity and sedentary behaviour. Geneva: WHO, 2020.",
    "PEDREGOSA, F. et al. Scikit-learn: machine learning in Python. Journal of Machine Learning Research, Cambridge, v. 12, p. 2825-2830, 2011.",
    "WITTEN, I. H.; FRANK, E.; HALL, M. A. Data mining: practical machine learning tools and techniques. 4. ed. Amsterdam: Morgan Kaufmann, 2017.",
    "WORLD HEALTH ORGANIZATION. Waist circumference and waist–hip ratio: report of a WHO expert consultation. Geneva: WHO, 2011.",
]


def _set_cell_bg(cell, hex_color: str) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def gerar_docx_tecnico(caminho_docx: Path) -> None:
    """Gera o arquivo Word (.docx) no padrão exato ABNT/UNEX do Bloco 2."""
    doc = docx.Document()

    for section in doc.sections:
        section.top_margin = Cm(3.0)
        section.left_margin = Cm(3.0)
        section.bottom_margin = Cm(2.0)
        section.right_margin = Cm(2.0)

    style_normal = doc.styles["Normal"]
    style_normal.font.name = "Times New Roman"
    style_normal.font.size = Pt(12)
    style_normal.font.color.rgb = RGBColor(0, 0, 0)

    # --- CAPA IDÊNTICA AO BLOCO 2 ---
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = p_inst.add_run("UNEX – CENTRO UNIVERSITÁRIO DE EXCELÊNCIA\nBACHARELADO EM SISTEMAS DE INFORMAÇÃO\n")
    r1.bold = True
    r1.font.size = Pt(12)
    r2 = p_inst.add_run("Disciplina: Mineração de Dados - Orientador: Wallas Froes de Oliveira")
    r2.font.size = Pt(12)

    doc.add_paragraph()
    p_int = doc.add_paragraph()
    p_int.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_int.add_run("Integrantes:\n" + "\n".join(INTEGRANTES))

    for _ in range(4):
        doc.add_paragraph()

    p_tit = doc.add_paragraph()
    p_tit.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rt = p_tit.add_run(
        "EXECUÇÃO DA MINERAÇÃO, RESULTADOS, VALIDAÇÃO E DOCUMENTAÇÃO TÉCNICA DE IMPLEMENTAÇÃO E TESTES"
    )
    rt.bold = True
    rt.font.size = Pt(12)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.add_run("Predição de risco de diabetes a partir de hábitos alimentares, condições demográficas e atividades físicas")

    doc.add_paragraph()
    p_bloco = doc.add_paragraph()
    p_bloco.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rb = p_bloco.add_run("Bloco 3 - Documentação Técnica e Relatório de Resultados")
    rb.bold = True

    for _ in range(5):
        doc.add_paragraph()

    p_loc = doc.add_paragraph()
    p_loc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_loc.add_run("Vitória da Conquista\n2026")

    doc.add_page_break()

    # --- SUMÁRIO ---
    p_sum = doc.add_paragraph()
    p_sum.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_sum = p_sum.add_run("SUMÁRIO")
    r_sum.bold = True
    doc.add_paragraph()

    for sec in SECOES_DOCUMENTO:
        ps = doc.add_paragraph()
        ps.paragraph_format.space_after = Pt(3)
        rs = ps.add_run(f"{sec['num']} {sec['titulo']}")
        rs.bold = True
        for sub in sec["subsecoes"]:
            psub = doc.add_paragraph()
            psub.paragraph_format.left_indent = Cm(0.6)
            psub.paragraph_format.space_after = Pt(2)
            psub.add_run(f"{sub['num']} {sub['titulo']}")

    ps_ref = doc.add_paragraph()
    rs_ref = ps_ref.add_run("REFERÊNCIAS")
    rs_ref.bold = True

    doc.add_page_break()

    # --- CORPO DO DOCUMENTO ---
    for sec in SECOES_DOCUMENTO:
        p_h1 = doc.add_paragraph()
        p_h1.paragraph_format.space_before = Pt(12)
        p_h1.paragraph_format.space_after = Pt(8)
        r_h1 = p_h1.add_run(f"{sec['num']} {sec['titulo']}")
        r_h1.bold = True
        r_h1.font.size = Pt(12)

        for sub in sec["subsecoes"]:
            p_h2 = doc.add_paragraph()
            p_h2.paragraph_format.space_before = Pt(10)
            p_h2.paragraph_format.space_after = Pt(6)
            r_h2 = p_h2.add_run(f"{sub['num']} {sub['titulo']}")
            r_h2.bold = True
            r_h2.font.size = Pt(12)

            for tipo, conteudo, *extra in sub["blocos"]:
                if tipo == "p":
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    p.paragraph_format.first_line_indent = Cm(1.25)
                    p.paragraph_format.line_spacing = 1.5
                    p.paragraph_format.space_after = Pt(6)
                    p.add_run(conteudo)
                elif tipo == "code":
                    p_code = doc.add_paragraph()
                    p_code.paragraph_format.left_indent = Cm(0.5)
                    p_code.paragraph_format.space_before = Pt(4)
                    p_code.paragraph_format.space_after = Pt(8)
                    rc = p_code.add_run(conteudo)
                    rc.font.name = "Consolas"
                    rc.font.size = Pt(9)
                elif tipo == "table":
                    legenda = conteudo
                    linhas_tab = extra[0]
                    p_leg = doc.add_paragraph()
                    p_leg.paragraph_format.space_before = Pt(8)
                    p_leg.paragraph_format.space_after = Pt(3)
                    r_leg = p_leg.add_run(legenda)
                    r_leg.font.size = Pt(10)

                    tab = doc.add_table(rows=len(linhas_tab), cols=len(linhas_tab[0]))
                    tab.style = "Table Grid"
                    tab.alignment = WD_TABLE_ALIGNMENT.CENTER
                    for i, row_vals in enumerate(linhas_tab):
                        for j, val in enumerate(row_vals):
                            cell = tab.cell(i, j)
                            if i == 0:
                                _set_cell_bg(cell, "E8E8E8")
                            p_c = cell.paragraphs[0]
                            r_c = p_c.add_run(str(val))
                            r_c.font.name = "Times New Roman"
                            r_c.font.size = Pt(9.5)
                            if i == 0:
                                r_c.bold = True
                    doc.add_paragraph()
                elif tipo == "figure":
                    nome_img = conteudo
                    legenda_fig = extra[0]
                    caminho_img = FIGURES_DIR / nome_img
                    if caminho_img.exists():
                        p_img = doc.add_paragraph()
                        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        p_img.add_run().add_picture(str(caminho_img), width=Cm(15.2))
                        p_cap = doc.add_paragraph()
                        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        r_cap = p_cap.add_run(legenda_fig)
                        r_cap.font.size = Pt(10)

    doc.add_page_break()
    p_ref_t = doc.add_paragraph()
    p_ref_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rr = p_ref_t.add_run("REFERÊNCIAS")
    rr.bold = True
    doc.add_paragraph()

    for ref in REFERENCIAS_ABNT:
        pr = doc.add_paragraph()
        pr.alignment = WD_ALIGN_PARAGRAPH.LEFT
        pr.paragraph_format.space_after = Pt(8)
        pr.paragraph_format.line_spacing = 1.15
        pr.add_run(ref)

    doc.save(caminho_docx)
    print(f"[DOCX] Gerado {caminho_docx}")


def _numerar_pagina_abnt(canvas, doc):
    """Numera as páginas no canto superior direito a partir da página 3 (padrão ABNT Bloco 2)."""
    page_num = canvas.getPageNumber()
    if page_num >= 3:
        canvas.saveState()
        canvas.setFont("Times-Roman", 10)
        canvas.drawRightString(A4[0] - 2.0 * cm, A4[1] - 2.0 * cm, str(page_num))
        canvas.restoreState()


def gerar_pdf_tecnico(caminho_pdf: Path) -> None:
    """Gera o PDF com tipografia Times-Roman, margens ABNT, quadros e figuras em 300 DPI."""
    doc = SimpleDocTemplate(
        str(caminho_pdf),
        pagesize=A4,
        topMargin=3.0 * cm,
        leftMargin=3.0 * cm,
        bottomMargin=2.0 * cm,
        rightMargin=2.0 * cm,
    )

    styles = getSampleStyleSheet()
    st_center_bold = ParagraphStyle(
        "ABNT_Center_Bold",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=12,
        leading=18,
        alignment=TA_CENTER,
    )
    st_center = ParagraphStyle(
        "ABNT_Center",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=12,
        leading=18,
        alignment=TA_CENTER,
    )
    st_h1 = ParagraphStyle(
        "ABNT_H1",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=12,
        leading=18,
        spaceBefore=14,
        spaceAfter=8,
        alignment=TA_LEFT,
    )
    st_h2 = ParagraphStyle(
        "ABNT_H2",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=12,
        leading=18,
        spaceBefore=12,
        spaceAfter=6,
        alignment=TA_LEFT,
    )
    st_body = ParagraphStyle(
        "ABNT_Body",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=12,
        leading=18,
        firstLineIndent=1.25 * cm,
        spaceAfter=6,
        alignment=TA_JUSTIFY,
    )
    st_caption = ParagraphStyle(
        "ABNT_Caption",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=10,
        leading=13,
        spaceBefore=6,
        spaceAfter=4,
        alignment=TA_LEFT,
    )
    st_code = ParagraphStyle(
        "ABNT_Code",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=8.2,
        leading=11,
        backColor=colors.HexColor("#F3F3F3"),
        borderPadding=6,
        spaceBefore=4,
        spaceAfter=8,
    )
    st_cell_hdr = ParagraphStyle(
        "ABNT_Cell_Hdr",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=9,
        leading=11.5,
        alignment=TA_LEFT,
    )
    st_cell = ParagraphStyle(
        "ABNT_Cell",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=8.8,
        leading=11.5,
        alignment=TA_LEFT,
    )
    st_ref = ParagraphStyle(
        "ABNT_Ref",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=11,
        leading=15,
        spaceAfter=8,
        alignment=TA_LEFT,
    )

    story = []

    # --- PÁGINA 1: CAPA IDÊNTICA AO BLOCO 2 ---
    story.append(Paragraph("UNEX – CENTRO UNIVERSITÁRIO DE EXCELÊNCIA", st_center_bold))
    story.append(Paragraph("BACHARELADO EM SISTEMAS DE INFORMAÇÃO", st_center_bold))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("Disciplina: Mineração de Dados - Orientador: Wallas Froes de Oliveira", st_center))
    story.append(Spacer(1, 1.2 * cm))
    story.append(Paragraph("Integrantes:", st_center))
    for nome in INTEGRANTES:
        story.append(Paragraph(nome, st_center))

    story.append(Spacer(1, 3.8 * cm))
    story.append(
        Paragraph(
            "EXECUÇÃO DA MINERAÇÃO, RESULTADOS, VALIDAÇÃO E DOCUMENTAÇÃO TÉCNICA DE IMPLEMENTAÇÃO E TESTES",
            st_center_bold,
        )
    )
    story.append(Spacer(1, 0.4 * cm))
    story.append(
        Paragraph(
            "Predição de risco de diabetes a partir de hábitos alimentares, condições demográficas e atividades físicas",
            st_center,
        )
    )
    story.append(Spacer(1, 1.0 * cm))
    story.append(Paragraph("Bloco 3 - Documentação Técnica e Relatório de Resultados", st_center_bold))
    story.append(Spacer(1, 5.2 * cm))
    story.append(Paragraph("Vitória da Conquista", st_center))
    story.append(Paragraph("2026", st_center))
    story.append(PageBreak())

    # --- PÁGINA 2: SUMÁRIO ---
    story.append(Paragraph("SUMÁRIO", st_center_bold))
    story.append(Spacer(1, 0.6 * cm))
    pag_sumario = {
        "1": "3", "1.1": "3", "1.2": "3", "1.3": "4", "1.4": "6",
        "2": "7", "2.1": "7", "2.2": "7", "2.3": "8",
        "3": "8", "3.1": "8", "3.2": "9",
        "4": "10", "4.1": "10", "4.2": "11", "4.3": "13", "4.4": "16", "4.5": "16",
        "5": "19", "5.1": "19", "5.2": "20",
        "REF": "21",
    }
    st_toc_l1 = ParagraphStyle("TOCL1", parent=styles["Normal"], fontName="Times-Bold", fontSize=11, leading=16)
    st_toc_l2 = ParagraphStyle("TOCL2", parent=styles["Normal"], fontName="Times-Roman", fontSize=11, leading=15, leftIndent=0.4 * cm)
    st_toc_pg_b = ParagraphStyle("TOCPGB", parent=styles["Normal"], fontName="Times-Bold", fontSize=11, leading=16, alignment=2)
    st_toc_pg = ParagraphStyle("TOCPG", parent=styles["Normal"], fontName="Times-Roman", fontSize=11, leading=15, alignment=2)

    linhas_toc = []
    for sec in SECOES_DOCUMENTO:
        pg1 = pag_sumario.get(sec["num"], "")
        linhas_toc.append([Paragraph(f"{sec['num']} {sec['titulo']}", st_toc_l1), Paragraph(pg1, st_toc_pg_b)])
        for sub in sec["subsecoes"]:
            pg2 = pag_sumario.get(sub["num"], "")
            linhas_toc.append([Paragraph(f"{sub['num']} {sub['titulo']}", st_toc_l2), Paragraph(pg2, st_toc_pg)])
    linhas_toc.append([Paragraph("REFERÊNCIAS", st_toc_l1), Paragraph(pag_sumario["REF"], st_toc_pg_b)])

    largura_util_toc = A4[0] - 5.0 * cm
    t_toc = Table(linhas_toc, colWidths=[largura_util_toc * 0.90, largura_util_toc * 0.10])
    t_toc.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#CCCCCC"), 1, (1, 2)),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(t_toc)
    story.append(PageBreak())

    # --- CORPO DO DOCUMENTO ---
    largura_util = A4[0] - 5.0 * cm
    for sec in SECOES_DOCUMENTO:
        story.append(Paragraph(f"{sec['num']} {sec['titulo']}", st_h1))
        for sub in sec["subsecoes"]:
            story.append(Paragraph(f"{sub['num']} {sub['titulo']}", st_h2))
            for tipo, conteudo, *extra in sub["blocos"]:
                if tipo == "p":
                    texto_xml = (
                        conteudo.replace("&", "&amp;")
                        .replace("<=", "&le;")
                        .replace(">=", "&ge;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                    )
                    story.append(Paragraph(texto_xml, st_body))
                elif tipo == "code":
                    story.append(Preformatted(conteudo, st_code))
                elif tipo == "table":
                    legenda = conteudo
                    linhas_tab = extra[0]
                    n_cols = len(linhas_tab[0])
                    dados_formatados = []
                    for i, r in enumerate(linhas_tab):
                        estilo_c = st_cell_hdr if i == 0 else st_cell
                        dados_formatados.append([
                            Paragraph(
                                str(c).replace("&", "&amp;").replace("<=", "&le;").replace(">=", "&ge;").replace("<", "&lt;").replace(">", "&gt;"),
                                estilo_c,
                            )
                            for c in r
                        ])
                    col_widths = [largura_util / n_cols] * n_cols
                    if n_cols == 4:
                        col_widths = [largura_util * 0.20, largura_util * 0.24, largura_util * 0.32, largura_util * 0.24]
                    elif n_cols == 6:
                        col_widths = [largura_util * 0.18, largura_util * 0.16, largura_util * 0.14, largura_util * 0.15, largura_util * 0.17, largura_util * 0.20]
                    elif n_cols == 8:
                        col_widths = [
                            largura_util * 0.20, largura_util * 0.14, largura_util * 0.10, largura_util * 0.09,
                            largura_util * 0.10, largura_util * 0.09, largura_util * 0.11, largura_util * 0.17,
                        ]
                    t = Table(dados_formatados, colWidths=col_widths, repeatRows=1)
                    t.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#555555")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ]))
                    story.append(Paragraph(legenda, st_caption))
                    story.append(t)
                    story.append(Spacer(1, 0.3 * cm))
                elif tipo == "figure":
                    nome_img = conteudo
                    legenda_fig = extra[0]
                    caminho_img = FIGURES_DIR / nome_img
                    if caminho_img.exists():
                        img_rl = RLImage(str(caminho_img), width=15.2 * cm, height=8.2 * cm, kind="proportional")
                        story.append(KeepTogether([
                            Spacer(1, 0.2 * cm),
                            img_rl,
                            Paragraph(legenda_fig, st_caption),
                            Spacer(1, 0.25 * cm),
                        ]))

    story.append(PageBreak())
    story.append(Paragraph("REFERÊNCIAS", st_center_bold))
    story.append(Spacer(1, 0.5 * cm))
    for ref in REFERENCIAS_ABNT:
        story.append(Paragraph(ref.replace("&", "&amp;"), st_ref))

    doc.build(story, onFirstPage=_numerar_pagina_abnt, onLaterPages=_numerar_pagina_abnt)
    print(f"[PDF] Gerado {caminho_pdf}")


if __name__ == "__main__":
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    docx_path = DOCS_DIR / "Bloco_3_Documentacao_Tecnica_Implementacao_Resultados_e_Testes.docx"
    pdf_path = DOCS_DIR / "Bloco_3_Documentacao_Tecnica_Implementacao_Resultados_e_Testes.pdf"
    gerar_docx_tecnico(docx_path)
    gerar_pdf_tecnico(pdf_path)

