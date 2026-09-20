# Resolve `conan` even when Scripts/ não está no PATH (pip --user).
$ErrorActionPreference = "Stop"

$candidates = @(
  (Get-Command conan -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source),
  "$env:APPDATA\Python\Python311\Scripts\conan.exe",
  "$env:APPDATA\Python\Python312\Scripts\conan.exe",
  "$env:APPDATA\Python\Python310\Scripts\conan.exe",
  "$env:LOCALAPPDATA\Programs\Python\Python311\Scripts\conan.exe",
  "C:\Python311\Scripts\conan.exe",
  "C:\Python310\Scripts\conan.exe"
) | Where-Object { $_ -and (Test-Path $_) }

if (-not $candidates) {
  Write-Error @"
Conan 2 não encontrado.
Instale com:  python -m pip install --user `"conan>=2,<3`"
E garanta que %APPDATA%\Python\Python3X\Scripts está no PATH, ou volte a correr esta task.
"@
}

$Conan = $candidates | Select-Object -First 1
Write-Host "Usando Conan: $Conan"
# Argumentos como array explícito (evita que -pr:h seja interpretado pelo PowerShell).
& $Conan @args
exit $LASTEXITCODE
