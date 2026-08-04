# Changelog

All notable changes to the _sample template project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Fixed

- First install now uses `uv sync` without `--frozen`, because generated projects do not include `uv.lock`.
- Generated projects require `arclith>=0.11.0`, matching the canonical `adapters/inbound` and `adapters/outbound` framework layout.

## [0.2.0] — 2026-08-03

### Changed

- Migrated the template implementation to `src/arclith_sample/...`.
- Updated imports, packaging, lint, typecheck and coverage settings for the namespaced source layout.
- Uses local editable `../arclith` during sample validation while generated projects still use the published PyPI package.

---

### Changed

- **BREAKING**: Default repository adapter changed from `mongodb` to `memory` for easier onboarding
  - New projects generated via `arclith-cli` no longer require MongoDB to start
  - All adapter options (memory/mongodb/duckdb) are now documented inline in `config/adapters/adapters.yaml`
  - Migration guide included in configuration comments for production deployments

### Removed

- **BREAKING**: Removed `unit` field from `Ingredient` entity to make template more generic
  - Simplifies the template structure for easier scaffolding
  - Reduces domain-specific logic in the reference implementation
  - Projects can add their own domain-specific fields as needed

### Added

- Comprehensive inline documentation in `config/adapters/adapters.yaml`
  - Detailed comparison of all repository adapter options
  - Clear pros/cons for each adapter choice
  - Step-by-step migration path to production

### Migration Guide

If you have an existing project using the old template:

1. Open `config/adapters/adapters.yaml`
2. Change `repository: mongodb` to `repository: memory` (or keep mongodb if you prefer)
3. Review the new inline documentation for adapter configuration options
