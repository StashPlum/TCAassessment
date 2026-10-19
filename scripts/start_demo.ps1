param([switch]$SkipInstall)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $projectRoot
if (Test-Path -LiteralPath '.env') {
    Get-Content -LiteralPath '.env' | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line.Contains('=')) {
            $parts = $line.Split('=', 2)
            [Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim(), 'Process')
        }
    }
}
$bundledPython = 'C:\Users\stash\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$pythonExe = if (Test-Path -LiteralPath $bundledPython) { $bundledPython } else { (Get-Command python -ErrorAction Stop).Source }
if (-not $SkipInstall) {
    & $pythonExe -m pip install --target .vendor --upgrade -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
}
$env:PYTHONPATH = (Resolve-Path '.vendor').Path
& $pythonExe tools/extract_sources.py
if ($LASTEXITCODE -ne 0) { throw 'Source extraction failed.' }
& $pythonExe manage.py migrate --noinput
if ($LASTEXITCODE -ne 0) { throw 'Migration failed.' }
& $pythonExe manage.py import_catalog
if ($LASTEXITCODE -ne 0) { throw 'Catalog import failed.' }
& $pythonExe manage.py seed_demo
if ($LASTEXITCODE -ne 0) { throw 'Demo seed failed.' }
Write-Host 'Open http://127.0.0.1:8000/login/ with demo / LocalDemo2026! (fictional local data).'
& $pythonExe manage.py runserver 127.0.0.1:8000 --noreload
