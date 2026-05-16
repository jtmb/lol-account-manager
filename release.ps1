param(
    [string]$Tag,
    [string]$Title,
    [string]$Repo,
    [switch]$Draft,
    [switch]$Prerelease,
    [switch]$SkipBuild,
    [switch]$OpenRelease
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[*] $Message" -ForegroundColor Cyan
}

function Fail {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
    exit 1
}

function Get-ProjectVersion {
    param([string]$ConfigPath)

    if (-not (Test-Path $ConfigPath)) {
        return $null
    }

    try {
        $json = Get-Content -Raw -Path $ConfigPath | ConvertFrom-Json
        if ($null -ne $json.app_version -and "$($json.app_version)".Trim().Length -gt 0) {
            return "$($json.app_version)".Trim()
        }
    }
    catch {
        return $null
    }

    return $null
}

function Resolve-RepoSlug {
    param([string]$RemoteUrl)

    if ([string]::IsNullOrWhiteSpace($RemoteUrl)) {
        return $null
    }

    # Supports:
    # - https://github.com/owner/repo.git
    # - git@github.com:owner/repo.git
    $url = $RemoteUrl.Trim()
    if ($url -match "github\.com[:/](?<slug>[^\s]+?)(\.git)?$") {
        return $Matches["slug"]
    }

    return $null
}

function Get-CommitNotes {
    param([string]$Range)

    $subjects = @()
    if ([string]::IsNullOrWhiteSpace($Range)) {
        $subjects = @(git log --pretty=format:"%s" 2>$null)
    }
    else {
        $subjects = @(git log $Range --pretty=format:"%s" 2>$null)
    }

    if ($LASTEXITCODE -ne 0) {
        return @()
    }

    $subjects = $subjects |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
        Where-Object { $_ -notmatch "^merge\b" }

    return $subjects
}

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Fail "git is required but not found in PATH."
}
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Fail "GitHub CLI (gh) is required but not found in PATH."
}

Write-Step "Checking GitHub CLI authentication"
$null = gh auth status 2>$null
if ($LASTEXITCODE -ne 0) {
    Fail "gh is not authenticated. Run: gh auth login"
}

if ([string]::IsNullOrWhiteSpace($Repo)) {
    $originUrl = git remote get-url origin 2>$null
    if ($LASTEXITCODE -eq 0) {
        $Repo = Resolve-RepoSlug -RemoteUrl $originUrl
    }
}
if ([string]::IsNullOrWhiteSpace($Repo)) {
    Fail "Could not determine GitHub repo slug. Pass -Repo owner/repo"
}

$projectVersion = Get-ProjectVersion -ConfigPath (Join-Path $root "app_config.json")
if ([string]::IsNullOrWhiteSpace($Tag)) {
    if ([string]::IsNullOrWhiteSpace($projectVersion)) {
        Fail "Unable to determine version. Pass -Tag explicitly."
    }
    $Tag = "$projectVersion"
}
if ([string]::IsNullOrWhiteSpace($Title)) {
    $Title = "LoL Account Manager $Tag"
}

Write-Step "Using repo: $Repo"
Write-Step "Using tag: $Tag"

if (-not $SkipBuild) {
    Write-Step "Running build_exe.bat"
    cmd /c build_exe.bat
    if ($LASTEXITCODE -ne 0) {
        Fail "build_exe.bat failed"
    }
}
else {
    Write-Step "Skipping build step"
}

$distDir = Join-Path $root "dist\LoLAccountManager"
if (-not (Test-Path $distDir)) {
    Fail "Build output not found: $distDir"
}

$zipPath = Join-Path $root "LoLAccountManager.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Write-Step "Creating release archive"
Compress-Archive -Path (Join-Path $distDir "*") -DestinationPath $zipPath -Force
if (-not (Test-Path $zipPath)) {
    Fail "Failed to create zip artifact"
}

$lastTag = ""
$lastTag = (git describe --tags --abbrev=0 2>$null)
if ($LASTEXITCODE -ne 0) {
    $lastTag = ""
}

$range = ""
if (-not [string]::IsNullOrWhiteSpace($lastTag)) {
    $range = "$lastTag..HEAD"
}

Write-Step "Generating release notes from git history"
$commitSubjects = Get-CommitNotes -Range $range

$featureLines = @()
if ($commitSubjects.Count -eq 0) {
    $featureLines += "- No new commits detected since the previous release tag."
}
else {
    foreach ($subject in $commitSubjects) {
        $featureLines += "- $subject"
    }
}

$downloadUrl = "https://github.com/$Repo/releases/download/$Tag/LoLAccountManager.zip"
$bugUrl = "https://github.com/$Repo/issues/new?assignees=&labels=bug&title=bug%3A+"
$featureUrl = "https://github.com/$Repo/issues/new?assignees=&labels=enhancement&title=feat%3A+"
$repoUrl = "https://github.com/$Repo"
$logoUrl = "https://github.com/jtmb/lol-account-manager/blob/main/assets/icon.ico"

$releaseNotesPath = Join-Path $root "release-notes.generated.md"
$releaseBody = @"
<h1 align="center">
	<a href="$repoUrl">
		<img src="$logoUrl" alt="LoL Account Manager Logo" width="220" height="auto">
	</a>
</h1>

<div align="center">
	<b>League of Legends Account Manager</b> - Securely manage, organize, and launch multiple LoL accounts from one desktop app.
	<br />
	<br />
	<a href="$downloadUrl">Download</a>
	·
	<a href="$bugUrl">Report a Bug</a>
	·
	<a href="$featureUrl">Request a Feature</a>
</div>

<br>

New features for this release include:

$($featureLines -join "`n")

-------------------------


**Install Instructions**

1. Download [LoLAccountManager.zip]($downloadUrl)

2. Extract the contents of the ZIP file.

3. Run LoLAccountManager.exe

4. You may see Windows SmartScreen warnings because the application is not yet digitally signed. These warnings are expected and can be safely ignored.
"@

Set-Content -Path $releaseNotesPath -Value $releaseBody -Encoding UTF8

Write-Step "Creating GitHub release"
$ghArgs = @(
    "release", "create", $Tag,
    $zipPath,
    "--repo", $Repo,
    "--title", $Title,
    "--notes-file", $releaseNotesPath
)
if ($Draft) {
    $ghArgs += "--draft"
}
if ($Prerelease) {
    $ghArgs += "--prerelease"
}

gh @ghArgs
if ($LASTEXITCODE -ne 0) {
    Fail "Failed to create GitHub release"
}

Write-Host "[SUCCESS] Release created: $Tag" -ForegroundColor Green
Write-Host "[INFO] Artifact: $zipPath" -ForegroundColor Green
Write-Host "[INFO] Notes file: $releaseNotesPath" -ForegroundColor Green

if ($OpenRelease) {
    gh release view $Tag --repo $Repo --web | Out-Null
}
