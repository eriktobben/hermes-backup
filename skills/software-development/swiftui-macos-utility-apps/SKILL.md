---
name: swiftui-macos-utility-apps
description: Build and iterate small macOS SwiftUI utility apps with AppKit integrations for file picking, drag-drop, and batch processing. Use when implementing desktop tools that process local files, need progress UX, and require codec/format fallback behavior.
---

# SwiftUI macOS Utility Apps

## When to use
Use for macOS desktop utilities that combine SwiftUI UI with AppKit/FileManager/ImageIO workflows (batch converters, file processors, local automation tools).

## Core workflow
1. **Model output capabilities explicitly**
   - Define an `OutputFormat` enum with display name, extension, preferred `UTType`, and fallback format.
   - Keep fallback logic centralized in the conversion service (`resolvedFormat`).

2. **Design conversion as a service, not in ViewModel**
   - Service owns file IO, destination generation, codec logic, and conversion loop.
   - ViewModel owns state (`isConverting`, `conversionProgress`, status/error text, selected files, results).

3. **Handle user file input from multiple paths**
   - `NSOpenPanel` for picking files.
   - SwiftUI `.onDrop` for drag-and-drop (`UTType.fileURL.identifier`).
   - Deduplicate by canonical file path in ViewModel.

4. **Implement safe output writing**
   - Never overwrite silently.
   - Generate unique destination names (`name.ext`, `name-2.ext`, `name-3.ext`, ...).

5. **Expose progress from service to UI**
   - Add a progress callback in service (`(done, total, currentURL) -> Void`).
   - Update `@Published` progress/status on `@MainActor`.
   - Show a `ProgressView` while converting.

6. **Show actionable results**
   - Return structured `ConversionResult` including source, destination, original/output bytes.
   - UI shows total input/output plus per-file savings samples.

7. **Add quality presets without losing manual control**
   - Model presets as an enum (e.g., `smallest`, `balanced`, `highest`) with `displayName` and numeric `qualityValue`.
   - ViewModel method `applyQualityPreset(_:)` sets slider quality and recomputes estimates.
   - When slider moves manually, snap preset selection to nearest preset (`syncPresetToClosestQuality`) so UI state stays coherent.

8. **Improve post-conversion workflow**
   - Persist `lastOutputFolder` in ViewModel after a successful run.
   - Auto-open output folder on success (`NSWorkspace.shared.open(folder)`).
   - Also expose an explicit “Open Output Folder” button (disabled until a folder exists).

## Pitfalls
- **Codec support varies by macOS version/runtime**: WebP/AVIF may not be universally writable. Always resolve to a supported fallback (typically JPEG) when `UTType`/destination support is unavailable.
- **UI thread violations**: service callbacks can run off-main-thread; bounce updates to `@MainActor`.
- **Selection UX debt**: include per-item removal and clear-all to avoid forcing users to restart selection.
- **Build checks can be environment-limited**: if `swift` CLI is missing, report verification as blocked and provide exact missing prerequisite.
- **Workspace path ambiguity**: this environment can contain multiple similarly named trees (e.g., `./Sources` and `Projects/minify/Sources`). Before patching files, confirm target repo root with `search_files` + `git -C <path> status` and then use absolute/anchored paths.

## Verification checklist
- `swift build` succeeds (or report exact environment blocker).
- Drag-drop imports files correctly.
- Duplicate filename outputs get suffixes instead of overwrite.
- Progress bar increments to 100% and status text updates per file.
- Unsupported requested output format falls back cleanly and still completes conversion.

## References
- See `references/image-converter-patterns.md` for concrete snippets and fallback patterns.
- See `references/minify-quality-presets-and-output-folder.md` for preset-sync and output-folder UX pattern, plus path-ambiguity guardrail.