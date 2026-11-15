@echo off
chcp 65001 > nul
title Radar Preditivo de Diabetes - Bloco 3 (UNEX)
cd /d "%~dp0"
cls
echo ============================================================================
echo   RADAR PREDITIVO DE DIABETES - DEMONSTRACAO EXECUTIVA (BLOCO 3 - UNEX)
echo ============================================================================
echo.
echo [1/3] Carregando modelos preditivos (Random Forest, Regressao Logistica e Arvore)...
echo [2/3] Conectando a base analitica NHANES + IBGE + DATASUS (n = 5.131 adultos)...
echo [3/3] Servidor web local iniciado com sucesso!
echo.
echo  --^> O painel interativo (100%% em Portugues) foi aberto no seu navegador:
echo      http://localhost:8501
echo.
echo  --^> Mantenha esta janela aberta enquanto estiver usando o sistema.
echo  --^> Para encerrar o servidor, basta fechar esta janela ou pressionar Ctrl+C.
echo ============================================================================
python -m streamlit run app/app_radar_diabetes.py --browser.gatherUsageStats=false --logger.level=error > nul 2>&1
pause
