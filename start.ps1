# Script para iniciar Backend e Frontend simultaneamente

Write-Host "Iniciando Gerenciador de Peças..." -ForegroundColor Cyan

# 1. Iniciar o Backend em uma nova janela
Write-Host "Iniciando Backend (Uvicorn)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; `$env:PYTHONPATH='.'; python -m uvicorn app.main:app --reload"

# 2. Iniciar o Frontend em uma nova janela
Write-Host "Iniciando Frontend (Vite)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend_new; npm run dev"

Write-Host "Ambos os serviços foram iniciados em novas janelas!" -ForegroundColor Green
Write-Host "Pronto para usar." -ForegroundColor White
