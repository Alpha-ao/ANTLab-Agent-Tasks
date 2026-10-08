Set-Location (Split-Path $PSScriptRoot -Parent)
$env:PYTHONIOENCODING='utf-8'
python scripts/serve_v2.py --port 8768
