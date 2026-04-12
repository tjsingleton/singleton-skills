skills_dir := justfile_directory() / "skills"
claude_skills := env("HOME") / ".claude" / "skills"
root := justfile_directory()

# Show all skills and install status
list:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "Skills:"
    for dir in "{{skills_dir}}"/*/; do
        name=$(basename "$dir")
        if [ -L "{{claude_skills}}/$name" ]; then
            echo "  ✓ $name (symlinked)"
        else
            echo "  ✗ $name (not installed)"
        fi
    done

# Symlink all skills to ~/.claude/skills/ + print plugin install instructions
install:
    #!/usr/bin/env bash
    set -euo pipefail
    mkdir -p "{{claude_skills}}"
    for dir in "{{skills_dir}}"/*/; do
        name=$(basename "$dir")
        target="{{claude_skills}}/$name"
        [ -L "$target" ] && rm "$target"
        ln -sf "$dir" "$target"
        echo "Linked: $name → $target"
    done
    echo ""
    echo "To register as a Claude Code plugin, run inside a Claude Code session:"
    echo "  /plugin marketplace add {{root}}"
    echo "  /plugin install singleton-skills@singleton-skills-dev"

# Remove all skill symlinks from ~/.claude/skills/
uninstall:
    #!/usr/bin/env bash
    set -euo pipefail
    for dir in "{{skills_dir}}"/*/; do
        name=$(basename "$dir")
        target="{{claude_skills}}/$name"
        if [ -L "$target" ]; then
            rm "$target"
            echo "Removed: $name"
        fi
    done

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
