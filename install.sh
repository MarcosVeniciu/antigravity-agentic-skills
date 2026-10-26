#!/usr/bin/env bash
# ==============================================================================
# Antigravity Agentic Workflows - Cross-Platform Installer (Linux / macOS / WSL)
# ==============================================================================
# Copies prompts, workflows, and skills into the global scope (~/.gemini) or a
# specific project directory (.agents/).
# Includes safeguards with timestamped backups (YYYYMMDD_HHMM).
# ==============================================================================

set -e

# ANSI Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Base repository locations
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_PROMPTS="$REPO_ROOT/prompts"
SOURCE_WORKFLOWS="$REPO_ROOT/workflows"
SOURCE_SKILLS="$REPO_ROOT/skills"
SOURCE_GEMINI_RULE="$SOURCE_PROMPTS/gemini.md"

# Transaction trackers for installation manifest
TX_MODIFIED_BACKUP=()
TX_MODIFIED_TARGET=()
TX_ADDED=()

print_header() {
    echo ""
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}============================================================${NC}"
}

print_success() { echo -e "  ${GREEN}[OK]${NC} $1"; }
print_info()    { echo -e "  ${GRAY}[INFO]${NC} $1"; }
print_warn()    { echo -e "  ${YELLOW}[WARN]${NC} $1"; }
print_sim()     { echo -e "  ${MAGENTA}[SIMULATION]${NC} $1"; }

show_help() {
    echo "Usage: ./install.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -g, --global           Install into global user scope (~/.gemini)"
    echo "  -p, --project <path>   Install into a specific project directory (.agents/)"
    echo "  -r, --restore          Restore files from a previous backup snapshot"
    echo "  -u, --uninstall        Safely remove installed workflows, skills, and rules"
    echo "      --backup-index <n> Non-interactive index of backup to restore"
    echo "      --backup-name <s>  Non-interactive name of backup directory to restore"
    echo "  -f, --force            Overwrite existing files without interactive confirmation"
    echo "      --no-backup        Disable creating timestamped backup directory"
    echo "      --dry-run          Simulate installation without modifying files on disk"
    echo "  -h, --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./install.sh --global"
    echo "  ./install.sh -p /path/to/my-project"
    echo "  ./install.sh --restore"
    echo "  ./install.sh --uninstall"
    echo "  ./install.sh -g --dry-run"
    exit 0
}

# Parse parameters
MODE=""
PROJECT_PATH=""
FORCE=false
NO_BACKUP=false
DRY_RUN=false
OVERWRITE_ALL=false
RESTORE=false
UNINSTALL=false
BACKUP_INDEX=0
BACKUP_NAME=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -g|--global)
            MODE="global"
            shift
            ;;
        -p|--project)
            MODE="project"
            PROJECT_PATH="$2"
            shift 2
            ;;
        -r|--restore)
            RESTORE=true
            shift
            ;;
        -u|--uninstall)
            UNINSTALL=true
            shift
            ;;
        --backup-index)
            BACKUP_INDEX="$2"
            shift 2
            ;;
        --backup-name)
            BACKUP_NAME="$2"
            shift 2
            ;;
        -f|--force)
            FORCE=true
            OVERWRITE_ALL=true
            shift
            ;;
        --no-backup)
            NO_BACKUP=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            show_help
            ;;
        *)
            echo -e "${RED}[ERROR] Unknown option: $1${NC}"
            show_help
            ;;
    esac
done

# Validate sources (only mandatory when performing installation)
if [ "$RESTORE" = false ] && [ "$UNINSTALL" = false ]; then
    if [ ! -d "$SOURCE_SKILLS" ]; then
        echo -e "${RED}[ERROR] 'skills' directory not found in: $REPO_ROOT${NC}"
        echo -e "${YELLOW}Make sure you are running the script from the root of the cloned/extracted repository.${NC}"
        exit 1
    fi
fi

# Restore handler function
restore_backup() {
    local is_global=false
    local target_project="$PROJECT_PATH"

    if [ "$MODE" = "global" ]; then
        is_global=true
    elif [ "$MODE" = "project" ]; then
        is_global=false
    else
        print_header "Restore Backup Scope"
        echo "Choose backup scope to restore:"
        echo ""
        echo -e "  [1] Global  (~/.gemini/backups) - Backups from global installations"
        echo -e "  [2] Project (.agents/backups)   - Backups from project installations"
        echo -e "  [3] Cancel"
        echo ""
        read -rp "Enter option [1-3]: " scope_choice
        case "$scope_choice" in
            1) is_global=true ;;
            2)
                read -rp "Enter project directory path: " input_proj
                if [ -z "$input_proj" ]; then
                    echo -e "${RED}[ERROR] Project path cannot be empty.${NC}"
                    return 1
                fi
                target_project="$input_proj"
                ;;
            *)
                echo -e "${YELLOW}Restoration canceled by user.${NC}"
                return 0
                ;;
        esac
    fi

    local target_base target_rule_file target_workflows_dir target_skills_dir backup_root_dir scope_name
    if [ "$is_global" = true ]; then
        scope_name="Global"
        target_base="$HOME/.gemini"
        backup_root_dir="$target_base/backups"
        target_rule_file="$target_base/GEMINI.md"
        target_workflows_dir="$target_base/config/global_workflows"
        target_skills_dir="$target_base/config/skills"
    else
        scope_name="Project"
        mkdir -p "$target_project"
        local target_proj_root
        target_proj_root="$(cd "$target_project" && pwd)"
        target_base="$target_proj_root/.agents"
        backup_root_dir="$target_base/backups"
        target_rule_file="$target_proj_root/GEMINI.md"
        target_workflows_dir="$target_base/workflows"
        target_skills_dir="$target_base/skills"
    fi

    if [ ! -d "$backup_root_dir" ]; then
        print_warn "Backup directory not found: $backup_root_dir"
        return 0
    fi

    # Find backup directories sorted reverse (newest first)
    local backup_dirs=()
    while IFS= read -r dir; do
        [ -n "$dir" ] && backup_dirs+=("$dir")
    done < <(find "$backup_root_dir" -maxdepth 1 -mindepth 1 -type d -name "backup_*" 2>/dev/null | sort -r)

    local total_backups="${#backup_dirs[@]}"
    if [ "$total_backups" -eq 0 ]; then
        print_warn "No backups found in: $backup_root_dir"
        return 0
    fi

    print_header "Available Backups ($scope_name)"
    echo -e "${GRAY}Found $total_backups backup snapshot(s) in $backup_root_dir:${NC}\n"

    for i in "${!backup_dirs[@]}"; do
        local bdir="${backup_dirs[$i]}"
        local bname
        bname="$(basename "$bdir")"
        local file_count
        file_count="$(find "$bdir" -type f | wc -l | tr -d ' ')"
        local timestamp_str="${bname#backup_}"
        local formatted_date="$timestamp_str"
        if [[ "$timestamp_str" =~ ^([0-9]{4})([0-9]{2})([0-9]{2})_([0-9]{2})([0-9]{2})$ ]]; then
            formatted_date="${BASH_REMATCH[1]}-${BASH_REMATCH[2]}-${BASH_REMATCH[3]} ${BASH_REMATCH[4]}:${BASH_REMATCH[5]}"
        fi
        local latest_tag=""
        if [ "$i" -eq 0 ]; then
            latest_tag=" [Latest]"
        fi
        local plural="s"
        [ "$file_count" -eq 1 ] && plural=""
        echo -e "  [$((i + 1))] $bname  ($formatted_date - $file_count file$plural)$latest_tag"
    done
    echo -e "  [0] Cancel\n"

    local selected_bdir=""
    if [ -n "$BACKUP_NAME" ]; then
        for bdir in "${backup_dirs[@]}"; do
            if [ "$(basename "$bdir")" = "$BACKUP_NAME" ]; then
                selected_bdir="$bdir"
                break
            fi
        done
        if [ -z "$selected_bdir" ]; then
            echo -e "${RED}[ERROR] Backup named '$BACKUP_NAME' not found.${NC}"
            return 1
        fi
    elif [ "$BACKUP_INDEX" -gt 0 ] 2>/dev/null && [ "$BACKUP_INDEX" -le "$total_backups" ]; then
        selected_bdir="${backup_dirs[$((BACKUP_INDEX - 1))]}"
    else
        read -rp "Select backup to restore [1-$total_backups]: " sel
        if [ -z "$sel" ] || [ "$sel" = "0" ]; then
            echo -e "${YELLOW}Restoration canceled by user.${NC}"
            return 0
        fi

        if ! [[ "$sel" =~ ^[0-9]+$ ]] || [ "$sel" -lt 1 ] || [ "$sel" -gt "$total_backups" ]; then
            echo -e "${RED}[ERROR] Invalid selection.${NC}"
            return 1
        fi
        selected_bdir="${backup_dirs[$((sel - 1))]}"
    fi

    local selected_bname
    selected_bname="$(basename "$selected_bdir")"

    local manifest_file="$selected_bdir/manifest.json"
    local has_manifest=false
    if [ -f "$manifest_file" ] && command -v python >/dev/null 2>&1; then
        has_manifest=true
    fi

    local restore_srcs=()
    local restore_dests=()
    local restore_rels=()
    local files_to_delete=()

    if [ "$has_manifest" = true ]; then
        while IFS=$'\t' read -r action arg1 arg2; do
            if [ "$action" = "MOD" ] && [ -n "$arg1" ]; then
                local src="$selected_bdir/$arg1"
                if [ -f "$src" ]; then
                    restore_srcs+=("$src")
                    restore_dests+=("$arg2")
                    restore_rels+=("$arg1")
                fi
            elif [ "$action" = "ADD" ] && [ -n "$arg1" ]; then
                if [ -f "$arg1" ]; then
                    files_to_delete+=("$arg1")
                fi
            fi
        done < <(python -c "
import json, sys
try:
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        data = json.load(f)
    for m in data.get('modified', []):
        print(f'MOD\t{m.get(\"backup_subpath\", \"\")}\t{m.get(\"target\", \"\")}')
    for a in data.get('added', []):
        print(f'ADD\t{a}')
except Exception:
    pass
" "$manifest_file")
    else
        # Legacy backup without manifest: restore all files in directory
        local files_to_restore=()
        while IFS= read -r -d '' f; do
            [ "$(basename "$f")" != "manifest.json" ] && files_to_restore+=("$f")
        done < <(find "$selected_bdir" -type f -print0)

        if [ "${#files_to_restore[@]}" -eq 0 ]; then
            print_warn "Selected backup directory is empty: $selected_bname"
            return 0
        fi

        for f in "${files_to_restore[@]}"; do
            local rel_path="${f#"$selected_bdir"/}"
            local dest_path=""
            if [ "$rel_path" = "GEMINI.md" ]; then
                dest_path="$target_rule_file"
            elif [[ "$rel_path" == workflows/* ]]; then
                local sub_path="${rel_path#workflows/}"
                dest_path="$target_workflows_dir/$sub_path"
            elif [[ "$rel_path" == skills/* ]]; then
                local sub_path="${rel_path#skills/}"
                dest_path="$target_skills_dir/$sub_path"
            else
                dest_path="$target_base/$rel_path"
            fi
            restore_srcs+=("$f")
            restore_dests+=("$dest_path")
            restore_rels+=("$rel_path")
        done
    fi

    if [ "${#restore_srcs[@]}" -eq 0 ] && [ "${#files_to_delete[@]}" -eq 0 ]; then
        print_info "No actions needed: all target files are already in their pre-install state."
        return 0
    fi

    print_header "Rollback Plan ($selected_bname)"
    if [ "${#restore_srcs[@]}" -gt 0 ]; then
        echo -e "${CYAN}Files to restore to previous version (${#restore_srcs[@]}):${NC}\n"
        for i in "${!restore_srcs[@]}"; do
            echo -e "  ${GRAY}* ${restore_rels[$i]} -> ${restore_dests[$i]}${NC}"
        done
    fi
    if [ "${#files_to_delete[@]}" -gt 0 ]; then
        echo -e "\n${YELLOW}Newly added files to delete / undo (${#files_to_delete[@]}):${NC}\n"
        for del_file in "${files_to_delete[@]}"; do
            echo -e "  ${GRAY}- $del_file${NC}"
        done
    fi

    if [ "$FORCE" = false ] && [ "$DRY_RUN" = false ]; then
        echo ""
        read -rp "Proceed with rollback (${#restore_srcs[@]} restore, ${#files_to_delete[@]} delete)? [y/N]: " confirm
        case "$confirm" in
            [yY]*) ;;
            *) echo -e "${YELLOW}Restoration canceled by user.${NC}"; return 0 ;;
        esac
    fi

    print_header "Applying Rollback"
    for i in "${!restore_srcs[@]}"; do
        local src="${restore_srcs[$i]}"
        local dest="${restore_dests[$i]}"
        local rel="${restore_rels[$i]}"

        if [ "$DRY_RUN" = true ]; then
            print_sim "Restore '$src' -> '$dest'"
        else
            mkdir -p "$(dirname "$dest")"
            cp "$src" "$dest"
            print_success "Restored: $rel"
        fi
    done

    for del_file in "${files_to_delete[@]}"; do
        if [ "$DRY_RUN" = true ]; then
            print_sim "Delete '$del_file'"
        else
            rm -f "$del_file"
            print_success "Deleted newly added: $(basename "$del_file")"
            local parent_dir
            parent_dir="$(dirname "$del_file")"
            [ -d "$parent_dir" ] && find "$parent_dir" -type d -empty -delete 2>/dev/null || true
        fi
    done

    print_header "Rollback Completed Successfully!"
    if [ "$DRY_RUN" = true ]; then
        echo -e "${MAGENTA}Simulation completed. No files were modified on disk.${NC}\n"
    else
        echo -e "${GREEN}Successfully restored ${#restore_srcs[@]} file(s) and removed ${#files_to_delete[@]} newly added file(s) from $scope_name scope.${NC}\n"
    fi
}

# Uninstall handler function
uninstall_workflows() {
    local is_global=false
    local target_project="$PROJECT_PATH"

    if [ "$MODE" = "global" ]; then
        is_global=true
    elif [ "$MODE" = "project" ]; then
        is_global=false
    else
        print_header "Uninstall Scope"
        echo "Choose scope to uninstall:"
        echo ""
        echo -e "  [1] Global  (~/.gemini) - Remove workflows & skills from global user scope"
        echo -e "  [2] Project (.agents)   - Remove workflows & skills from a specific project"
        echo -e "  [3] Cancel"
        echo ""
        read -rp "Enter option [1-3]: " scope_choice
        case "$scope_choice" in
            1) is_global=true ;;
            2)
                read -rp "Enter project directory path: " input_proj
                if [ -z "$input_proj" ]; then
                    echo -e "${RED}[ERROR] Project path cannot be empty.${NC}"
                    return 1
                fi
                target_project="$input_proj"
                ;;
            *)
                echo -e "${YELLOW}Uninstall canceled by user.${NC}"
                return 0
                ;;
        esac
    fi

    local target_base target_rule_file target_workflows_dir target_skills_dir backup_root_dir scope_name
    if [ "$is_global" = true ]; then
        scope_name="Global"
        target_base="$HOME/.gemini"
        target_rule_file="$target_base/GEMINI.md"
        target_workflows_dir="$target_base/config/global_workflows"
        target_skills_dir="$target_base/config/skills"
        backup_root_dir="$target_base/backups"
    else
        scope_name="Project"
        mkdir -p "$target_project"
        local target_proj_root
        target_proj_root="$(cd "$target_project" && pwd)"
        target_base="$target_proj_root/.agents"
        target_rule_file="$target_proj_root/GEMINI.md"
        target_workflows_dir="$target_base/workflows"
        target_skills_dir="$target_base/skills"
        backup_root_dir="$target_base/backups"
    fi

    local files_to_remove=()
    [ -f "$target_rule_file" ] && files_to_remove+=("$target_rule_file")
    if [ -d "$target_workflows_dir" ]; then
        while IFS= read -r -d '' f; do
            files_to_remove+=("$f")
        done < <(find "$target_workflows_dir" -type f -print0)
    fi
    if [ -d "$target_skills_dir" ]; then
        while IFS= read -r -d '' f; do
            files_to_remove+=("$f")
        done < <(find "$target_skills_dir" -type f -print0)
    fi

    if [ "${#files_to_remove[@]}" -eq 0 ]; then
        print_info "No Antigravity workflows or skills found in $scope_name scope ($target_base)."
        return 0
    fi

    print_header "Uninstall Resources ($scope_name)"
    echo -e "${YELLOW}Found ${#files_to_remove[@]} installed file(s) in $scope_name scope:${NC}\n"
    for f in "${files_to_remove[@]}"; do
        echo -e "  ${GRAY}* $f${NC}"
    done

    local uninstall_ts
    uninstall_ts="$(date +"%Y%m%d_%H%M")"
    local uninstall_backup_dir="$backup_root_dir/backup_${uninstall_ts}_uninstall"

    if [ "$FORCE" = false ] && [ "$DRY_RUN" = false ]; then
        echo ""
        read -rp "Proceed with uninstalling ${#files_to_remove[@]} file(s)? [y/N]: " confirm
        case "$confirm" in
            [yY]*) ;;
            *) echo -e "${YELLOW}Uninstall canceled by user.${NC}"; return 0 ;;
        esac
    fi

    if [ "$NO_BACKUP" = false ] && [ "$DRY_RUN" = false ]; then
        mkdir -p "$uninstall_backup_dir"
        print_header "Creating Pre-Uninstall Safety Backup"
        for f in "${files_to_remove[@]}"; do
            local sub=""
            if [[ "$f" == "$target_base"* ]]; then
                sub="${f#"$target_base"/}"
            elif [ "$f" = "$target_rule_file" ]; then
                sub="GEMINI.md"
            else
                sub="$(basename "$f")"
            fi
            local bk_dest="$uninstall_backup_dir/$sub"
            mkdir -p "$(dirname "$bk_dest")"
            cp "$f" "$bk_dest"
        done
        print_success "Pre-uninstall safety backup created at: $uninstall_backup_dir"
    fi

    print_header "Removing Resources"
    for f in "${files_to_remove[@]}"; do
        if [ "$DRY_RUN" = true ]; then
            print_sim "Remove '$f'"
        else
            rm -f "$f"
            print_success "Removed: $f"
        fi
    done

    # Clean empty directories
    if [ "$DRY_RUN" = false ]; then
        [ -d "$target_workflows_dir" ] && find "$target_workflows_dir" -type d -empty -delete 2>/dev/null || true
        [ -d "$target_skills_dir" ] && find "$target_skills_dir" -type d -empty -delete 2>/dev/null || true
    fi

    print_header "Uninstall Completed Successfully!"
    if [ "$DRY_RUN" = true ]; then
        echo -e "${MAGENTA}Simulation completed. No files were removed from disk.${NC}\n"
    else
        echo -e "${GREEN}Successfully removed ${#files_to_remove[@]} file(s) from $scope_name scope.${NC}\n"
        if [ "$NO_BACKUP" = false ]; then
            echo -e "${YELLOW}[ROLLBACK AVAILABLE] To undo this uninstall at any time, run:${NC}"
            echo -e "  ${CYAN}./install.sh --restore${NC}\n"
        fi
    fi
}

# Interactive menu if no mode was provided and restore/uninstall not directly invoked
if [ -z "$MODE" ] && [ "$RESTORE" = false ] && [ "$UNINSTALL" = false ]; then
    print_header "Antigravity Agentic Workflows Installer"
    echo "Choose installation mode:"
    echo ""
    echo -e "  [1] Global  (~/.gemini) - Applies to all projects on this machine"
    echo -e "  [2] Project (.agents)   - Installs into a specific project directory"
    echo -e "  [3] Restore Backup      - Rollback to a previously saved state"
    echo -e "  [4] Uninstall           - Remove installed workflows, skills and rules"
    echo -e "  [5] Exit"
    echo ""
    read -rp "Enter option [1-5]: " choice
    case "$choice" in
        1)
            MODE="global"
            ;;
        2)
            read -rp "Enter project directory path: " input_proj
            if [ -z "$input_proj" ]; then
                echo -e "${RED}[ERROR] Project path cannot be empty.${NC}"
                exit 1
            fi
            MODE="project"
            PROJECT_PATH="$input_proj"
            ;;
        3)
            RESTORE=true
            ;;
        4)
            UNINSTALL=true
            ;;
        5)
            echo -e "${YELLOW}Operation canceled by user.${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}[ERROR] Invalid option. Operation aborted.${NC}"
            exit 1
            ;;
    esac
fi

# Dispatch directly to restore handler if requested
if [ "$RESTORE" = true ]; then
    restore_backup
    exit 0
fi

# Dispatch directly to uninstall handler if requested
if [ "$UNINSTALL" = true ]; then
    uninstall_workflows
    exit 0
fi

TIMESTAMP="$(date +"%Y%m%d_%H%M")"

if [ "$MODE" = "global" ]; then
    TARGET_MODE="Global"
    TARGET_BASE="$HOME/.gemini"
    TARGET_RULE_FILE="$TARGET_BASE/GEMINI.md"
    TARGET_WORKFLOWS_DIR="$TARGET_BASE/config/global_workflows"
    TARGET_SKILLS_DIR="$TARGET_BASE/config/skills"
    BACKUP_DIR="$TARGET_BASE/backups/backup_$TIMESTAMP"
else
    TARGET_MODE="Project"
    mkdir -p "$PROJECT_PATH"
    TARGET_PROJECT_ROOT="$(cd "$PROJECT_PATH" && pwd)"
    TARGET_BASE="$TARGET_PROJECT_ROOT/.agents"
    TARGET_RULE_FILE="$TARGET_PROJECT_ROOT/GEMINI.md"
    TARGET_WORKFLOWS_DIR="$TARGET_BASE/workflows"
    TARGET_SKILLS_DIR="$TARGET_BASE/skills"
    BACKUP_DIR="$TARGET_BASE/backups/backup_$TIMESTAMP"
fi

print_header "Installation Setup ($TARGET_MODE)"
print_info "Mode:                $TARGET_MODE"
print_info "Repository Source:   $REPO_ROOT"
print_info "Rules Target:        $TARGET_RULE_FILE"
print_info "Workflows Target:    $TARGET_WORKFLOWS_DIR"
print_info "Skills Target:       $TARGET_SKILLS_DIR"
if [ "$NO_BACKUP" = false ]; then
    print_info "Backup Directory:    $BACKUP_DIR"
fi
if [ "$DRY_RUN" = true ]; then
    echo -e "\n${MAGENTA}*** DRY-RUN SIMULATION ACTIVE - NO FILES WILL BE MODIFIED ***${NC}\n"
fi

# Safe single file install function
install_single_file() {
    local src="$1"
    local dest="$2"
    local rel_backup="$3"

    if [ ! -f "$src" ]; then
        print_warn "Source file not found: $src"
        return
    fi

    local dest_dir
    dest_dir="$(dirname "$dest")"
    local file_name
    file_name="$(basename "$dest")"

    if [ -f "$dest" ]; then
        # Check if identical
        if cmp -s "$src" "$dest"; then
            print_info "$file_name is already up to date and identical."
            return
        fi

        # File exists and differs
        if [ "$DRY_RUN" = false ] && [ "$OVERWRITE_ALL" = false ]; then
            echo ""
            echo -e "${YELLOW}File '$file_name' already exists at target and differs.${NC}"
            read -rp "Overwrite? [y]es / [n]o / [a]ll / [c]ancel: " resp
            case "$resp" in
                [yY]*) ;;
                [aA]*) OVERWRITE_ALL=true ;;
                [nN]*) print_info "Skipped: $file_name"; return ;;
                [cC]*) echo -e "${YELLOW}Installation aborted by user.${NC}"; exit 0 ;;
                *) print_info "Skipped by default: $file_name"; return ;;
            esac
        fi

        # Backup
        if [ "$NO_BACKUP" = false ]; then
            local backup_file_dest="$BACKUP_DIR/$rel_backup"
            local backup_file_dir
            backup_file_dir="$(dirname "$backup_file_dest")"
            if [ "$DRY_RUN" = true ]; then
                print_sim "Backup '$dest' -> '$backup_file_dest'"
            else
                mkdir -p "$backup_file_dir"
                cp "$dest" "$backup_file_dest"
                print_warn "Backup created: $rel_backup"
            fi
        fi

        TX_MODIFIED_BACKUP+=("$rel_backup")
        TX_MODIFIED_TARGET+=("$dest")
    else
        TX_ADDED+=("$dest")
    fi

    if [ "$DRY_RUN" = true ]; then
        print_sim "Copy '$src' -> '$dest'"
    else
        mkdir -p "$dest_dir"
        cp "$src" "$dest"
        print_success "Installed: $file_name"
    fi
}

# 1. Install Rule (GEMINI.md)
print_header "1. Installing Base Prompt / Global Rule"
if [ -f "$SOURCE_GEMINI_RULE" ]; then
    install_single_file "$SOURCE_GEMINI_RULE" "$TARGET_RULE_FILE" "GEMINI.md"
else
    print_warn "Source file $SOURCE_GEMINI_RULE not found."
fi

# 2. Install Workflows (Legacy backward-compatibility, if present)
if [ -d "$SOURCE_WORKFLOWS" ]; then
    print_header "2. Installing Legacy Workflows (if present)"
    for wf in "$SOURCE_WORKFLOWS"/*.md; do
        if [ -f "$wf" ]; then
            wf_name="$(basename "$wf")"
            install_single_file "$wf" "$TARGET_WORKFLOWS_DIR/$wf_name" "workflows/$wf_name"
        fi
    done
fi

# 3. Install Skills
print_header "3. Installing Modular Skills"
for skill_dir in "$SOURCE_SKILLS"/*; do
    if [ -d "$skill_dir" ]; then
        skill_name="$(basename "$skill_dir")"
        while IFS= read -r -d '' file; do
            rel_file="${file#"$skill_dir"/}"
            dest_file="$TARGET_SKILLS_DIR/$skill_name/$rel_file"
            rel_backup="skills/$skill_name/$rel_file"
            install_single_file "$file" "$dest_file" "$rel_backup"
        done < <(find "$skill_dir" -type f -print0)
    fi
done

# Save installation transaction manifest
if [ "$DRY_RUN" = false ] && [ "$NO_BACKUP" = false ]; then
    mkdir -p "$BACKUP_DIR"
    manifest_path="$BACKUP_DIR/manifest.json"
    cat <<EOF > "$manifest_path"
{
  "timestamp": "$(date +"%Y-%m-%d %H:%M")",
  "mode": "$TARGET_MODE",
  "target_base": "$TARGET_BASE",
  "modified": [
EOF
    first=true
    for i in "${!TX_MODIFIED_BACKUP[@]}"; do
        [ "$first" = false ] && echo "," >> "$manifest_path"
        printf '    { "backup_subpath": "%s", "target": "%s" }' "${TX_MODIFIED_BACKUP[$i]}" "${TX_MODIFIED_TARGET[$i]}" >> "$manifest_path"
        first=false
    done
    echo -e "\n  ],\n  \"added\": [" >> "$manifest_path"
    first=true
    for item in "${TX_ADDED[@]}"; do
        [ "$first" = false ] && echo "," >> "$manifest_path"
        printf '    "%s"' "$item" >> "$manifest_path"
        first=false
    done
    echo -e "\n  ]\n}" >> "$manifest_path"
fi

# Completion
print_header "Installation Completed Successfully!"
if [ "$DRY_RUN" = true ]; then
    echo -e "${MAGENTA}Simulation completed. No files were modified on disk.${NC}\n"
else
    echo -e "${GREEN}All resources synchronized successfully.${NC}"
    if [ -d "$BACKUP_DIR" ]; then
        echo -e "\n${YELLOW}[BACKUP] Replaced files and transaction snapshot saved to:${NC}"
        echo -e "  ${CYAN}$BACKUP_DIR${NC}\n"
    fi
    echo -e "To get started in Antigravity:"
    echo -e "${GRAY}  1. Open or reload your session in the Antigravity IDE.${NC}"
    echo -e "${GRAY}  2. Type /ask or /plan in chat to verify available slash commands.${NC}\n"
fi
