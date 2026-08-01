skills_dir := justfile_directory() / "skills"
root := justfile_directory()

# Show support, installation, and checkout ownership independently
list target="shared" shared_dir="" claude_dir="":
    #!/usr/bin/env bash
    set -euo pipefail
    target_value="{{target}}"
    shared_value="{{shared_dir}}"
    claude_value="{{claude_dir}}"
    target_value="${target_value#target=}"
    shared_value="${shared_value#shared_dir=}"
    claude_value="${claude_value#claude_dir=}"
    args=(list --target "$target_value")
    [[ -n "$shared_value" ]] && args+=(--shared-dir "$shared_value")
    [[ -n "$claude_value" ]] && args+=(--claude-dir "$claude_value")
    python3 "{{root}}/scripts/skill_installer.py" "${args[@]}"

# Install the supported set by default; use set=all and/or target=claude|all explicitly
install set="default" target="shared" shared_dir="" claude_dir="":
    #!/usr/bin/env bash
    set -euo pipefail
    set_value="{{set}}"
    target_value="{{target}}"
    shared_value="{{shared_dir}}"
    claude_value="{{claude_dir}}"
    set_value="${set_value#set=}"
    target_value="${target_value#target=}"
    shared_value="${shared_value#shared_dir=}"
    claude_value="${claude_value#claude_dir=}"
    args=(install --set "$set_value" --target "$target_value")
    [[ -n "$shared_value" ]] && args+=(--shared-dir "$shared_value")
    [[ -n "$claude_value" ]] && args+=(--claude-dir "$claude_value")
    python3 "{{root}}/scripts/skill_installer.py" "${args[@]}"

# Remove only links proven to be owned by this checkout
uninstall set="default" target="shared" shared_dir="" claude_dir="":
    #!/usr/bin/env bash
    set -euo pipefail
    set_value="{{set}}"
    target_value="{{target}}"
    shared_value="{{shared_dir}}"
    claude_value="{{claude_dir}}"
    set_value="${set_value#set=}"
    target_value="${target_value#target=}"
    shared_value="${shared_value#shared_dir=}"
    claude_value="${claude_value#claude_dir=}"
    args=(uninstall --set "$set_value" --target "$target_value")
    [[ -n "$shared_value" ]] && args+=(--shared-dir "$shared_value")
    [[ -n "$claude_value" ]] && args+=(--claude-dir "$claude_value")
    python3 "{{root}}/scripts/skill_installer.py" "${args[@]}"

# Scaffold a new skill: just new name=my-skill
new name:
    #!/usr/bin/env bash
    set -euo pipefail
    skill_dir="{{skills_dir}}/{{name}}"
    if [ -d "$skill_dir" ]; then
        echo "Error: skill '{{name}}' already exists at $skill_dir"
        exit 1
    fi
    mkdir -p "$skill_dir/scripts" "$skill_dir/evals"
    python3 "{{root}}/scripts/new_skill.py" "{{name}}" "$skill_dir"
    echo ""
    echo "Next: edit skills/{{name}}/SKILL.md"
    echo "Then: just install  (to symlink)"

# Register: write SINGLETON_SKILLS_PATH to shell profile
register:
    #!/usr/bin/env bash
    set -euo pipefail
    profile="${HOME}/.zprofile"
    line="export SINGLETON_SKILLS_PATH=\"{{root}}\""
    if grep -q "SINGLETON_SKILLS_PATH" "$profile" 2>/dev/null; then
        echo "SINGLETON_SKILLS_PATH already set in $profile"
    else
        echo "$line" >> "$profile"
        echo "Added to $profile"
    fi
    echo ""
    echo "Reload: source $profile"
    echo ""
    echo "To register as a Claude Code plugin, run inside a Claude Code session:"
    echo "  /plugin marketplace add {{root}}"
    echo "  /plugin install singleton-skills@singleton-skills-dev"

# Bump version in manifests: just bump ver=1.2.0
bump ver:
    #!/usr/bin/env bash
    set -euo pipefail
    sed -i '' "s/\"version\": \".*\"/\"version\": \"{{ver}}\"/" "{{root}}/.claude-plugin/plugin.json"
    sed -i '' "s/\"version\": \".*\"/\"version\": \"{{ver}}\"/" "{{root}}/.claude-plugin/marketplace.json"
    echo "Bumped to {{ver}}"
