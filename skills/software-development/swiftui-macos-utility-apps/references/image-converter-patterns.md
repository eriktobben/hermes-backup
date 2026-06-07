# Image Converter Patterns (macOS SwiftUI)

## Common web output set
A pragmatic default set for end-user image compression utilities:
- WebP
- PNG
- JPEG
- AVIF

Keep each format mapped to:
- display label
- file extension
- preferred UTType
- fallback format

## Fallback pattern
Use service-level `resolvedFormat(requested)` before each conversion.

Example policy:
- WebP requested but unavailable -> JPEG
- AVIF requested but unavailable -> JPEG

This preserves successful conversion even when runtime codec support differs.

## Collision-safe destination naming
Given `name.ext`:
1. If missing, use as-is.
2. Else try `name-2.ext`, `name-3.ext`, ... until free.

Never overwrite existing files by default.

## Progress callback pattern
Conversion service signature:
`convert(..., progress: ((Int, Int, URL) -> Void)? = nil)`

After each file:
- append result
- emit `(doneCount, totalCount, sourceURL)`

ViewModel receives callback and updates:
- `conversionProgress = done / total`
- `statusMessage = "Converting d/t: filename"`

Perform these updates on `@MainActor`.

## Build verification blocker reporting
If local environment lacks Swift CLI, report explicitly:
- command run: `swift build`
- blocker: `swift: command not found`
- implication: compile verification pending until toolchain installed