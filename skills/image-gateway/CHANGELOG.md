# Changelog

All notable changes to this skill are documented in this file.

## [Unreleased]

### Added

- Saved OpenRouter defaults and a one-command image-generation/editing gateway.

### Fixed

- Support for shell-style `export OPENROUTER_API_KEY=...` lines in the saved
  env file.
- A clear stop condition when an account's Zero Data Retention guardrail
  excludes the selected model endpoint.
