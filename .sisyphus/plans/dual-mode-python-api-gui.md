# OSkhQuant Dual-Mode Execution Plan (Python API + GUI)

## TL;DR
> **Summary**: Decouple `khFrame.py` from direct PyQt runtime dependencies so backtests can run headlessly via Python API while preserving existing GUI flow and result windows.
> **Deliverables**:
> - Headless API entry module and result object parser
> - Engine-side UI/interaction adapter boundary (GUI adapter + headless adapter)
> - GUI integration kept compatible with current `StrategyThread -> KhQuantFramework.run()` flow
> - Automated smoke verification commands and evidence artifacts
> **Effort**: Medium
> **Parallel**: YES - 2 waves
> **Critical Path**: T1 (engine interface) -> T2/T3 (PyQt decoupling) -> T6 (API module) -> T9/T10 (verification)

## Context
### Original Request
- "优化成能通过python 接口调用，也能通过GUI操作。"
- "便于你能直接调用和回测，而不用操作界面。"

### Interview Summary
- API return contract: result object + DataFrames + `output_dir`.
- Headless period mismatch behavior: default fail-fast, configurable warning/continue.
- Verification strategy: lightweight smoke validation; no pytest/CI bootstrap in this scope.

### Metis Review (gaps addressed)
- Guardrail: keep CSV artifact contract and directory layout unchanged to avoid GUI breakage.
- Guardrail: move `QSettings`/`QMessageBox`/`QMetaObject` usage behind adapter boundary, no import-time Qt requirements in engine path.
- Risk control: avoid scope creep (no GUI redesign, no trading logic rewrite, no config format rewrite).

## Work Objectives
### Core Objective
- Enable two first-class execution modes over the same backtest core:
  - GUI mode (existing behavior preserved)
  - Headless Python API mode (direct programmatic invocation)

### Deliverables
- New API module (e.g. `api.py`) exposing `run_backtest(...)` and structured `BacktestResult`.
- Engine interaction boundary for UI-dependent operations (log/progress/confirm/result-open hooks).
- Refactored `khFrame.py` runtime logic to eliminate hard PyQt dependency from core execution path.
- GUI wiring update to use adapter path with no user-visible behavior regression.
- Smoke verification assets under `.sisyphus/evidence/`.

### Definition of Done (verifiable conditions with commands)
- `python -c "from api import run_backtest; print(callable(run_backtest))"` succeeds.
- `python -c "import khFrame; from khFrame import KhQuantFramework; print('engine-import-ok')"` succeeds in headless environment.
- GUI strategy start path still calls framework run successfully (manual+scripted smoke evidence captured).
- Backtest output directory contains `trades.csv`, `daily_stats.csv`, `summary.csv`, `benchmark.csv`, `config.csv` after API-run smoke.

### Must Have
- Preserve current backtest output schema/location behavior.
- Preserve GUI button flow and result window opening behavior for GUI mode.
- Provide deterministic headless behavior for period mismatch via explicit API flag.

### Must NOT Have (guardrails, AI slop patterns, scope boundaries)
- Must NOT redesign GUI layout/theme.
- Must NOT change strategy callback contract (`init`, `khHandlebar`, `khPreMarket`, `khPostMarket`).
- Must NOT introduce new config format or break `.kh` JSON compatibility.
- Must NOT introduce heavyweight test framework in this iteration.

## Verification Strategy
> ZERO HUMAN INTERVENTION — all verification is agent-executed.
- Test decision: tests-after + lightweight smoke commands (no pytest bootstrap).
- QA policy: Every task includes happy path + failure/edge scenario with evidence files.
- Evidence: `.sisyphus/evidence/task-{N}-{slug}.{ext}`

## Execution Strategy
### Parallel Execution Waves
> Target: 5-8 tasks per wave. <3 per wave (except final) = under-splitting.
> Extract shared dependencies as Wave-1 tasks for max parallelism.

Wave 1: Core decoupling foundation (`khFrame.py`, adapter contracts, config injection, period confirmation policy, result contract)

Wave 2: API + GUI integration + smoke verification + docs/usage update

### Dependency Matrix (full, all tasks)
- T1 blocks T2, T3, T4, T6, T8
- T2 blocks T7, T8, T10
- T3 blocks T7, T8, T9, T10
- T4 blocks T8
- T5 blocks T6, T7, T10
- T6 blocks T7, T9, T10
- T7 blocks T9, T10, T11
- T8 blocks T10, T11
- T9 blocks T10, T12
- T10 blocks T11, T12
- T11 blocks T12

### Agent Dispatch Summary (wave -> task count -> categories)
- Wave 1 -> 6 tasks -> `deep`, `quick`, `unspecified-high`
- Wave 2 -> 6 tasks -> `unspecified-high`, `quick`, `writing`

## TODOs
> Implementation + Test = ONE task. Never separate.
> EVERY task MUST have: Agent Profile + Parallelization + QA Scenarios.

- [x] 1. Introduce Runtime Interaction Boundary in Engine Core

  **What to do**: Add a runtime interaction interface (`log`, `progress`, `confirm_period_mismatch`, `on_finished`, `open_result`) with headless default implementation and GUI adapter implementation.
  **Must NOT do**: Do not alter trading calculations or strategy callback signatures.

  **Recommended Agent Profile**:
  - Category: `deep` — Reason: cross-cutting refactor.
  - Skills: [`brainstorming`] — ensure stable interface.
  - Omitted: [`playwright`] — no browser scope.

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: [2,3,4,6,8] | Blocked By: []

  **References**:
  - Pattern: `khFrame.py:30`
  - Pattern: `khFrame.py:277`
  - API/Type: `khFrame.py:498`
  - API/Type: `khFrame.py:585`
  - Pattern: `GUIkhQuant.py:2220`

  **Acceptance Criteria**:
  - [x] Engine runtime paths call interaction interface, not GUI concrete methods directly.

  **QA Scenarios**:
  ```text
  Scenario: Headless interaction fallback works
    Tool: Bash
    Steps: `python -c "import khFrame; from khFrame import SimpleGUI; g=SimpleGUI(); g.log_message('smoke'); print('ok')"`
    Expected: Exit 0 and prints "ok".
    Evidence: .sisyphus/evidence/task-1-runtime-boundary.txt

  Scenario: Import path remains stable
    Tool: Bash
    Steps: `python -c "from khFrame import KhQuantFramework; print('import-pass')"`
    Expected: No GUI-dependent import error.
    Evidence: .sisyphus/evidence/task-1-runtime-boundary-error.txt
  ```

  **Commit**: YES | Message: `refactor(engine): add runtime interaction boundary for gui/headless` | Files: [`khFrame.py`, `runtime adapter module if created`]

- [x] 2. Remove Engine `QSettings` Dependency From `run()`

  **What to do**: Replace `QSettings` lookup in `KhQuantFramework.run()` with injected runtime option (`init_data_enabled`) passed from GUI/API.
  **Must NOT do**: Do not change default behavior semantics.

  **Recommended Agent Profile**:
  - Category: `quick` — Reason: localized runtime dependency removal.
  - Skills: [] — direct refactor.
  - Omitted: [`brainstorming`] — design fixed.

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: [7,8,10] | Blocked By: [1]

  **References**:
  - Pattern: `khFrame.py:912`
  - Pattern: `khFrame.py:935`
  - Pattern: `GUIkhQuant.py:212`
  - API/Type: `khConfig.py:6`

  **Acceptance Criteria**:
  - [x] `run()` no longer imports/reads `QSettings` directly.

  **QA Scenarios**:
  ```text
  Scenario: Default behavior preserved
    Tool: Bash
    Steps: Execute framework/API run without explicit override.
    Expected: Same default init-data behavior as before.
    Evidence: .sisyphus/evidence/task-2-init-data-default.txt

  Scenario: Explicit disable path
    Tool: Bash
    Steps: Execute with `init_data_enabled=False`.
    Expected: Data init is skipped and logged.
    Evidence: .sisyphus/evidence/task-2-init-data-disabled.txt
  ```

  **Commit**: YES | Message: `refactor(engine): inject init-data option instead of qsettings` | Files: [`khFrame.py`, `GUIkhQuant.py`, `api.py`]

- [x] 3. Replace Modal Period Mismatch Dialog With Policy Hook

  **What to do**: Refactor `_check_period_consistency()` so headless default is fail-fast and configurable override is warn-and-continue.
  **Must NOT do**: Must not call `QMessageBox`/`QMetaObject` from engine core path.

  **Recommended Agent Profile**:
  - Category: `unspecified-high` — Reason: behavior-critical policy.
  - Skills: [`brainstorming`] — preserve GUI semantics.
  - Omitted: [`playwright`] — not needed.

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: [7,8,9,10] | Blocked By: [1]

  **References**:
  - Pattern: `khFrame.py:1135`
  - Pattern: `khFrame.py:1197`
  - Pattern: `khFrame.py:1219`
  - Pattern: `GUIkhQuant.py:2220`

  **Acceptance Criteria**:
  - [x] Default mismatch in headless mode raises deterministic exception.
  - [x] Override flag continues with warning.

  **QA Scenarios**:
  ```text
  Scenario: Headless mismatch fails fast
    Tool: Bash
    Steps: Run mismatched config with default flags.
    Expected: Non-zero exit with mismatch error.
    Evidence: .sisyphus/evidence/task-3-period-policy-error.txt

  Scenario: Headless mismatch override
    Tool: Bash
    Steps: Run same config with `allow_period_mismatch=True`.
    Expected: Warning and continued execution.
    Evidence: .sisyphus/evidence/task-3-period-policy-allow.txt
  ```

  **Commit**: YES | Message: `refactor(engine): replace modal period check with configurable policy` | Files: [`khFrame.py`, `api.py`, `GUI adapter module`]

- [x] 4. Decouple Engine Result-Window Invocation

  **What to do**: Replace direct result-window invoke in engine with adapter callback; GUI implementation opens window, headless implementation returns/stores path only.
  **Must NOT do**: Do not change output naming/layout.

  **Recommended Agent Profile**:
  - Category: `quick` — Reason: narrow callback refactor.
  - Skills: []
  - Omitted: [`brainstorming`]

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: [8] | Blocked By: [1]

  **References**:
  - Pattern: `khFrame.py:2245`
  - Pattern: `khFrame.py:2476`
  - Pattern: `khFrame.py:2489`
  - Pattern: `GUIkhQuant.py:3568`

  **Acceptance Criteria**:
  - [x] GUI still opens result window on completion.
  - [x] Headless path has no GUI invoke attempt.

  **QA Scenarios**:
  ```text
  Scenario: GUI callback preserved
    Tool: interactive_bash
    Steps: Run short GUI backtest and inspect completion logs.
    Expected: Result-open callback executed without exception.
    Evidence: .sisyphus/evidence/task-4-gui-result-open.txt

  Scenario: Headless no-GUI invoke
    Tool: Bash
    Steps: Run API backtest; inspect logs for GUI invoke calls.
    Expected: No GUI invoke attempt.
    Evidence: .sisyphus/evidence/task-4-headless-no-gui.txt
  ```

  **Commit**: YES | Message: `refactor(engine): route result window opening through runtime adapter` | Files: [`khFrame.py`, `GUIkhQuant.py`]

- [x] 5. Stabilize Backtest Artifact Contract

  **What to do**: Lock artifact set and schema compatibility (`trades.csv`, `daily_stats.csv`, `summary.csv`, `benchmark.csv`, `config.csv`).
  **Must NOT do**: Must not rename artifacts or remove expected columns.

  **Recommended Agent Profile**:
  - Category: `unspecified-low`
  - Skills: []
  - Omitted: [`brainstorming`]

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: [6,7,10] | Blocked By: [1]

  **References**:
  - Pattern: `khFrame.py:2291`
  - Pattern: `khFrame.py:2302`
  - Pattern: `khFrame.py:2335`
  - Pattern: `khFrame.py:2400`
  - Pattern: `khFrame.py:2476`
  - Pattern: `backtest_result_window.py:36`

  **Acceptance Criteria**:
  - [x] Artifact contract unchanged after refactor.

  **QA Scenarios**:
  ```text
  Scenario: Full artifact set exists
    Tool: Bash
    Steps: Run one backtest and list latest run directory files.
    Expected: All required CSV artifacts exist.
    Evidence: .sisyphus/evidence/task-5-artifacts.txt

  Scenario: No-trade schema still valid
    Tool: Bash
    Steps: Run no-signal strategy and inspect `trades.csv` header.
    Expected: File exists with expected columns.
    Evidence: .sisyphus/evidence/task-5-artifacts-empty-trade.txt
  ```

  **Commit**: YES | Message: `chore(backtest): harden artifact compatibility contract` | Files: [`khFrame.py`]

- [x] 6. Implement `backtest_result.py` Parser for API Return Object

  **What to do**: Add parser for run directory artifacts into structured return object.
  **Must NOT do**: Do not import PyQt/GUI modules.

  **Recommended Agent Profile**:
  - Category: `quick`
  - Skills: []
  - Omitted: [`playwright`]

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: [7,9,10] | Blocked By: [1,5]

  **References**:
  - Pattern: `khFrame.py:2245`
  - Pattern: `khFrame.py:2291`
  - Pattern: `khFrame.py:2302`
  - Pattern: `khFrame.py:2335`
  - Pattern: `khFrame.py:2476`

  **Acceptance Criteria**:
  - [x] Valid run dir parses into expected fields.
  - [x] Missing artifact error is explicit.

  **QA Scenarios**:
  ```text
  Scenario: Parse happy path
    Tool: Bash
    Steps: Parse latest run and print per-artifact row counts.
    Expected: Exit 0 with counts.
    Evidence: .sisyphus/evidence/task-6-parser-happy.txt

  Scenario: Parse missing-path failure
    Tool: Bash
    Steps: Parse non-existent directory.
    Expected: Clear missing-path/missing-file error.
    Evidence: .sisyphus/evidence/task-6-parser-error.txt
  ```

  **Commit**: YES | Message: `feat(api): add backtest result parser and structured return type` | Files: [`backtest_result.py`]

- [x] 7. Add Headless API Entry Module (`api.py`)

  **What to do**: Implement `run_backtest(config, strategy_file, *, allow_period_mismatch=False, init_data_enabled=None)` returning result object + output path.
  **Must NOT do**: Must not use GUI threads/classes.

  **Recommended Agent Profile**:
  - Category: `unspecified-high`
  - Skills: [`brainstorming`]
  - Omitted: [`playwright`]

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: [9,10,11] | Blocked By: [2,3,5,6]

  **References**:
  - Pattern: `GUIkhQuant.py:147`
  - API/Type: `khFrame.py:498`
  - API/Type: `khFrame.py:912`
  - API/Type: `khConfig.py:6`
  - API/Type: `backtest_result.py`

  **Acceptance Criteria**:
  - [x] `run_backtest` import/call works and returns contract fields.

  **QA Scenarios**:
  ```text
  Scenario: API happy path
    Tool: Bash
    Steps: Run short backtest via API and print `result.output_dir`.
    Expected: Exit 0 with valid path and metrics.
    Evidence: .sisyphus/evidence/task-7-api-happy.txt

  Scenario: API invalid strategy path
    Tool: Bash
    Steps: Call API with missing strategy file.
    Expected: Deterministic missing-path error.
    Evidence: .sisyphus/evidence/task-7-api-error.txt
  ```

  **Commit**: YES | Message: `feat(api): expose headless run_backtest entrypoint` | Files: [`api.py`, `khFrame.py`, `backtest_result.py`]

- [x] 8. Preserve GUI Flow While Switching to Runtime Options

  **What to do**: Update GUI launch path to pass runtime options/adapters explicitly while preserving user workflow.
  **Must NOT do**: Do not change GUI button behavior.

  **Recommended Agent Profile**:
  - Category: `quick`
  - Skills: []
  - Omitted: [`brainstorming`]

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: [10,11] | Blocked By: [1,2,4]

  **References**:
  - Pattern: `GUIkhQuant.py:2220`
  - Pattern: `GUIkhQuant.py:2255`
  - Pattern: `GUIkhQuant.py:2307`
  - Pattern: `GUIkhQuant.py:3568`

  **Acceptance Criteria**:
  - [x] GUI start/stop/completion path unchanged from user perspective.

  **QA Scenarios**:
  ```text
  Scenario: GUI start-stop smoke
    Tool: interactive_bash
    Steps: Launch GUI, start then stop run, collect logs.
    Expected: No uncaught exception.
    Evidence: .sisyphus/evidence/task-8-gui-start-stop.txt

  Scenario: GUI completion callback smoke
    Tool: interactive_bash
    Steps: Run short completion and inspect logs.
    Expected: Completion callback and result-open path run.
    Evidence: .sisyphus/evidence/task-8-gui-finish.txt
  ```

  **Commit**: YES | Message: `refactor(gui): pass runtime options to framework without ux changes` | Files: [`GUIkhQuant.py`, `khFrame.py`]

- [x] 9. Enforce Headless Policy Flags and Error Semantics

  **What to do**: Ensure API flags are fully threaded and produce explicit deterministic errors/warnings.
  **Must NOT do**: Must not silently swallow mismatch/config errors.

  **Recommended Agent Profile**:
  - Category: `quick`
  - Skills: []
  - Omitted: [`brainstorming`]

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: [10,12] | Blocked By: [3,6,7]

  **References**:
  - Pattern: `khFrame.py:1135`
  - Pattern: `khFrame.py:2503`
  - API/Type: `api.py`

  **Acceptance Criteria**:
  - [x] Default mismatch policy is fail-fast.
  - [x] Override policy warns and continues.

  **QA Scenarios**:
  ```text
  Scenario: Default mismatch policy raises
    Tool: Bash
    Steps: Run API with mismatched period config and default flag.
    Expected: Non-zero exit with mismatch error.
    Evidence: .sisyphus/evidence/task-9-policy-default-error.txt

  Scenario: Override policy continues
    Tool: Bash
    Steps: Run with `allow_period_mismatch=True`.
    Expected: Warning and continued start.
    Evidence: .sisyphus/evidence/task-9-policy-override.txt
  ```

  **Commit**: YES | Message: `feat(api): enforce explicit period mismatch policy semantics` | Files: [`api.py`, `khFrame.py`]

- [x] 10. Add Automated Smoke Verification Runner

  **What to do**: Add one lightweight smoke runner command/script for import/API/artifact checks.
  **Must NOT do**: Do not introduce pytest in this iteration.

  **Recommended Agent Profile**:
  - Category: `unspecified-low`
  - Skills: []
  - Omitted: [`brainstorming`]

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: [11,12] | Blocked By: [2,3,5,7,8,9]

  **References**:
  - Pattern: `khFrame.py:2245`
  - Pattern: `khFrame.py:2291`
  - Pattern: `GUIkhQuant.py:2220`

  **Acceptance Criteria**:
  - [x] Single smoke command exits 0 on pass and writes evidence files.

  **QA Scenarios**:
  ```text
  Scenario: Smoke runner happy
    Tool: Bash
    Steps: Run smoke command/script from repo root.
    Expected: Exit 0 and evidence generated.
    Evidence: .sisyphus/evidence/task-10-smoke-happy.txt

  Scenario: Smoke runner failure report
    Tool: Bash
    Steps: Run with invalid strategy argument.
    Expected: Non-zero exit and failed-check summary.
    Evidence: .sisyphus/evidence/task-10-smoke-error.txt
  ```

  **Commit**: YES | Message: `chore(verification): add automated dual-mode smoke runner` | Files: [`smoke script/module`, `.sisyphus/evidence/*`]

- [x] 11. Document Python API Usage and Compatibility Notes

  **What to do**: Update docs with API usage examples, flags, and compatibility notes.
  **Must NOT do**: Do not rewrite unrelated documentation sections.

  **Recommended Agent Profile**:
  - Category: `writing`
  - Skills: []
  - Omitted: [`playwright`]

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: [12] | Blocked By: [7,8,10]

  **References**:
  - Pattern: `README.md`
  - Pattern: `GUIkhQuant.py:2220`
  - API/Type: `api.py`

  **Acceptance Criteria**:
  - [x] README includes working API invocation example and mismatch-policy notes.

  **QA Scenarios**:
  ```text
  Scenario: Doc example execution
    Tool: Bash
    Steps: Run documented example command.
    Expected: Exit 0 and output path printed.
    Evidence: .sisyphus/evidence/task-11-doc-example.txt

  Scenario: Error guidance validity
    Tool: Bash
    Steps: Trigger mismatch case and compare with docs.
    Expected: Docs match actual failure/solution.
    Evidence: .sisyphus/evidence/task-11-doc-error.txt
  ```

  **Commit**: YES | Message: `docs(api): add headless backtest usage and policy notes` | Files: [`README.md`]

- [x] 12. Final Dual-Mode Regression Pass and Evidence Consolidation

  **What to do**: Execute full smoke matrix and consolidate evidence for handoff.
  **Must NOT do**: Must not mark done if any required check/evidence is missing.

  **Recommended Agent Profile**:
  - Category: `unspecified-high`
  - Skills: []
  - Omitted: [`brainstorming`]

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: [] | Blocked By: [9,10,11]

  **References**:
  - Pattern: `khFrame.py:2291`
  - Pattern: `khFrame.py:2302`
  - Pattern: `khFrame.py:2335`
  - Pattern: `khFrame.py:2400`
  - Pattern: `khFrame.py:2476`
  - Pattern: `GUIkhQuant.py:3568`

  **Acceptance Criteria**:
  - [x] All smoke checks pass for both modes.
  - [x] Evidence exists for all QA scenarios.

  **QA Scenarios**:
  ```text
  Scenario: Full matrix pass
    Tool: Bash
    Steps: Run consolidated smoke matrix command.
    Expected: Exit 0 and full-pass summary.
    Evidence: .sisyphus/evidence/task-12-matrix-happy.txt

  Scenario: Matrix fail blocks approval
    Tool: Bash
    Steps: Inject one invalid input and rerun matrix.
    Expected: Non-zero exit and failed-case listing.
    Evidence: .sisyphus/evidence/task-12-matrix-error.txt
  ```

  **Commit**: NO | Message: `n/a` | Files: [`n/a`]

## Final Verification Wave (4 parallel agents, ALL must APPROVE)
- [x] F1. Plan Compliance Audit — oracle
- [x] F2. Code Quality Review — unspecified-high
- [x] F3. Real Manual QA — unspecified-high (+ playwright if UI)
- [x] F4. Scope Fidelity Check — deep

## Commit Strategy
- Commit 1: `refactor(engine): decouple runtime UI dependencies for headless execution`
- Commit 2: `feat(api): add headless backtest API and result parsing contract`
- Commit 3: `chore(verification): add smoke verification scripts and usage docs`

## Success Criteria
- API and GUI can both trigger backtests from the same engine logic without behavior divergence.
- Headless mode does not require PyQt modal interaction or QSettings reads in core runtime path.
- Existing GUI workflow remains usable with equivalent result outputs and result window behavior.
- Smoke evidence demonstrates happy path and failure-path handling for both modes.
