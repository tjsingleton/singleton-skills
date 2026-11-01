# Changelog

All notable changes to this skill are documented here.

## [Unreleased]

### Added

- Portable issue authoring and substantial rewrites with coverage checks,
  requirement preservation, exact proposals, and verified authorized saves.
- Shared Linear contract for authoring, progress reconciliation, and read-only
  triage, including evidence gates and uncertain-write recovery.
- Controlled synthetic request-to-output scenarios and recorded agent runs.

### Fixed

- Require the exact approved content before saving an already approved issue.
  A controlled run exposed invented wording when the approval artifact was
  unavailable; the missing-content path now returns an unsaved draft.
