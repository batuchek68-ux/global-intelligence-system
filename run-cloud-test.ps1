param(
    [string]$Repository = $env:GITHUB_REPOSITORY,
    [string]$Token = $env:GITHUB_TOKEN,
    [string]$Branch = "main",
    [switch]$CreateRepo,
    [switch]$Upload,
    [switch]$Public,
    [switch]$NoTrigger
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

function Test-RepositoryName {
    param([string]$Value)
    if (-not $Value) {
        return $false
    }
    $Parts = $Value.Split("/")
    if ($Parts.Count -ne 2) {
        return $false
    }
    $Owner = $Parts[0]
    $Name = $Parts[1]
    if ($Owner -ne $Owner.Trim() -or $Name -ne $Name.Trim()) {
        return $false
    }
    if ([string]::IsNullOrWhiteSpace($Owner) -or [string]::IsNullOrWhiteSpace($Name)) {
        return $false
    }
    if ($Owner -match '^(owner|yourname|username)$' -or $Name -match '^(repository|repo)$') {
        return $false
    }
    return $Owner -match '^[A-Za-z0-9]([A-Za-z0-9-]{0,38}[A-Za-z0-9])?$' -and $Name -match '^[A-Za-z0-9._-]+$'
}

if (-not $Token -and $env:GH_TOKEN) {
    $Token = $env:GH_TOKEN
}

if (-not $Repository) {
    $LocalConfig = Join-Path $ProjectRoot "cloud.local.json"
    if (Test-Path $LocalConfig) {
        $Config = Get-Content $LocalConfig -Raw | ConvertFrom-Json
        $Repository = $Config.repository
        if ($Config.branch -and $Branch -eq "main") {
            $Branch = $Config.branch
        }
    }
}

if (-not $Token -or -not $Repository) {
    Write-Host "Missing GitHub cloud test configuration." -ForegroundColor Yellow
    Write-Host "Set GITHUB_TOKEN or GH_TOKEN, and GITHUB_REPOSITORY as owner/repository."
    Write-Host ""
    Write-Host "Example:"
    Write-Host '$env:GITHUB_TOKEN = "your GitHub token"'
    Write-Host '$env:GITHUB_REPOSITORY = "owner/repository"'
    Write-Host 'Or copy cloud.local.example.json to cloud.local.json and set repository there.'
    Write-Host '.\run-cloud-test.ps1 -CreateRepo'
    python workflows\cloud_run.py
    python workflows\cloud_test_status.py
    exit $LASTEXITCODE
}

if (-not (Test-RepositoryName $Repository)) {
    Write-Host "Repository must be a real GitHub owner/repository, for example octocat/international-trade-ai." -ForegroundColor Yellow
    python workflows\cloud_run.py --repository $Repository
    python workflows\cloud_test_status.py
    exit 2
}

$env:GITHUB_TOKEN = $Token
$env:GITHUB_REPOSITORY = $Repository
$env:GITHUB_REF_NAME = $Branch

$argsList = @("workflows\cloud_run.py", "--repository", $Repository, "--branch", $Branch)

if ($CreateRepo) {
    $argsList += "--create-repo"
    $argsList += "--confirm-upload"
} elseif ($Upload) {
    $argsList += "--upload"
    $argsList += "--confirm-upload"
}

if ($Public) {
    $argsList += "--public"
}

if ($NoTrigger) {
    $argsList += "--no-trigger"
}

python @argsList
exit $LASTEXITCODE
