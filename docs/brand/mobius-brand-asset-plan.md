# Mobius Brand Asset Integration Plan

## Goal

Create and integrate a minimal Mobius icon and homepage image from the supplied visual identity content without changing the brand direction: deep space background, luminous Mobius loop, future-facing visual tone, and the `MOBIUS` temporal-governance message.

## Existing asset locations inspected

- `README.md`, `README.zh.md`, `README.ja.md`, and `README.ko.md` are the primary documentation entry points.
- `assets/brand/` is the canonical location for brand assets in this repository.
- `docs/` contains project documentation and can describe asset usage, but brand image files should live in `assets/brand/`.
- No existing favicon, packaged app icon, or web-app splash asset location was found in source code.

## Created assets

| Asset type | Path | Format | Status |
| --- | --- | --- | --- |
| README / homepage hero | `assets/brand/mobius-homepage.svg` | SVG | Created and referenced from README files. |
| App icon candidate | `assets/brand/mobius-icon.svg` | SVG | Created and referenced from README files. |

## Required output formats still recommended

| Asset type | Proposed path | Notes |
| --- | --- | --- |
| GitHub social preview / banner | `assets/brand/mobius-social-preview.png` | Export or crop at 1280×640 when raster conversion tooling is available. |
| App icon raster | `assets/brand/mobius-app-icon-1024.png` | Export from `mobius-icon.svg` for app/package usage. |
| Favicon candidates | `assets/brand/favicon-32.png`, `assets/brand/favicon-16.png`, `assets/brand/favicon.ico` | Derive from the icon candidate when icon tooling is available. |
| Splash screen raster | `assets/brand/mobius-splash-screen.png` | Export from `mobius-homepage.svg` if a PNG splash is needed. |

## Current execution result

- Changed files:
  - `assets/brand/README.md`
  - `assets/brand/mobius-homepage.svg`
  - `assets/brand/mobius-icon.svg`
  - `docs/brand/mobius-brand-asset-plan.md`
  - `README.md`
  - `README.zh.md`
  - `README.ja.md`
  - `README.ko.md`
- Copied assets:
  - None.
- Created assets:
  - `assets/brand/mobius-homepage.svg`
  - `assets/brand/mobius-icon.svg`
- Image conversion performed:
  - No. The generated files are source SVG assets; no PNG/ICO conversion tooling was available in this environment.
- README references:
  - The localized README files now reference the homepage image and icon from `assets/brand/`.

## Next recommended step

Review the SVG visuals in a browser or design tool. If approved, export non-destructive PNG/ICO derivatives for GitHub social preview, app icon, favicon, and splash screen packaging.
