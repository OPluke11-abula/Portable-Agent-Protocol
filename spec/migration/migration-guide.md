# Portable Agent Protocol (PAP) Versioning and Migration Guide

This guide establishes the versioning principles for the Portable Agent Protocol and describes migration procedures between protocol releases.

---

## 1. Versioning Rules

PAP adheres strictly to **Semantic Versioning (SemVer) 2.0.0** rules:

- **MAJOR Version (`X.y.z`)**: Incremented when backward-incompatible changes are made.
  - Examples: Removing required schema fields, changing the layout registry structure, changing path resolution rules, or breaking existing CLI/API signatures.
- **MINOR Version (`x.Y.z`)**: Incremented when backward-compatible features are added.
  - Examples: Introducing optional schema fields, adding new CLI arguments, or introducing new memory backends.
- **PATCH Version (`x.y.Z`)**: Incremented for backward-compatible bug fixes.
  - Examples: Clarifying schema descriptions, refining validation messages, or fixing internal runtime bugs.

---

## 2. Compatibility Checks

Runtimes MUST inspect the manifest's version fields during bootstrap:
- **`protocol_version`**: If the major version does not match the runtime's supported protocol major version, the runtime must warn the user of potential incompatibilities.
- **`min_runtime_version`**: If the runtime's current version is less than `min_runtime_version`, the runtime must warn the user to upgrade the runtime package.

---

## 3. Migration Guide: Upgrading to v1.x.y

If moving from a pre-v1.0.0 prototype to a stable v1.0.0 release:

1. **Manifest File Layout**:
   Ensure `.agent/agent.md` declares `protocol_version: "1.0.0"` in its front-matter.
2. **Schema Uniformity**:
   Run the CLI validation to check your workspace's integrity:
   ```bash
   python cli.py validate
   ```
3. **Memory Backends**:
   Ensure sqlite, episodic, or semantic directories are placed under `.agent/memory/`.
