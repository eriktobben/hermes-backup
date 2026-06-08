---
name: creative-workstation-consulting
description: "Recommend hardware (Mac/PC) for creative professionals — Adobe CC users working with large files, multi-app workflows, and demanding rendering/animation. Use when asked to recommend a computer, workstation, or hardware configuration for graphic design, photo editing, video production, print layout, animation, or 3D work."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [product-recommendations, hardware, creative, adobe, mac, consulting, sales]
    related_skills: []
---

# Creative Workstation Consulting

## Overview

Creative professionals — particularly those in Adobe Creative Cloud (Photoshop, InDesign, Bridge, Illustrator, After Effects, Premiere Pro) — have specific hardware needs driven by file sizes, layer counts, multitasking patterns, and rendering workloads. This skill structures a three-tier recommendation approach suitable for B2B sales or consulting.

## When to Use

- Customer asks for a new computer/workstation for design, photo editing, video, print, or animation work
- Customer describes workflow with large files (500MB–2GB+ PSD, TIFF, INDD)
- Customer mentions Adobe CC, Figma, Affinity Suite, DaVinci Resolve, or similar creative tools
- Customer asks for "three alternatives" from budget to premium
- Customer is a museum, agency, print shop, photography studio, or design firm

## Workflow

### Step 1: Gather Requirements

Ask about or extract from conversation:
- **Primary apps**: Which Creative Cloud apps? (Photoshop, InDesign, Illustrator, Premiere Pro, After Effects, Bridge, Lightroom)
- **File sizes**: Typical PSD/AI/INDD file sizes and layer counts. "A 1.25 GB Photoshop file with many layers" vs "500 KB JPEGs" gives very different answers.
- **Workflow pattern**: Single heavy file at a time, or multiple apps with multiple files simultaneously? (Bridge + InDesign + Photoshop open concurrently changes RAM recommendations dramatically.)
- **Additional tasks**: Animations, video editing, 3D rendering, color grading, web publishing
- **Current bottleneck**: Where does the current machine fail? (Lag on save, must close apps, impossible to open certain files)
- **Budget**: Open-ended or specific range? "Three alternatives from budget to premium" is common.

### Step 2: Map Requirements to Hardware

| Requirement | Recommendation |
|---|---|
| 1GB+ PSD files with many layers | 64 GB RAM minimum; 96 GB recommended |
| 500MB–1GB files, moderate layers | 36–48 GB RAM |
| Multiple Adobe apps simultaneously | Add 16–32 GB per additional heavy app |
| Video editing (Premiere Pro, DaVinci) | GPU matters: 40+ cores preferred |
| After Effects / animations | RAM + CPU cores: 64 GB+ and 16+ CPU cores |
| Print layout (InDesign, Illustrator) | Moderate GPU, RAM priority |
| Future-proofing (5+ years) | One chip tier above current needs |

**Key insight for Adobe Photoshop**: Photoshop uses system RAM for both the file content AND all undo history, layer comps, smart objects, and cache. A 1.25 GB PSD with layers typically needs 4–6× the file size in available system RAM when actively worked on. So a 1.25 GB file = 5–8 GB of just that file's working set, plus the OS and other apps.

### Step 3: Structure Three Tiers

Use a consistent format:

1. **🟢 Alternativ 1 — Prisvennlig** ("budget")
   - Clean functional machine for current needs
   - May compromise on future-proofing
   - Frame as: "Meets today's requirements, may need replacing sooner"

2. **🟡 Alternativ 2 — Anbefalt** ("sweet spot")
   - Best price/performance ratio
   - Comfortably handles typical workflow without compromises
   - Frame as: "The best value for your use case"

3. **🔵 Alternativ 3 — Topp/Stødig** ("premium")
   - Maximum specs, maximum future-proofing
   - For customers where downtime is expensive and longevity matters
   - Frame as: "Will handle anything for 5–7 years"

Each tier should include:
- Chip/processor
- RAM
- Storage
- Notable features (ports, networking)
- ca. price range
- Brief rationale paragraph

### Step 4: Add Comparison Table

Include a quick table so the customer can compare tiers at a glance.

| | Alt 1 | Alt 2 | Alt 3 |
|---|---|---|---|
| **Chip** | ... | ... | ... |
| **RAM** | ... | ... | ... |
| **Storage** | ... | ... | ... |
| **Key differentiator** | ... | ... | ... |
| **ca. pris** | ... | ... | ... |

### Step 5: Make a Recommendation

End with a clear "Anbefalingen min" statement that calls out which option you'd pick and why. This helps the customer (and the salesperson) make a decision.

## Common Pitfalls

- **Don't underspec RAM for Photoshop**. 36 GB is too tight for 1+ GB PSD files with many layers. Always err on the high side — RAM is the #1 bottleneck for creative work.
- **Don't recommend "minimum specs" from Adobe's website**. Those specs are for opening the app, not for real work. Real recommendations need 2–4× the listed minimum.
- **M-series unified memory**: Upgrading RAM also upgrades memory bandwidth on some M-series configs. An M4 Max (14-core, 36 GB) has 410 GB/s bandwidth; the 16-core model with 64+ GB has 546 GB/s.
- **M4 Max vs M3 Ultra**: M4 Max has newer architecture and better single-core, but M3 Ultra has 2× the memory bandwidth (819 GB/s) and more cores. For file-opening, layer operations, and multitasking, Ultra wins. For lightly-threaded tasks, M4 Max can feel faster.
- **Don't forget the display**: If they're coming from an iMac, they need a monitor. Mac Studio has no built-in display. Budget for a Studio Display or similar (kr 15.000–20.000+).
- **SSD sizing**: Large creative files consume storage fast. 512 GB is too small for a professional designer. 1 TB minimum, 2 TB recommended.
- **Norwegian VAT**: Always use Norwegian prices (inkl. mva) when presenting to customers. Apple NO prices include 25% VAT.

## Reference Files

- `references/mac-studio-norway-pricing-2026.md` — Verified Norwegian Apple Store pricing, config options, memory bandwidth data, and display costs for Mac Studio (M4 Max / M3 Ultra). Read this first when recommending a Mac in Norway.

## Verification Checklist

- [ ] Did I capture file sizes, layer counts, and apps used?
- [ ] Did I ask about multitasking (how many apps open simultaneously)?
- [ ] Do all three tiers have clear differentiation?
- [ ] Did I include a comparison table?
- [ ] Did I end with a clear recommendation?
- [ ] For Mac recommendations: did I remember they need a separate display?
- [ ] Are prices in NOK with Norwegian VAT included?
