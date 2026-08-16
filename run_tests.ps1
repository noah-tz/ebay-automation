# Run tests and generate Allure report
# Usage: .\run_tests.ps1

Write-Host "Running tests..." -ForegroundColor Cyan
& .\venv\Scripts\python.exe -m pytest tests/ -v

Write-Host "`nGenerating Allure report..." -ForegroundColor Cyan
allure generate reports/allure-results -o reports/allure-report --clean

Write-Host "`nOpening report in browser..." -ForegroundColor Green
allure open reports/allure-report
