skills_dir := justfile_directory() / "skills"
root := justfile_directory()

# Run all repository tests, portable-core conformance checks, and Python syntax checks
check:
    #!/usr/bin/env bash
    set -euo pipefail
    python3 -m unittest discover -s "{{root}}/tests" -p 'test_*.py'
    python3 -m unittest discover -s "{{root}}/skills/git-triage/evals" -p 'test_*.py'
    python3 -m compileall -q \
        "{{root}}/scripts" \
        "{{root}}/tests" \
        "{{root}}/skills/git-triage/evals" \
        "{{root}}/skills/imessage-search/scripts"

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

# Print shell-neutral registration commands without changing host configuration
register:
    @printf '%s\n' 'export SINGLETON_SKILLS_PATH="{{root}}"'
    @printf '%s\n' '/plugin marketplace add {{root}}'
    @printf '%s\n' '/plugin install singleton-skills@singleton-skills'
    @printf '%s\n' 'codex plugin marketplace add {{root}}'
    @printf '%s\n' 'codex plugin add singleton-skills@singleton-skills'
    @printf '%s\n' 'cursor-agent plugin marketplace add https://github.com/tjsingleton/singleton-skills'
    @printf '%s\n' 'cursor-agent --plugin-dir {{root}}'

# Propose learnings for a skill from its CHANGELOG.md [Unreleased] section: just propose-learnings my-skill
propose-learnings name:
    #!/usr/bin/env bash
    set -euo pipefail
    changelog="{{skills_dir}}/{{name}}/CHANGELOG.md"
    if [ ! -f "$changelog" ]; then
        echo "No CHANGELOG.md found for skill '{{name}}' at $changelog"
        exit 1
    fi
    python3 "{{root}}/scripts/propose_learnings.py" "$changelog"

# Bump every version-bearing plugin manifest: just bump ver=1.3.0
bump ver:
    #!/usr/bin/env python3
    import json
    import re
    from pathlib import Path

    version = "{{ver}}".removeprefix("ver=")
    if re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?", version) is None:
        raise SystemExit(f"invalid semantic version: {version}")

    root_path = Path("{{root}}")
    manifests = (
        root_path / ".claude-plugin" / "plugin.json",
        root_path / ".claude-plugin" / "marketplace.json",
        root_path / ".cursor-plugin" / "plugin.json",
        root_path / ".codex-plugin" / "plugin.json",
    )
    for manifest in manifests:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        if manifest.name == "marketplace.json":
            for plugin in data["plugins"]:
                plugin["version"] = version
        else:
            data["version"] = version
        manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    print(f"Bumped all plugin manifests to {version}")
