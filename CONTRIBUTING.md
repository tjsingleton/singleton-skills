# Contributing

## Prepare the environment

Use Linux or macOS with Git, Python 3.11 or newer, and
[Just](https://github.com/casey/just#installation) 1.59.0 or newer. Just runs the
repository's named commands. The installer uses POSIX filesystem operations;
native Windows execution is outside the contributor check matrix. Individual
skills may need additional tools or macOS data access, as described in their
skill instructions.

Check the installed tools:

```bash
git --version
python3 --version
just --version
```

If a command is missing or its version is too old, install a supported version
before continuing. When several Python versions are installed, use a supported
interpreter to create the environment below.

From the repository root, create an isolated Python environment and install the
pinned development dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
just check
```

If environment creation fails because `venv` is unavailable, install your
platform's Python venv package and retry. If dependency installation fails,
check the package-index connection and retry inside the activated environment.
If checks fail, fix the reported error and rerun `just check`. A missing `ruff`
module usually means the environment is inactive or dependencies were installed
under a different interpreter.

## Choose and coordinate work

Read [AGENTS.md](AGENTS.md) before editing. Use the Singleton Skills project in
Linear for specifications, work status, acceptance criteria, and dependencies.
Follow [the tracker guidance](docs/agents/issue-tracker.md) when retrieving or
updating work. Search existing coverage before creating an issue.

Keep reusable instructions and synthetic evaluation evidence in the repository.
Keep current work lists in Linear. Check `git status` before editing and preserve
unrelated uncommitted files and changes.

## Make a focused change

- Keep core skill behavior host-neutral, with a direct fallback for optional
  host capabilities.
- Give each skill discovery metadata that matches its directory and describes
  when to invoke it. Use `just new name=my-skill` to scaffold a new skill.
- Write Python helpers for the minimum contributor runtime. Prefer the standard
  library for repository tooling and document additional skill dependencies.
- Add type annotations and docstrings where they clarify a helper's interface
  or safety boundary. Follow nearby code style; keep formatting changes scoped.
- Test externally visible behavior through the existing installer, helper CLI,
  and conformance tests. Use temporary directories and synthetic fixtures.
- When candidate status changes, keep `supported-skills.txt`, the README support
  matrix, and conformance tests aligned. Installation or packaging success does
  not certify live compatibility on any host.
- When skill behavior changes, run its relevant evaluation protocol as well as
  packaging checks. Record the evidence and its limits. Consult the relevant
  skill evaluation README when one exists.

Ruff checks Python imports, undefined names, and basic errors. Run `just lint`
for a focused check. It reports problems without rewriting files. For a finding,
correct the reported issue and rerun the command; avoid broad automatic fixes
over unrelated work.

## Verify and submit

Run `just check` from the activated environment before submitting. It runs lint,
repository unit and conformance tests, Git-triage contract tests, and Python
compilation checks. Test fixtures do not require live accounts, credentials,
host installations, contacts, or Messages data.

CI runs that same command on Linux and macOS with Python 3.11 and 3.14. It pins
Just to 1.59.0 and installs Ruff from the development requirements. Passing
these checks establishes repository behavior on the tested runtime; live
Claude Code, Cursor, and Codex discovery and behavior checks remain separate.

Review the final diff, including new files. This is a public repository: exclude
secrets, credentials, private paths, contacts, message contents, and sensitive
fixtures. If public suitability is uncertain, obtain explicit confirmation
before publishing.

Use a short, descriptive commit subject that states the change. Open a pull
request with the problem, resulting behavior, relevant Linear issue, validation
results, and material risks or limitations. Use the PR template to record the
review. If CI fails, inspect the failing job, reproduce it with the matching
Python version and `just check`, and address the cause before requesting merge.
Required-check enforcement is a separate repository setting; adding a workflow
does not configure branch protection.
