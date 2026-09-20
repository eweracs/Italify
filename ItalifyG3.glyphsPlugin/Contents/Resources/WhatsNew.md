# What’s New in Italify

The release notes customers read **inside the plugin** – the Settings
window’s *What’s New* pane, and the window that comes up after an update.
This file is bundled into both plugin targets; `CHANGELOG.md` is not.

Same grammar as `CHANGELOG.md` (`## [X.Y.Z] – YYYY-MM-DD`, then `### Added`
/ `### Changed` / `### Fixed`, then `- ` bullets, continuation lines
indented two spaces), but a different voice: what changed for someone
using Italify, in a sentence or two per bullet. No function or file
names, no build, website or vendor tooling – the same rule as the public
release notes, which are condensed from these sections. A release with
nothing user-facing gets no section here (and then no window after the
update). `## [Unreleased]` is shown in Debug builds only. Inline
Markdown understood: `**bold**`, `*italic*`, `` `code` ``, `[links](…)`.
See RELEASING.md.

## [Unreleased]

## [0.29.1] – 2026-09-20

### Added

- **Export filter with master licences.** With master credits, the
  *Filter* custom parameter now also runs on interpolated instances – as
  long as every master the instance is interpolated from is activated.

### Fixed

- **Per-master parameters at export.** Parameters saved for a master, a
  group in one master or a layer are now interpolated when an instance
  between masters is exported. Before, they were ignored.
- **Curve extension and terminal settings at export.** These are now
  interpolated for instances between masters, too.

## [0.29.0] – 2026-09-20

### Added

- **Arrow keys for curve extension and terminal settings.** Click a
  control in the Italify Tagger to select it, then press ↑ or ↓ to
  change its value by 1 % – or by 10 % with Shift. A selected curve
  extension control shows its percentage.
- **Terminal settings also in upright sources.** If the slant angle is
  0° (e.g. when the angle lock is on and an upright master is selected),
  a selected terminal now still allows for angle and position control.

### Changed

- **The preview panel shows the locked angle.** With the angle lock on,
  the Space + Shift preview panel shows the angle the preview really
  uses – the layer’s own – marked with a padlock.

### Fixed

- **Terminal position on open corners.** A terminal drawn with open
  corners now follows *Keep terminals → Position* – the filter’s and its
  own – like any other terminal.
- **Doubled nodes.** A terminal whose corners are doubled nodes now
  also shows angle and position controls. The same is fixed for curve
  extension settings.

## [0.28.0] – 2026-09-20

### Added

- **Settings and Licences.** A new window – *Glyph → Italify → Settings
  and Licences…*, also in the filter dialogue’s gear menu – now offers
  a centralised place for Italify preferences and licensing.
- **Custom shortcuts.** Every single-key shortcut of the Italify Tagger,
  including the key that activates it, can be re-assigned or removed in
  the Settings window. The right-click menu shows your keys.
- **Advanced options without the Macro panel.** *Flatten intersections*,
  the automatic metric snap, *Correct tagged stems only* and the
  keep-extremes tolerance are now checkboxes and a field in the Settings
  window, next to a switch for the log file.
- **What’s New.** After an update, Italify shows what changed since the
  version you had. You can switch this off in the new Settings window.

### Changed

- ***Generate from* suggests the source by axis location.** In a font
  with an italic or slant axis, the suggested source is the layer at the
  same position on every other axis – whatever the masters are called.
  Intermediate and alternate layers are matched with their counterparts.
- **Resetting modified parameters is a button.** A ↺ button appears next
  to the status line while it reads “… parameters modified”, replacing
  the entry in the ⋯ menu.
- **Licence codes are entered in the Settings window.** The filter
  dialogue’s *Licence…* button and its gear menu now lead there, closing
  the dialogue on the way.

### Fixed

- **A doubled start point no longer reorders the path.** A path starting
  on a doubled node came back with a different start node – the same
  shape, but no longer compatible with the other masters.
- **Red anchors under the tagger’s own in Glyphs 4.** Glyphs 4 kept
  drawing its red anchor markers beneath Italify’s blue ones.
- **Locked angle with several angles selected.** The angle field showed
  “0°” when the selected layers disagreed; it is now empty.
- **UI fixes.** Minor improvements to some UI details.

## [0.27.0] – 2026-09-18

### Added

- **Keep terminals is now two sliders.** *Angle* is the slider you know.
  The new *Position* lets a terminal follow the curve correction along
  its stroke, instead of staying where a plain slant puts it. Files and
  Filter parameters saved with earlier versions behave exactly as before.
- **Individual terminals can have their own settings.** Select a
  terminal in the tagger and drag its two knobs. A small reset button
  marks terminals that carry their own values.
- **Generate from.** A layer can now be generated from another master.
  The filter rebuilds it from that master’s outlines every time it runs,
  so an italic master follows its upright.
- **Angle lock.** The angle can be locked to each layer’s own italic
  angle.
- **Paste Tags onto Selection.** Copied tags can be pasted onto the
  selected nodes.
- **Python API:** `resolved_parameters`, `auto_link_anchors` and
  per-terminal settings are new.

### Changed

- **Python API:** `correct()` now takes `keep_terminal_angle` and
  `keep_terminal_position` instead of `keep_terminals`.
  `set_limit_curve` is removed; use `set_curve_extension(…, 0)` instead.
- **No Curve Correction wins over Curve Extension** where both apply.

### Fixed

- **Inktraps hold their length more reliably** – they are re-solved
  after the stem correction, and find their endpoint next to a No Curve
  Correction segment.
- **Adding an Italify Filter parameter in Font Info no longer crashes
  Glyphs**, and the dialogue lays out correctly there.
- **The *Save for* popup no longer overlaps the Save button** in
  Glyphs 4.

## [0.26.0] – 2026-09-05

### Added

- **Your licence is now registered to your Mac.** When you enter a code,
  Italify registers that Mac with the licence server. A licence covers
  up to three Macs per seat; a trial covers one. Codes you entered
  before this update keep working as they are.
- **One online moment.** Entering a code needs an internet connection;
  afterwards Italify checks in briefly once a day. What it sends: the
  code, a hashed hardware identifier, the Glyphs version and the plugin
  version. Never your fonts or files.
- **Seats for teams.** Additional seats can be bought on the
  [Buy page](https://www.sebastiancarewe.com/italify/buy).

### Changed

- **Licence terms updated** for seats, device registration and what the
  plugin sends: [licence terms](https://www.sebastiancarewe.com/italify/eula).

## [0.25.0] – 2026-08-31

### Added

- **Licence codes by card payment.** Codes bought by card on the Buy
  page arrive by email the moment the payment lands. Enter them within
  90 days of purchase.

## [0.24.1] – 2026-08-31

### Fixed

- **The curve-extension control now appears everywhere it should.** At
  corners where Italify takes the curve as it is, the teal control now
  appears too, resting at “no extension” – drag it to add as much
  extension as the geometry supports.

## [0.24.0] – 2026-08-31

### Added

- **Adjustable curve extension.** Selecting a corner node whose curve
  Italify extends internally now shows a draggable teal control: slide
  it to set how much of that extension is used, from the full extension
  down to none. Partial settings interpolate between masters and reset
  with ⌫.

### Changed

- **Live preview on unlicensed masters.** The filter dialogue no longer
  hides behind a lock: the sliders and the preview work normally, and
  only applying is withheld. A licence bar at the bottom shows what is
  covered and lets you activate a master in place.

### Fixed

- **Stable stem directions.** A stem’s slant direction could in rare
  cases flip from one run to the next.

## [0.23.0] – 2026-08-01

### Added

- **Import.** *Glyph → Italify → Import* copies stems, tags and anchor
  links onto the selected glyphs from another master – of the current
  font, or of another `.glyphs` / `.glyphspackage` file. Imported kinds
  replace what the glyphs carry; one undo reverts the whole batch.

### Changed

- **“Clear all” is now “Clear”.** The submenu reads *Clear → Stems /
  Tags / Anchor Links / All*.

## [0.22.0] – 2026-07-30

### Added

- **Keep nodes on extremes.** A new checkbox at the bottom of the filter
  dialogue, off by default. Where a curve cannot be described with its
  node on the extreme, Italify leaves that node where the correction
  placed it rather than distorting the curve.

## [0.21.2] – 2026-07-29

### Added

- **⌘X cuts the selection.** Copies the selected stems, tags and anchor
  links and removes them in one undo step.
- **Italify is listed in the Glyphs Plugin Manager.** Install and update
  it from there.

### Changed

- **Auto-Tag Stems handles condensed, tapered and fused designs much
  better** – nearly vertical strokes, shallow tapers, fused apexes and
  hairlines now tag, with new safeguards against over-tagging.
- **Automatic anchor edges follow the outline, not the sidebearings.**
- **Tab cycles mixed selections** through the highest type present –
  stems first, then tags, then anchors.

### Fixed

- **Asymmetric stems are no longer flagged as corrupted.**

## [0.21.1] – 2026-07-28

### Changed

- **Time-limited licences start when you enter the code**, not when it
  was issued – a one-week licence is a full week from the moment you
  paste it, and the free trial likewise.

## [0.21.0] – 2026-07-28

### Added

- **Glyphs 4.** Italify now also runs in Glyphs 4.

### Changed

- **Parameter values are stored at the precision the dialogue shows**,
  so moving a slider away and back no longer marks the file as changed.

## [0.20.1] – 2026-07-18

### Added

- **Direction arrow.** A selected anchor with an x/y link shows a small
  arrow below its marker; click it to toggle between left/right and
  up/down movement (⌥ changes all masters).

### Fixed

- **x/y-intersection anchor links now actually follow** the curve they
  are linked to.

## [0.20.0] – 2026-07-18

### Added

- **Auto-Link Anchors.** One command links every unlinked anchor: anchors
  sitting on a curve get an x/y-intersection link, everything else links
  to its nearest node. Anchors you linked by hand are never touched.
- **Smarter anchor links.** Links can attach to path intersections and
  to a curve’s intersection with the anchor’s own x or y.
- **Scope the export filter.** The `Filter = Italify;…` custom parameter
  takes `include:` / `exclude:` glyph lists, wildcards allowed.
- **Wildcards in glyph groups.** A group’s member list accepts live
  patterns such as `*-ar`.

### Changed

- **Toggle Terminal moved from T to C** – T switches to the Text tool
  again – and **Esc** leaves the tagger.
- **The “Save for:” picker opens on the scope currently in use.**
- **Corners can no longer be dropped onto another stem’s nodes.**

### Fixed

- **A Y-Snap tag on a doubled node now always takes effect.**

## [0.19.0] – 2026-07-18

### Added

- **Run Italify from a script.** `italify.correct(layer, angle=10, …)`
  runs the same pass as the filter dialogue, one undo step per call. See
  the [Python API reference](https://www.sebastiancarewe.com/italify/python-api).

### Changed

- **Stem compensation now defaults to 0 %.** Fresh installs no longer
  widen stems unless you turn the slider up; saved settings are
  unchanged.
