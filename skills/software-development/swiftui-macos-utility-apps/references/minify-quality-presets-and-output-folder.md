# Minify session note: quality presets + output folder UX

## Context
Implemented in `Projects/minify` SwiftUI macOS utility app.

## Added pattern
1. `QualityPreset` enum with:
   - `displayName`
   - `qualityValue` (Smallest 0.45, Balanced 0.72, Highest 0.90)
2. ViewModel:
   - `selectedQualityPreset`
   - `applyQualityPreset(_:)`
   - `syncPresetToClosestQuality()` when slider changes
3. Footer UX:
   - `Open Output Folder` button bound to `lastOutputFolder`
   - Auto-open output folder after successful conversion with `NSWorkspace.shared.open(folder)`

## Practical pitfall observed
The working directory had multiple candidate source trees. Initial reads against `Sources/...` failed; correct files were under `Projects/minify/Sources/...`.

## Reusable guardrail
Before edits in CLI sessions:
- locate candidate paths with `search_files("*.swift")`
- verify repo with `git -C <candidate> status`
- then patch using anchored path under the confirmed repo.
