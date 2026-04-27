#requires -Version 5.1
param(
    [switch]$SkipPush,
    [switch]$WhatIf
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Run-Command {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [Parameter()]
        [string[]]$Arguments = @(),

        [Parameter()]
        [switch]$AllowFailure,

        [Parameter()]
        [string]$WorkingDirectory = (Get-Location).Path
    )

    function Format-ProcessArgument {
        param(
            [Parameter(Mandatory = $true)]
            [string]$Value
        )

        if ($Value -notmatch '[\s"]') {
            return $Value
        }

        $escaped = $Value -replace '(\\*)"', '$1$1\"'
        $escaped = $escaped -replace '(\\+)$', '$1$1'
        return '"' + $escaped + '"'
    }

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FilePath
    $psi.WorkingDirectory = $WorkingDirectory
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    $psi.Arguments = (($Arguments | ForEach-Object { Format-ProcessArgument -Value $_ }) -join ' ')

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $psi
    [void]$process.Start()

    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()

    $exitCode = $process.ExitCode
    $text = (($stdout, $stderr) -join [Environment]::NewLine).Trim()

    if ((-not $AllowFailure) -and $exitCode -ne 0) {
        $joinedArguments = $Arguments -join ' '
        throw "Command failed: $FilePath $joinedArguments`n$text"
    }

    return @{
        ExitCode = $exitCode
        Output = $text
    }
}

function Log-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    Write-Host "[sync] $Message"
}

function Copy-Directory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SourcePath,

        [Parameter(Mandatory = $true)]
        [string]$DestinationPath
    )

    Copy-Item -LiteralPath $SourcePath -Destination $DestinationPath -Recurse -Force
}

function Test-RepoPathIgnored {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot,

        [Parameter(Mandatory = $true)]
        [string]$RelativePath,

        [Parameter()]
        [string[]]$IgnorePatterns = @()
    )

    $result = Run-Command -FilePath 'git' -Arguments @('-C', $RepoRoot, 'check-ignore', $RelativePath) -AllowFailure -WorkingDirectory $RepoRoot
    if ($result.ExitCode -eq 0) {
        return $true
    }

    foreach ($pattern in $IgnorePatterns) {
        $normalizedPattern = $pattern.Replace('/', '\')
        $normalizedPath = $RelativePath.Replace('/', '\')

        if ($normalizedPattern.EndsWith('\')) {
            $normalizedPattern = $normalizedPattern + '*'
        }

        if ($normalizedPath -like $normalizedPattern) {
            return $true
        }
    }

    return $false
}

function Assert-GitIndexUnlocked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot
    )

    $lockPath = Join-Path $RepoRoot '.git\index.lock'
    if (-not (Test-Path -LiteralPath $lockPath -PathType Leaf)) {
        return
    }

    $gitProcesses = Get-CimInstance Win32_Process -Filter "name = 'git.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like "*$RepoRoot*" }

    if ($gitProcesses) {
        $processSummary = $gitProcesses |
            ForEach-Object { "PID=$($_.ProcessId) CMD=$($_.CommandLine)" }
        throw "Git index.lock exists and repository still has active git.exe processes.`n$($processSummary -join [Environment]::NewLine)"
    }

    Remove-Item -LiteralPath $lockPath -Force
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$userHome = [Environment]::GetFolderPath('UserProfile')
$sourceAgentsPath = Join-Path $userHome '.codex\AGENTS.md'
$fallbackAgentsPath = Join-Path $userHome 'AGENTS.md'
$sourceSkillsRoot = Join-Path $userHome '.codex\skills'
$destinationAgentsPath = Join-Path $repoRoot 'AGENTS.md'
$gitIgnorePath = Join-Path $repoRoot '.gitignore'
$preserveNames = @('.git', '.gitignore', 'LICENSE', 'README.md', 'sync-codex-global.ps1')
$ignorePatterns = @()
if (Test-Path -LiteralPath $gitIgnorePath -PathType Leaf) {
    $ignorePatterns = ([IO.File]::ReadAllText($gitIgnorePath) -split "`r?`n") |
        ForEach-Object { $_.Trim() } |
        Where-Object { $_ -and -not $_.StartsWith('#') }
}

if (-not (Test-Path -LiteralPath $sourceAgentsPath -PathType Leaf)) {
    if (Test-Path -LiteralPath $fallbackAgentsPath -PathType Leaf) {
        $sourceAgentsPath = $fallbackAgentsPath
    }
    else {
        throw "Global AGENTS.md not found. Checked: $sourceAgentsPath ; $fallbackAgentsPath"
    }
}

if (-not (Test-Path -LiteralPath $sourceSkillsRoot -PathType Container)) {
    throw "Global skills directory not found: $sourceSkillsRoot"
}

$skillDirectories = Get-ChildItem -LiteralPath $sourceSkillsRoot -Force |
    Where-Object { $_.PSIsContainer } |
    Where-Object { -not (Test-RepoPathIgnored -RepoRoot $repoRoot -RelativePath ($_.Name + '/') -IgnorePatterns $ignorePatterns) } |
    Sort-Object Name

if (-not $skillDirectories) {
    throw "No installed skills found under $sourceSkillsRoot"
}

Log-Step "repo root: $repoRoot"
Log-Step "source agents: $sourceAgentsPath"
Log-Step "source skills: $sourceSkillsRoot"
Log-Step "installed skills: $($skillDirectories.Count)"
if ($ignorePatterns.Count -gt 0) {
    Log-Step "ignore rules: $($ignorePatterns -join ', ')"
}
Assert-GitIndexUnlocked -RepoRoot $repoRoot

$repoEntries = Get-ChildItem -LiteralPath $repoRoot -Force
foreach ($entry in $repoEntries) {
    if ($preserveNames -contains $entry.Name) {
        continue
    }

    if ($WhatIf) {
        Log-Step "whatif remove: $($entry.FullName)"
    }
    else {
        Remove-Item -LiteralPath $entry.FullName -Recurse -Force
    }
}

if ($WhatIf) {
    Log-Step "whatif copy: $sourceAgentsPath -> $destinationAgentsPath"
}
else {
    Copy-Item -LiteralPath $sourceAgentsPath -Destination $destinationAgentsPath -Force
}

foreach ($skillDirectory in $skillDirectories) {
    $destinationPath = Join-Path $repoRoot $skillDirectory.Name

    if ($WhatIf) {
        Log-Step "whatif copy skill: $($skillDirectory.FullName) -> $destinationPath"
    }
    else {
        Copy-Directory -SourcePath $skillDirectory.FullName -DestinationPath $destinationPath
    }
}

$repoView = Run-Command -FilePath 'gh' -Arguments @('repo', 'view', '--json', 'nameWithOwner,defaultBranchRef') -WorkingDirectory $repoRoot
$repoJson = $repoView.Output | ConvertFrom-Json
$remoteRepo = $repoJson.nameWithOwner
$defaultBranch = $repoJson.defaultBranchRef.name

if ([string]::IsNullOrWhiteSpace($remoteRepo)) {
    throw 'Failed to resolve remote repository via gh repo view.'
}

if ([string]::IsNullOrWhiteSpace($defaultBranch)) {
    throw 'Failed to resolve remote default branch via gh repo view.'
}

Log-Step "remote repo: $remoteRepo"
Log-Step "default branch: $defaultBranch"

if ($WhatIf) {
    Log-Step 'whatif git add -A'
    Log-Step 'whatif git diff --cached --name-status'
}
else {
    Run-Command -FilePath 'git' -Arguments @('-C', $repoRoot, 'add', '-A') -WorkingDirectory $repoRoot | Out-Null
}

$stagedOutput = ''
if (-not $WhatIf) {
    $stagedDiff = Run-Command -FilePath 'git' -Arguments @('-C', $repoRoot, 'diff', '--cached', '--name-status') -WorkingDirectory $repoRoot
    $stagedOutput = $stagedDiff.Output
}

$createdCommit = $false
if ($WhatIf) {
    Log-Step 'whatif git commit -m "sync: export codex global agents and skills"'
}
elseif (-not [string]::IsNullOrWhiteSpace($stagedOutput)) {
    Run-Command -FilePath 'git' -Arguments @('-C', $repoRoot, 'commit', '-m', 'sync: export codex global agents and skills') -WorkingDirectory $repoRoot | Out-Null
    $createdCommit = $true
}

$performedPush = $false
if ($SkipPush) {
    Log-Step 'skip push requested'
}
elseif ($WhatIf) {
    Log-Step "whatif git push --force origin HEAD:$defaultBranch"
}
else {
    Run-Command -FilePath 'git' -Arguments @('-C', $repoRoot, 'push', '--force', 'origin', "HEAD:$defaultBranch") -WorkingDirectory $repoRoot | Out-Null
    $performedPush = $true
}

Write-Host "RepoRoot: $repoRoot"
Write-Host "SourceAgents: $sourceAgentsPath"
Write-Host "SourceSkillsRoot: $sourceSkillsRoot"
Write-Host "ExportedSkills: $($skillDirectories.Count)"
Write-Host "Committed: $createdCommit"
Write-Host "Pushed: $performedPush"
Write-Host "RemoteRepo: $remoteRepo"
Write-Host "DefaultBranch: $defaultBranch"
