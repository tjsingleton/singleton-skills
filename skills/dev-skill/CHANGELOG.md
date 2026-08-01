# Changelog

All notable changes to the **dev-skill** skill are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

## [Unreleased]

### Changed
- Replaced machine and host cache fallbacks with a tested editable-checkout resolver.
- Made subagent and skill-creator routing capability-based with direct execution fallback.
- Made setup, invocation examples, and sanitization guidance host-neutral.

## [1.0.0] - 2026-04-12

### Added
- Initial skill: full dev lifecycle for singleton-skills (new, eval, iterate, install, list)
- Subagent execution model — spawns agent scoped to SINGLETON_SKILLS_PATH so skill works from any project
- Explicit `cd` in all subagent blocks to prevent inheriting calling session's working directory
- Step 4 — Reflect: after iterate loop, write a CHANGELOG entry with rationale and sanitization check
- Portable repository discovery through `SINGLETON_SKILLS_PATH` or the active skill location
- skill-creator:skill-creator integration for eval/iterate commands
