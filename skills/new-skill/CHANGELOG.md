# Changelog

All notable changes to the **new-skill** skill are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

## [Unreleased]

### Changed
- Delegated checkout resolution to `dev-skill` and removed the machine-specific fallback.
- Replaced Claude-specific invocation and argument wording with host-neutral guidance.

## [1.0.0] - 2026-04-12

### Added
- Initial skill: scaffold new skill following singleton-skills conventions
- Interview workflow for description, argument-hint, usage hint block, and steps
- Description quality checklist (trigger-aware, includes "Don't use when" contrast)
- `$ARGUMENTS` injection guide and argument-hint documentation
- Dev cycle offer at end: prompt to enter skill-creator loop or just install
- SKILL.md conventions reference table (frontmatter fields, body structure)
