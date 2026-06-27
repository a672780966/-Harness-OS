# Mobius Brand Asset Integration Plan

## Goal

Integrate the finalized Mobius visual identity as a canonical repository asset without redesigning, regenerating, or restyling the image.

## Existing asset locations inspected

- `README.md`, `README.zh.md`, `README.ja.md`, and `README.ko.md` are the primary documentation entry points.
- `docs/` contains project documentation and is appropriate for documentation-facing imagery.
- No existing favicon, app icon, splash screen, social preview, or brand asset directory was found outside the previously generated SVG files.
- The generated SVG icon and splash files from the previous pass were removed because the canonical image must not be redesigned.

## Proposed repository locations

| Asset type | Proposed path | Source | Notes |
| --- | --- | --- | --- |
| Canonical visual identity reference | `assets/brand/mobius-visual-identity-canonical.png` | Direct copy from `/mnt/data/1000037149.png` | Preserve unchanged. |
| README hero image | `assets/brand/mobius-readme-hero.png` | Non-destructive copy or crop from canonical image | Add only after confirming desired crop. |
| GitHub social preview / banner | `assets/brand/mobius-social-preview.png` | Non-destructive crop or resize from canonical image | GitHub social preview commonly uses a 1280×640 image. |
| App icon candidate | `assets/brand/mobius-app-icon-1024.png` | Non-destructive crop from canonical app-icon panel | Use the app-icon area from the canonical reference. |
| Favicon candidates | `assets/brand/favicon-32.png`, `assets/brand/favicon-16.png`, `assets/brand/favicon.ico` | Derived from app icon candidate | Generate only with approved tooling and source crop. |
| Splash screen candidate | `assets/brand/mobius-splash-screen.png` | Non-destructive crop from canonical splash panel | Use the splash-screen panel from the canonical reference. |

## Current execution result

- Changed files:
  - `assets/brand/README.md`
  - `docs/brand/mobius-brand-asset-plan.md`
  - `README.md`
  - `README.zh.md`
  - `README.ja.md`
  - `README.ko.md`
  - `docs/assets/mobius-icon.svg`
  - `docs/assets/mobius-splash.svg`
- Copied assets:
  - None. The input file `/mnt/data/1000037149.png` was not present in this environment.
- Derived assets:
  - None. Image conversion tooling was not used because the canonical input file was unavailable and Python Pillow was not installed.
- Image conversion performed:
  - No.
- README references:
  - The README files should reference the canonical README hero image later, after `assets/brand/mobius-readme-hero.png` or the direct canonical image is available.

## Next recommended step

Provide the canonical image at `assets/brand/mobius-visual-identity-canonical.png` or make `/mnt/data/1000037149.png` available, then generate only direct, non-destructive crops/resizes for README, social preview, app icon, favicon, and splash usage.
