<#
.SYNOPSIS
    Native installer for the Antigravity Agentic Workflows ecosystem (Windows / PowerShell).

.DESCRIPTION
    Copies and synchronizes prompts, workflows, and skills from the repository into the global
    scope (~/.gemini) or a specific project directory (.agents/).
    Includes safety safeguards with timestamped backups (YYYYMMDD_HHMM), transactional
    rollback with manifest.json, and safe uninstallation.

.PARAMETER Global
    Installs to global user scope (~/.gemini).

.PARAMETER Project
    Path to project directory where customizations will be installed (.agents/ and GEMINI.md).

.PARAMETER Force
    Overwrites existing files without terminal confirmation (still creates timestamped backups).

.PARAMETER NoBackup
    Disables creating the timestamped backup directory.

.PARAMETER DryRun
    Simulates actions and displays file operations without modifying files on disk.

.PARAMETER Restore
    Restores previously backed-up files from a timestamped backup snapshot directory.

.PARAMETER Uninstall
    Safely removes installed workflows, skills, and rules from the selected scope.

.PARAMETER BackupName
    Non-interactive name of backup directory snapshot to restore.

.PARAMETER BackupIndex
    Non-interactive numeric index of backup directory snapshot to restore.

.EXAMPLE
    .\install.ps1 -Global
    Installs into global scope (~/.gemini).

.EXAMPLE
    .\install.ps1 -Project "C:\Projects\my-app"
    Installs into a specific project.

.EXAMPLE
    .\install.ps1 -Restore
    Opens interactive rollback menu to restore a previously created backup snapshot.

.EXAMPLE
    .\install.ps1 -Uninstall
    Opens interactive uninstall menu to safely remove installed workflows, skills, and rules.

.EXAMPLE
    .\install.ps1 -Global -DryRun
    Simulates global installation listing all affected files.
#>

[CmdletBinding()]
param (
    [switch]$Global,
    [string]$Project,
    [switch]$Force,
    [switch]$NoBackup,
    [switch]$DryRun,
    [switch]$Restore,
    [switch]$Uninstall,
    [string]$BackupName,
    [int]$BackupIndex = 0
)

# Set UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Base repository locations
$RepoRoot = $PSScriptRoot
$SourcePrompts = Join-Path $RepoRoot "prompts"
$SourceWorkflows = Join-Path $RepoRoot "workflows"
$SourceSkills = Join-Path $RepoRoot "skills"
$SourceGeminiRule = Join-Path $SourcePrompts "gemini.md"

# Transaction trackers for installation manifest
$script:TxModified = @()
$script:TxAdded = @()

# Validate sources (only mandatory when performing installation)
if (-not $Restore -and -not $Uninstall -and -not (Test-Path $SourceSkills)) {
    Write-Host "[ERROR] 'skills' directory not found in: $RepoRoot" -ForegroundColor Red
    Write-Host "Make sure you are running the script from the root of the cloned/extracted repository." -ForegroundColor Yellow
    exit 1
}

# Colors and formatting
function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Cyan
}

function Write-Success { param([string]$Text) Write-Host "  [OK] $Text" -ForegroundColor Green }
function Write-Info { param([string]$Text) Write-Host "  [INFO] $Text" -ForegroundColor Gray }
function Write-Warn { param([string]$Text) Write-Host "  [WARN] $Text" -ForegroundColor Yellow }
function Write-Sim { param([string]$Text) Write-Host "  [SIMULATION] $Text" -ForegroundColor Magenta }

# Helper to resolve cross-platform user home path
function Get-UserHomeDirectory {
    $homePath = [Environment]::GetFolderPath('UserProfile')
    if ([string]::IsNullOrWhiteSpace($homePath)) {
        if ($env:USERPROFILE) {
            $homePath = $env:USERPROFILE
        }
        else {
            $homePath = $env:HOME
        }
    }
    return $homePath
}

# Restore handler function
function Invoke-Restore {
    param(
        [switch]$GlobalScope,
        [string]$ProjectPath,
        [switch]$DryRunMode,
        [switch]$ForceMode,
        [string]$SelectedBackupName,
        [int]$SelectedBackupIndex = 0
    )

    $UserHome = Get-UserHomeDirectory
    $isGlobal = $GlobalScope
    $targetProject = $ProjectPath

    # Prompt scope if neither -Global nor -Project was supplied
    if (-not $isGlobal -and [string]::IsNullOrWhiteSpace($targetProject)) {
        Write-Header "Restore Backup Scope"
        Write-Host "Choose backup scope to restore:`n"
        Write-Host "  [1] Global  (~/.gemini/backups) - Backups from global installations" -ForegroundColor White
        Write-Host "  [2] Project (.agents/backups)   - Backups from project installations" -ForegroundColor White
        Write-Host "  [3] Cancel" -ForegroundColor White
        Write-Host ""

        $scopeChoice = Read-Host "Enter option [1-3]"
        switch ($scopeChoice.Trim()) {
            "1" { $isGlobal = $true }
            "2" {
                $inputProj = Read-Host "Enter project directory path (absolute or relative)"
                if ([string]::IsNullOrWhiteSpace($inputProj)) {
                    Write-Host "[ERROR] Project path cannot be empty." -ForegroundColor Red
                    return
                }
                $targetProject = $inputProj.Trim()
            }
            default {
                Write-Host "Restoration canceled by user." -ForegroundColor Yellow
                return
            }
        }
    }

    if ($isGlobal) {
        $ScopeName = "Global"
        $TargetBase = Join-Path $UserHome ".gemini"
        $BackupRootDir = Join-Path $TargetBase "backups"
        $TargetRuleFile = Join-Path $TargetBase "GEMINI.md"
        $TargetWorkflowsDir = Join-Path $TargetBase "config\global_workflows"
        $TargetSkillsDir = Join-Path $TargetBase "config\skills"
    }
    else {
        $ScopeName = "Project"
        if (Test-Path $targetProject) {
            $TargetProjectRoot = (Resolve-Path $targetProject).Path
        }
        else {
            $TargetProjectRoot = [System.IO.Path]::GetFullPath($targetProject)
        }
        $TargetBase = Join-Path $TargetProjectRoot ".agents"
        $BackupRootDir = Join-Path $TargetBase "backups"
        $TargetRuleFile = Join-Path $TargetProjectRoot "GEMINI.md"
        $TargetWorkflowsDir = Join-Path $TargetBase "workflows"
        $TargetSkillsDir = Join-Path $TargetBase "skills"
    }

    if (-not (Test-Path $BackupRootDir)) {
        Write-Warn "Backup directory not found: $BackupRootDir"
        return
    }

    $backupDirs = @(Get-ChildItem -Path $BackupRootDir -Directory -Filter "backup_*" | Sort-Object Name -Descending)
    if ($backupDirs.Count -eq 0) {
        Write-Warn "No backups found in: $BackupRootDir"
        return
    }

    Write-Header "Available Backups ($ScopeName)"
    Write-Host "Found $($backupDirs.Count) backup snapshot(s) in $($BackupRootDir):`n" -ForegroundColor Gray

    for ($i = 0; $i -lt $backupDirs.Count; $i++) {
        $dir = $backupDirs[$i]
        $files = @(Get-ChildItem -Path $dir.FullName -Recurse -File)
        $fileCount = $files.Count
        $timestampStr = $dir.Name -replace '^backup_', ''
        if ($timestampStr -match '^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})$') {
            $formattedDate = "$($Matches[1])-$($Matches[2])-$($Matches[3]) $($Matches[4]):$($Matches[5])"
        }
        else {
            $formattedDate = $timestampStr
        }
        $latestTag = $(if ($i -eq 0) { " [Latest]" } else { "" })
        Write-Host ("  [{0}] {1}  ({2} - {3} file{4}){5}" -f ($i + 1), $dir.Name, $formattedDate, $fileCount, $(if ($fileCount -ne 1) { 's' } else { '' }), $latestTag) -ForegroundColor White
    }
    Write-Host "  [0] Cancel`n" -ForegroundColor White

    $selectedBackup = $null
    if (-not [string]::IsNullOrWhiteSpace($SelectedBackupName)) {
        $selectedBackup = $backupDirs | Where-Object { $_.Name -eq $SelectedBackupName } | Select-Object -First 1
        if (-not $selectedBackup) {
            Write-Host "[ERROR] Backup named '$SelectedBackupName' not found." -ForegroundColor Red
            return
        }
    }
    elseif ($SelectedBackupIndex -gt 0 -and $SelectedBackupIndex -le $backupDirs.Count) {
        $selectedBackup = $backupDirs[$SelectedBackupIndex - 1]
    }
    else {
        $sel = Read-Host "Select backup to restore [1-$($backupDirs.Count)]"
        if ($sel.Trim() -eq "0" -or [string]::IsNullOrWhiteSpace($sel)) {
            Write-Host "Restoration canceled by user." -ForegroundColor Yellow
            return
        }

        $selIndex = 0
        if (-not [int]::TryParse($sel.Trim(), [ref]$selIndex) -or $selIndex -lt 1 -or $selIndex -gt $backupDirs.Count) {
            Write-Host "[ERROR] Invalid selection." -ForegroundColor Red
            return
        }
        $selectedBackup = $backupDirs[$selIndex - 1]
    }

    $manifestFile = Join-Path $selectedBackup.FullName "manifest.json"
    $hasManifest = Test-Path $manifestFile
    $manifestData = $null
    if ($hasManifest) {
        try {
            $manifestData = Get-Content -Path $manifestFile -Raw -Encoding UTF8 | ConvertFrom-Json
        }
        catch {
            $hasManifest = $false
        }
    }

    $restorePlan = @()
    $filesToDelete = @()

    if ($hasManifest -and $manifestData) {
        # 1. Revert modified files
        if ($manifestData.modified) {
            foreach ($item in $manifestData.modified) {
                $src = Join-Path $selectedBackup.FullName $item.backup_subpath
                if (Test-Path $src) {
                    $restorePlan += [PSCustomObject]@{
                        Source       = $src
                        Destination  = $item.target
                        RelativePath = $item.backup_subpath
                    }
                }
            }
        }
        # 2. Delete added files (if they currently exist on disk)
        if ($manifestData.added) {
            foreach ($addedPath in $manifestData.added) {
                if (Test-Path $addedPath) {
                    $filesToDelete += $addedPath
                }
            }
        }
    }
    else {
        # Legacy backup without manifest: restore all files in directory
        $filesToRestore = @(Get-ChildItem -Path $selectedBackup.FullName -Recurse -File | Where-Object { $_.Name -ne "manifest.json" })
        if ($filesToRestore.Count -eq 0) {
            Write-Warn "Selected backup directory is empty: $($selectedBackup.Name)"
            return
        }
        foreach ($file in $filesToRestore) {
            $relPath = $file.FullName.Substring($selectedBackup.FullName.Length).TrimStart('\', '/')
            if ($relPath -eq "GEMINI.md") {
                $destPath = $TargetRuleFile
            }
            elseif ($relPath -like "workflows\*" -or $relPath -like "workflows/*") {
                $subPath = $relPath.Substring(9).TrimStart('\', '/')
                $destPath = Join-Path $TargetWorkflowsDir $subPath
            }
            elseif ($relPath -like "skills\*" -or $relPath -like "skills/*") {
                $subPath = $relPath.Substring(6).TrimStart('\', '/')
                $destPath = Join-Path $TargetSkillsDir $subPath
            }
            else {
                $destPath = Join-Path $TargetBase $relPath
            }

            $restorePlan += [PSCustomObject]@{
                Source       = $file.FullName
                Destination  = $destPath
                RelativePath = $relPath
            }
        }
    }

    if ($restorePlan.Count -eq 0 -and $filesToDelete.Count -eq 0) {
        Write-Info "No actions needed: all target files are already in their pre-install state."
        return
    }

    Write-Header "Rollback Plan ($($selectedBackup.Name))"
    if ($restorePlan.Count -gt 0) {
        Write-Host "Files to restore to previous version ($($restorePlan.Count)):`n" -ForegroundColor Cyan
        foreach ($item in $restorePlan) {
            Write-Host "  * $($item.RelativePath) -> $($item.Destination)" -ForegroundColor Gray
        }
    }
    if ($filesToDelete.Count -gt 0) {
        Write-Host "`nNewly added files to delete / undo ($($filesToDelete.Count)):`n" -ForegroundColor Yellow
        foreach ($delFile in $filesToDelete) {
            Write-Host "  - $delFile" -ForegroundColor Gray
        }
    }

    if (-not $ForceMode -and -not $DryRunMode) {
        Write-Host ""
        $confirm = Read-Host "Proceed with rollback ($($restorePlan.Count) restore, $($filesToDelete.Count) delete)? [y/N]"
        if ($confirm.Trim().ToLower() -notmatch '^(y|yes)$') {
            Write-Host "Restoration canceled by user." -ForegroundColor Yellow
            return
        }
    }

    Write-Header "Applying Rollback"
    foreach ($item in $restorePlan) {
        if ($DryRunMode) {
            Write-Sim "Restore '$($item.Source)' -> '$($item.Destination)'"
        }
        else {
            $destParent = Split-Path $item.Destination -Parent
            if (-not (Test-Path $destParent)) {
                [void](New-Item -ItemType Directory -Path $destParent -Force)
            }
            Copy-Item -Path $item.Source -Destination $item.Destination -Force
            Write-Success "Restored: $($item.RelativePath)"
        }
    }

    foreach ($delFile in $filesToDelete) {
        if ($DryRunMode) {
            Write-Sim "Delete '$delFile'"
        }
        else {
            Remove-Item -Path $delFile -Force
            Write-Success "Deleted newly added: $(Split-Path $delFile -Leaf)"
            $parentDir = Split-Path $delFile -Parent
            if ((Test-Path $parentDir) -and (Get-ChildItem -Path $parentDir -Recurse -File).Count -eq 0) {
                Remove-Item -Path $parentDir -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
    }

    Write-Header "Rollback Completed Successfully!"
    if ($DryRunMode) {
        Write-Host "Simulation completed. No files were modified on disk.`n" -ForegroundColor Magenta
    }
    else {
        Write-Host "Successfully restored $($restorePlan.Count) file(s) and removed $($filesToDelete.Count) newly added file(s) from $ScopeName scope.`n" -ForegroundColor Green
    }
}

# Uninstall handler function
function Invoke-Uninstall {
    param(
        [switch]$GlobalScope,
        [string]$ProjectPath,
        [switch]$DryRunMode,
        [switch]$ForceMode,
        [switch]$NoBackupMode
    )

    $UserHome = Get-UserHomeDirectory
    $isGlobal = $GlobalScope
    $targetProject = $ProjectPath

    if (-not $isGlobal -and [string]::IsNullOrWhiteSpace($targetProject)) {
        Write-Header "Uninstall Scope"
        Write-Host "Choose scope to uninstall:`n"
        Write-Host "  [1] Global  (~/.gemini) - Remove workflows & skills from global user scope" -ForegroundColor White
        Write-Host "  [2] Project (.agents)   - Remove workflows & skills from a specific project" -ForegroundColor White
        Write-Host "  [3] Cancel" -ForegroundColor White
        Write-Host ""

        $scopeChoice = Read-Host "Enter option [1-3]"
        switch ($scopeChoice.Trim()) {
            "1" { $isGlobal = $true }
            "2" {
                $inputProj = Read-Host "Enter project directory path (absolute or relative)"
                if ([string]::IsNullOrWhiteSpace($inputProj)) {
                    Write-Host "[ERROR] Project path cannot be empty." -ForegroundColor Red
                    return
                }
                $targetProject = $inputProj.Trim()
            }
            default {
                Write-Host "Uninstall canceled by user." -ForegroundColor Yellow
                return
            }
        }
    }

    if ($isGlobal) {
        $ScopeName = "Global"
        $TargetBase = Join-Path $UserHome ".gemini"
        $TargetRuleFile = Join-Path $TargetBase "GEMINI.md"
        $TargetWorkflowsDir = Join-Path $TargetBase "config\global_workflows"
        $TargetSkillsDir = Join-Path $TargetBase "config\skills"
        $BackupRootDir = Join-Path $TargetBase "backups"
    }
    else {
        $ScopeName = "Project"
        if (Test-Path $targetProject) {
            $TargetProjectRoot = (Resolve-Path $targetProject).Path
        }
        else {
            $TargetProjectRoot = [System.IO.Path]::GetFullPath($targetProject)
        }
        $TargetBase = Join-Path $TargetProjectRoot ".agents"
        $TargetRuleFile = Join-Path $TargetProjectRoot "GEMINI.md"
        $TargetWorkflowsDir = Join-Path $TargetBase "workflows"
        $TargetSkillsDir = Join-Path $TargetBase "skills"
        $BackupRootDir = Join-Path $TargetBase "backups"
    }

    # Collect files to remove
    $filesToRemove = @()
    if (Test-Path $TargetRuleFile) {
        $filesToRemove += (Get-Item $TargetRuleFile)
    }
    if (Test-Path $TargetWorkflowsDir) {
        $filesToRemove += @(Get-ChildItem -Path $TargetWorkflowsDir -Recurse -File)
    }
    if (Test-Path $TargetSkillsDir) {
        $filesToRemove += @(Get-ChildItem -Path $TargetSkillsDir -Recurse -File)
    }

    if ($filesToRemove.Count -eq 0) {
        Write-Info "No Antigravity workflows or skills found in $ScopeName scope ($TargetBase)."
        return
    }

    Write-Header "Uninstall Resources ($ScopeName)"
    Write-Host "Found $($filesToRemove.Count) installed file(s) in $ScopeName scope:`n" -ForegroundColor Yellow
    foreach ($f in $filesToRemove) {
        Write-Host "  * $($f.FullName)" -ForegroundColor Gray
    }

    # Safety backup before uninstall
    $timestamp = (Get-Date -Format "yyyyMMdd_HHmm")
    $uninstallBackupDir = Join-Path $BackupRootDir "backup_${timestamp}_uninstall"

    if (-not $ForceMode -and -not $DryRunMode) {
        Write-Host ""
        $confirm = Read-Host "Proceed with uninstalling $($filesToRemove.Count) file(s)? [y/N]"
        if ($confirm.Trim().ToLower() -notmatch '^(y|yes)$') {
            Write-Host "Uninstall canceled by user." -ForegroundColor Yellow
            return
        }
    }

    if (-not $NoBackupMode -and -not $DryRunMode) {
        if (-not (Test-Path $uninstallBackupDir)) {
            [void](New-Item -ItemType Directory -Path $uninstallBackupDir -Force)
        }
        Write-Header "Creating Pre-Uninstall Safety Backup"
        foreach ($f in $filesToRemove) {
            $rel = $f.FullName
            if ($rel.StartsWith($TargetBase, [System.StringComparison]::OrdinalIgnoreCase)) {
                $sub = $rel.Substring($TargetBase.Length).TrimStart('\', '/')
            }
            elseif ($rel -eq $TargetRuleFile) {
                $sub = "GEMINI.md"
            }
            else {
                $sub = Split-Path $f.FullName -Leaf
            }
            $bkDest = Join-Path $uninstallBackupDir $sub
            $bkParent = Split-Path $bkDest -Parent
            if (-not (Test-Path $bkParent)) { [void](New-Item -ItemType Directory -Path $bkParent -Force) }
            Copy-Item -Path $f.FullName -Destination $bkDest -Force
        }
        Write-Success "Pre-uninstall safety backup created at: $uninstallBackupDir"
    }

    Write-Header "Removing Resources"
    foreach ($f in $filesToRemove) {
        if ($DryRunMode) {
            Write-Sim "Remove '$($f.FullName)'"
        }
        else {
            Remove-Item -Path $f.FullName -Force
            Write-Success "Removed: $($f.FullName)"
        }
    }

    # Clean up empty directories
    if (-not $DryRunMode) {
        $dirsToCheck = @($TargetWorkflowsDir, $TargetSkillsDir)
        foreach ($d in $dirsToCheck) {
            if ((Test-Path $d) -and (Get-ChildItem -Path $d -Recurse -File).Count -eq 0) {
                Remove-Item -Path $d -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
    }

    Write-Header "Uninstall Completed Successfully!"
    if ($DryRunMode) {
        Write-Host "Simulation completed. No files were removed from disk.`n" -ForegroundColor Magenta
    }
    else {
        Write-Host "Successfully removed $($filesToRemove.Count) file(s) from $ScopeName scope.`n" -ForegroundColor Green
        if (-not $NoBackupMode) {
            Write-Host "[ROLLBACK AVAILABLE] To undo this uninstall at any time, run:" -ForegroundColor Yellow
            Write-Host "  .\install.ps1 -Restore`n" -ForegroundColor Cyan
        }
    }
}

# Interactive menu if no target mode is specified
if (-not $Global -and [string]::IsNullOrWhiteSpace($Project) -and -not $Restore -and -not $Uninstall) {
    Write-Header "Antigravity Agentic Workflows Installer"
    Write-Host "Choose installation mode:`n"
    Write-Host "  [1] Global  (~/.gemini) - Applies to all projects on this machine" -ForegroundColor White
    Write-Host "  [2] Project (.agents)   - Installs into a specific project directory" -ForegroundColor White
    Write-Host "  [3] Restore Backup      - Rollback to a previously saved state" -ForegroundColor White
    Write-Host "  [4] Uninstall           - Remove installed workflows, skills and rules" -ForegroundColor White
    Write-Host "  [5] Exit" -ForegroundColor White
    Write-Host ""

    $choice = Read-Host "Enter option [1-5]"
    switch ($choice.Trim()) {
        "1" { $Global = $true }
        "2" {
            $inputPath = Read-Host "Enter project directory path (absolute or relative)"
            if ([string]::IsNullOrWhiteSpace($inputPath)) {
                Write-Host "[ERROR] Project path cannot be empty." -ForegroundColor Red
                exit 1
            }
            $Project = $inputPath.Trim()
        }
        "3" {
            $Restore = $true
        }
        "4" {
            $Uninstall = $true
        }
        "5" {
            Write-Host "Operation canceled by user." -ForegroundColor Yellow
            exit 0
        }
        default {
            Write-Host "[ERROR] Invalid option. Operation aborted." -ForegroundColor Red
            exit 1
        }
    }
}

# Dispatch directly to restore handler if requested
if ($Restore) {
    Invoke-Restore -GlobalScope:$Global -ProjectPath $Project -DryRunMode:$DryRun -ForceMode:$Force -SelectedBackupName $BackupName -SelectedBackupIndex $BackupIndex
    exit 0
}

# Dispatch directly to uninstall handler if requested
if ($Uninstall) {
    Invoke-Uninstall -GlobalScope:$Global -ProjectPath $Project -DryRunMode:$DryRun -ForceMode:$Force -NoBackupMode:$NoBackup
    exit 0
}

# Target paths
$UserHome = Get-UserHomeDirectory
$Timestamp = (Get-Date -Format "yyyyMMdd_HHmm")
$script:OverwriteAll = $Force

if ($Global) {
    $TargetMode = "Global"
    $TargetBase = Join-Path $UserHome ".gemini"
    $TargetRuleFile = Join-Path $TargetBase "GEMINI.md"
    $TargetWorkflowsDir = Join-Path $TargetBase "config\global_workflows"
    $TargetSkillsDir = Join-Path $TargetBase "config\skills"
    $BackupDir = Join-Path $TargetBase "backups\backup_$Timestamp"
}
else {
    $TargetMode = "Project"
    if (Test-Path $Project) {
        $TargetProjectRoot = (Resolve-Path $Project).Path
    }
    else {
        $TargetProjectRoot = [System.IO.Path]::GetFullPath($Project)
    }
    $TargetBase = Join-Path $TargetProjectRoot ".agents"
    $TargetRuleFile = Join-Path $TargetProjectRoot "GEMINI.md"
    $TargetWorkflowsDir = Join-Path $TargetBase "workflows"
    $TargetSkillsDir = Join-Path $TargetBase "skills"
    $BackupDir = Join-Path $TargetBase "backups\backup_$Timestamp"
}

Write-Header "Installation Setup ($TargetMode)"
Write-Info "Mode:                $TargetMode"
Write-Info "Repository Source:   $RepoRoot"
Write-Info "Rules Target:        $TargetRuleFile"
Write-Info "Workflows Target:    $TargetWorkflowsDir"
Write-Info "Skills Target:       $TargetSkillsDir"
if (-not $NoBackup) {
    Write-Info "Backup Directory:    $BackupDir"
}
if ($DryRun) {
    Write-Host "`n*** DRY-RUN SIMULATION ACTIVE - NO FILES WILL BE MODIFIED ***`n" -ForegroundColor Magenta
}

# Helper to verify identical file content
function Test-FilesIdentical {
    param([string]$FileA, [string]$FileB)
    if (-not (Test-Path $FileA) -or -not (Test-Path $FileB)) { return $false }
    $hashA = (Get-FileHash -Algorithm SHA256 -Path $FileA).Hash
    $hashB = (Get-FileHash -Algorithm SHA256 -Path $FileB).Hash
    return ($hashA -eq $hashB)
}

# Safe single file install function
function Install-SingleFile {
    param(
        [string]$SourceFile,
        [string]$DestFile,
        [string]$RelativeBackupSubpath
    )

    if (-not (Test-Path $SourceFile)) {
        Write-Warn "Source file not found: $SourceFile"
        return
    }

    $destDir = Split-Path $DestFile -Parent
    $fileName = Split-Path $DestFile -Leaf

    if (Test-Path $DestFile) {
        if (Test-FilesIdentical $SourceFile $DestFile) {
            Write-Info "$fileName is already up to date and identical."
            return
        }

        # File exists and differs
        if (-not $DryRun -and -not $script:OverwriteAll) {
            Write-Host "`nFile '$fileName' already exists at target and differs." -ForegroundColor Yellow
            $resp = Read-Host "Overwrite? [Y]es / [N]o / [A]ll / [C]ancel"
            switch ($resp.Trim().ToLower()) {
                "y" { }
                "a" { $script:OverwriteAll = $true }
                "n" { Write-Info "Skipped: $fileName"; return }
                "c" { Write-Host "Installation aborted by user." -ForegroundColor Yellow; exit 0 }
                default { Write-Info "Skipped by default: $fileName"; return }
            }
        }

        # Create backup if enabled
        if (-not $NoBackup) {
            $backupFileDest = Join-Path $BackupDir $RelativeBackupSubpath
            $backupFileDir = Split-Path $backupFileDest -Parent
            if ($DryRun) {
                Write-Sim "Backup '$DestFile' -> '$backupFileDest'"
            }
            else {
                if (-not (Test-Path $backupFileDir)) {
                    [void](New-Item -ItemType Directory -Path $backupFileDir -Force)
                }
                Copy-Item -Path $DestFile -Destination $backupFileDest -Force
                Write-Warn "Backup created: $RelativeBackupSubpath"
            }
        }

        $script:TxModified += [PSCustomObject]@{
            backup_subpath = $RelativeBackupSubpath
            target         = $DestFile
        }
    }
    else {
        $script:TxAdded += $DestFile
    }

    if ($DryRun) {
        Write-Sim "Copy '$SourceFile' -> '$DestFile'"
    }
    else {
        if (-not (Test-Path $destDir)) {
            [void](New-Item -ItemType Directory -Path $destDir -Force)
        }
        Copy-Item -Path $SourceFile -Destination $DestFile -Force
        Write-Success "Installed: $fileName"
    }
}

# 1. Install Rule (GEMINI.md)
Write-Header "1. Installing Base Prompt / Global Rule"
if (Test-Path $SourceGeminiRule) {
    Install-SingleFile -SourceFile $SourceGeminiRule -DestFile $TargetRuleFile -RelativeBackupSubpath "GEMINI.md"
}
else {
    Write-Warn "Source file $SourceGeminiRule not found."
}

# 2. Install Workflows (Legacy backward-compatibility, if present)
if (Test-Path $SourceWorkflows) {
    Write-Header "2. Installing Legacy Workflows (if present)"
    $workflowFiles = Get-ChildItem -Path $SourceWorkflows -Filter "*.md" -File
    foreach ($wf in $workflowFiles) {
        $destWf = Join-Path $TargetWorkflowsDir $wf.Name
        Install-SingleFile -SourceFile $wf.FullName -DestFile $destWf -RelativeBackupSubpath (Join-Path "workflows" $wf.Name)
    }
}

# 3. Install Skills
Write-Header "3. Installing Modular Skills"
$skillDirs = Get-ChildItem -Path $SourceSkills -Directory
foreach ($sDir in $skillDirs) {
    $skillName = $sDir.Name
    $allFiles = Get-ChildItem -Path $sDir.FullName -Recurse -File
    foreach ($file in $allFiles) {
        $subPath = $file.FullName.Substring($sDir.FullName.Length).TrimStart('\', '/')
        $destSkillFile = Join-Path (Join-Path $TargetSkillsDir $skillName) $subPath
        $relBackup = Join-Path (Join-Path "skills" $skillName) $subPath
        Install-SingleFile -SourceFile $file.FullName -DestFile $destSkillFile -RelativeBackupSubpath $relBackup
    }
}

# Save installation transaction manifest
if (-not $DryRun -and -not $NoBackup) {
    if (-not (Test-Path $BackupDir)) {
        [void](New-Item -ItemType Directory -Path $BackupDir -Force)
    }
    $manifestObj = [PSCustomObject]@{
        timestamp   = (Get-Date -Format "yyyy-MM-dd HH:mm")
        mode        = $TargetMode
        target_base = $TargetBase
        modified    = @($script:TxModified)
        added       = @($script:TxAdded)
    }
    $manifestPath = Join-Path $BackupDir "manifest.json"
    $manifestObj | ConvertTo-Json -Depth 5 | Set-Content -Path $manifestPath -Encoding UTF8
}

# Completion
Write-Header "Installation Completed Successfully!"
if ($DryRun) {
    Write-Host "Simulation completed. No files were modified on disk.`n" -ForegroundColor Magenta
}
else {
    Write-Host "All resources synchronized successfully." -ForegroundColor Green
    if (Test-Path $BackupDir) {
        Write-Host "`n[BACKUP] Replaced files and transaction snapshot saved to:" -ForegroundColor Yellow
        Write-Host "  $BackupDir`n" -ForegroundColor Cyan
    }
    Write-Host "To get started in Antigravity:" -ForegroundColor White
    Write-Host "  1. Open or reload your session in the Antigravity IDE." -ForegroundColor Gray
    Write-Host "  2. Type /ask or /plan in chat to verify available slash commands.`n" -ForegroundColor Gray
}