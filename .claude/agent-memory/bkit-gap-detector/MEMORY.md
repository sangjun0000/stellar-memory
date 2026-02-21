# Gap Detector Memory

## Project: stellar-memory

### Architecture
- Package: `stellar_memory/` under `C:\Users\USER\env_1\stellar-memory\`
- Design docs: `C:\Users\USER\env_1\docs\02-design\features\`
- Analysis docs: `C:\Users\USER\env_1\docs\03-analysis\`
- Tests: `C:\Users\USER\env_1\stellar-memory\tests\`
- Python project, pyproject.toml based, zero core deps, optional deps for AI features

### P1 Feature Analysis History
- v0.1 (2026-02-20): 79% match rate, 11 missing items
- v0.2 (2026-02-20): 89% match rate after fixes, 4 remaining items
- Weakest section: WeightTuner (60%) -- uses usage-rate strategy vs design's hit-rate
- Design uses single ImportanceEvaluator; impl uses RuleBasedEvaluator + LLMEvaluator split
- `store()` importance default: design says `None` (AI-first), impl uses `0.5` + `auto_evaluate` flag
- Key P1 files: embedder.py, importance_evaluator.py, llm_adapter.py, weight_tuner.py, utils.py

### Scoring Approach
- Per-section scored /10, weighted average for overall %
- "Match" = functionally equivalent even if naming differs
- "Changed" = behavior preserved but API/signature differs
- "Added" = not in design but enhances, does not penalize score
- "Missing" = design specifies, implementation lacks -- penalizes score
- Weight 0.5 for trivial files (version bumps, assets), 1.0 for substantive modules

### Platform-SDK Analysis (2026-02-21)
- v1 (initial): 68% match rate -- below 70% threshold
- v2 (iter-1): 88% match rate -- above 70%, approaching 90% target
- v3 (iter-2): 89% match rate -- 1% below 90% target
- F5 Protocols: 95% (unchanged across all iterations)
- F4 Builder: 92% (unchanged across all iterations)
- F3 Plugin: 98% (unchanged since iter-1)
- F1 Core SDK: 81% (was 78%) -- link() default fixed to "related", session property added, EventConfig removed
- F2 Package Split: 91% (was 92%) -- regression: EventConfig compat map entry now stale
- F6 Migration: 90% (unchanged since iter-1)
- Remaining gaps: config.py 30 dataclasses (target 12), stellar.py 1072 LOC (target 400)
- Key insight: removing a config class requires updating compat maps too -- stale entries cause runtime errors
- Key insight: fixing EventConfig compat map (2 line deletions) would push exactly to 90.0%
- Key insight: config simplification is the structural bottleneck but functional goals are all met
- Design doc path: docs/02-design/features/platform-sdk.design.md
- Analysis output: docs/03-analysis/platform-sdk.analysis.md

### Homunculus Installer Analysis (env_3)
- Date: 2026-02-20, Match Rate: 92%
- 7 new files + 2 modified files + 1 asset, all in Python/bat/sh
- Weakest: setup.py (3/10) -- design said modularize + add scope step, not done
- icon.ico partial (7/10) -- multi-resolution spec unverifiable from binary
- All core installer files (installer.py, installer_wizard.py, shortcut.py, scripts) were exact or near-exact matches
- Common pattern: impl improves on design (existence guards, simplified branches) -- record as "Changed" not "Missing"
- Unused imports (os) in installer.py and installer_wizard.py -- low severity code quality note
