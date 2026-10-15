"""Italify scripting API.

Thin Python shim over the compiled ``@objc(ItalifyScripting)`` facade
that ships in ``Italify.glyphsPlugin``. The facade holds one headless
``ItalifyInterface`` engine and calls the same layer-pure operation
cores the tagger and the Glyph > Italify menu use, so a script
authors the exact ``userData`` contract the filter consumes. It never
moves geometry.

Naming: a *diagonal* was called a *stem* up to v0.29.x – in this API,
in the facade and in the ``userData`` keys. All of them were renamed
together (old fonts are migrated as they open), with no aliases.
``stem_compensation`` is a different thing (the filter’s *Stem
compensation* parameter, about vertical stems) and keeps its name.

Discovery: this package lives in a top-level ``Python API/`` folder at
the repo root and is made importable by a symlink into Glyphs’ Scripts
folder (registered as a hidden *Module* dependency of the plug-in in the
package index – see ItalifyInterface/ARCHITECTURE.md s.11). The facade
class is reached via ``objc.lookUpClass`` regardless of ``sys.path``
because it is compiled into the loaded bundle.

Every mutating call returns an :class:`ItalifyResult` that is truthy on
success and carries ``.diagonal_id`` / ``.count`` and, on refusal,
``.reason`` (a machine code) + ``.message``::

    import italify
    layer = Glyphs.font.selectedLayers[0]
    r = italify.add_diagonal(layer, layer.selection)
    if r:
        italify.set_anchored_edge(layer, r.diagonal_id, a, b)
    else:
        print("refused:", r.reason, r.message)

Set ``italify.strict = True`` (or pass ``strict=True`` per call) to make
a refusal raise :class:`ItalifyError` instead of returning it.
"""

from __future__ import annotations

import objc

__all__ = [
    "ItalifyError",
    "ItalifyResult",
    "ItalifyDiagonal",
    "strict",
    # reads
    "diagonal_ids", "corners", "extras", "is_corrupted", "is_flipped",
    "anchored_edge", "hinge_corners", "linked_nodes", "linked_anchors",
    "curve_extension", "has_no_curve_correction", "has_inktrap", "snap_y", "terminal",
    "terminal_angle", "terminal_position",
    # diagonal objects
    "diagonal", "diagonals",
    # diagonals
    "add_diagonal", "add_diagonal_explicit", "delete_diagonal", "set_flipped",
    # corner roles
    "set_anchored_edge", "set_hinge_corners",
    # extras
    "add_extras", "remove_extras",
    # tag flags
    "set_curve_extension", "set_no_curve_correction", "set_inktrap", "set_snap_y", "set_terminal",
    "set_terminal_angle", "set_terminal_position",
    # anchor links
    "link_anchor", "unlink_anchor",
    # bulk
    "auto_tag", "auto_link_anchors", "resolve_corrupted",
    "clear_diagonals", "clear_tags", "clear_anchor_links", "clear",
    "propagate_diagonals", "propagate_tags", "propagate_anchor_links", "propagate",
    # cross-layer transfer
    "transfer",
    # parameters + correction
    "resolved_parameters", "correct",
]

try:
    _api = objc.lookUpClass("ItalifyScripting").new()
except objc.error as exc:  # class not in the loaded bundle
    raise ImportError(
        "ItalifyScripting was not found in the running Glyphs process. "
        "Rebuild Italify.glyphsPlugin with the scripting facade and "
        "relaunch Glyphs."
    ) from exc


# -- Result / error ----------------------------------------------------

#: When True, a refused write raises ItalifyError instead of returning a
#: falsy ItalifyResult. Override per call with the ``strict=`` kwarg.
strict = False


class ItalifyError(Exception):
    """Raised (in strict mode) when a write is refused."""

    def __init__(self, reason, message):
        self.reason = reason
        self.message = message
        super().__init__(f"{reason}: {message}" if reason else message)


class ItalifyResult:
    """Pythonic view of the facade’s ``ItalifyResult``.

    Truthy on success. ``diagonal_id`` is the new UUID for ``add_diagonal`` /
    ``add_diagonal_explicit`` (else None); ``count`` is masters touched /
    diagonals repaired / segments tagged; ``reason`` / ``message`` describe a
    refusal (both None / "" on success).
    """

    __slots__ = ("ok", "diagonal_id", "count", "reason", "message", "_layer")

    def __init__(self, objc_result, layer=None):
        # Read via KVC so this works regardless of how PyObjC bridges the
        # facade’s @objc properties (attribute vs. method).
        sid = objc_result.valueForKey_("diagonalId")
        reason = objc_result.valueForKey_("reason")
        self.ok = bool(objc_result.valueForKey_("ok"))
        self.diagonal_id = str(sid) if sid is not None else None
        self.count = int(objc_result.valueForKey_("count"))
        self.reason = str(reason) if reason is not None else None
        self.message = str(objc_result.valueForKey_("message") or "")
        # Captured only by the diagonal-creating verbs, so `.diagonal` can hand back
        # a ready ItalifyDiagonal handle; None for every other call.
        self._layer = layer

    def __bool__(self):
        return self.ok

    def __repr__(self):
        if self.ok:
            inner = f"diagonal_id={self.diagonal_id!r}" if self.diagonal_id else f"count={self.count}"
            return f"<ItalifyResult ok {inner}>"
        return f"<ItalifyResult refused reason={self.reason!r} message={self.message!r}>"

    @property
    def diagonal(self):
        """The created diagonal as an :class:`ItalifyDiagonal` handle, or None.

        Set only for ``add_diagonal`` / ``add_diagonal_explicit`` results – the
        verbs that carry both a ``diagonal_id`` and the originating layer.
        None for every other call, success or refusal.
        """
        if self.diagonal_id is None or self._layer is None:
            return None
        return ItalifyDiagonal(self._layer, self.diagonal_id)


def _wrap(objc_result, strict_override, layer=None):
    result = ItalifyResult(objc_result, layer)
    use_strict = strict if strict_override is None else strict_override
    if use_strict and not result.ok:
        raise ItalifyError(result.reason, result.message)
    return result


def _nodes(seq):
    """Materialise a node selection (GSNodes / a GSLayer.selection) into
    a plain list PyObjC can bridge to NSArray."""
    return list(seq) if seq is not None else []


# -- Reads -------------------------------------------------------------

def diagonal_ids(layer):
    """The diagonal-id (UUID) strings tagged on ``layer``, sorted."""
    return list(_api.diagonalIdsOnLayer_(layer))


def corners(layer, diagonal_id):
    """The (up to four) corner GSNodes of ``diagonal_id``."""
    return list(_api.cornersOnLayer_diagonalId_(layer, diagonal_id))


def extras(layer, diagonal_id):
    """The non-corner member GSNodes (on- and off-curve) of ``diagonal_id``."""
    return list(_api.extrasOnLayer_diagonalId_(layer, diagonal_id))


def is_corrupted(layer, diagonal_id):
    return bool(_api.isCorruptedOnLayer_diagonalId_(layer, diagonal_id))


def is_flipped(layer, diagonal_id):
    return bool(_api.isFlippedOnLayer_diagonalId_(layer, diagonal_id))


def anchored_edge(layer, diagonal_id):
    """The anchored edge’s two corner GSNodes as a tuple, or None."""
    pair = list(_api.anchoredEdgeOnLayer_diagonalId_(layer, diagonal_id))
    return (pair[0], pair[1]) if len(pair) == 2 else None


def hinge_corners(layer, diagonal_id):
    """The hinge pair’s two corner GSNodes as a tuple, or None."""
    pair = list(_api.hingeCornersOnLayer_diagonalId_(layer, diagonal_id))
    return (pair[0], pair[1]) if len(pair) == 2 else None


def linked_nodes(layer, anchor_name):
    """The GSNodes ``anchor_name`` is linked to on ``layer``."""
    return list(_api.linkedNodesOnLayer_anchorName_(layer, anchor_name))


def linked_anchors(node):
    """The anchor names ``node`` is linked to."""
    return list(_api.linkedAnchorsForNode_(node))


def curve_extension(node):
    """The node’s effective curve-extension ratio in [0, 1]: 0.0 limits
    the curve (no extension; also what a legacy ``italify.limitCurve``
    flag in an old file reads as), 1.0 when untagged (full extension)."""
    return float(_api.curveExtensionForNode_(node))


def has_no_curve_correction(node):
    """Whether ``node`` carries the No Curve Correction flag (set on both
    on-curve endpoints of an opted-out segment)."""
    return bool(_api.hasNoCurveCorrectionForNode_(node))


def has_inktrap(node):
    """Whether ``node`` carries the Inktrap flag (set on both on-curve
    endpoints of the straight length-preserving segment)."""
    return bool(_api.hasInktrapForNode_(node))


def snap_y(node):
    """Whether ``node`` carries the Y-Snap tag (retains its y through the
    correction)."""
    return bool(_api.hasSnapYForNode_(node))


def terminal(node):
    """The segment’s Terminal override for ``node``: ``True`` (force
    terminal), ``False`` (opt out), or ``None`` (auto detection decides).
    The tag sits on both endpoints, so either identifies the segment."""
    value = _api.terminalOverrideForNode_(node)
    return None if value is None else bool(value)


def terminal_angle(node):
    """The per-terminal *angle* override on the terminal ``node`` bounds:
    a float in 0–1 that replaces the filter’s Keep terminals → Angle for
    this one terminal, or ``None`` when it follows the filter. The value
    sits on both endpoints, so either identifies the terminal."""
    value = _api.terminalAngleOverrideForNode_(node)
    return None if value is None else float(value)


def terminal_position(node):
    """The per-terminal *position* override (see :func:`terminal_angle`):
    a float in −1–2 – 0 is where the curve correction carries the cut
    (its corners at the same t), 1 where a plain slant puts it, beyond
    that range it overshoots along the adjoining segments – or ``None``
    when the terminal follows the filter."""
    value = _api.terminalPositionOverrideForNode_(node)
    return None if value is None else float(value)


# -- Diagonals -------------------------------------------------------------

def add_diagonal(layer, nodes, all_masters=False, strict=None):
    """Tag a diagonal from ``nodes`` (>=4 on-curves; corners auto-picked via
    PCA, the rest become extras). Returns a result whose ``diagonal_id`` is
    the new UUID."""
    return _wrap(_api.addDiagonalOnLayer_nodes_allMasters_(layer, _nodes(nodes), all_masters), strict, layer)


def add_diagonal_explicit(layer, corners, extras=None, all_masters=False, strict=None):
    """Tag a diagonal from an explicit four-corner set (+ optional extras)."""
    return _wrap(
        _api.addDiagonalOnLayer_corners_extras_allMasters_(layer, _nodes(corners), _nodes(extras), all_masters),
        strict,
        layer,
    )


def delete_diagonal(layer, diagonal_id, all_masters=False, strict=None):
    return _wrap(_api.deleteDiagonalOnLayer_diagonalId_allMasters_(layer, diagonal_id, all_masters), strict)


def set_flipped(layer, diagonal_id, flipped, all_masters=False, strict=None):
    return _wrap(_api.setFlippedOnLayer_diagonalId_flipped_allMasters_(layer, diagonal_id, flipped, all_masters), strict)


# -- Corner roles ------------------------------------------------------

def set_anchored_edge(layer, diagonal_id, node_a, node_b, on=True, all_masters=False, strict=None):
    return _wrap(
        _api.setAnchoredEdgeOnLayer_diagonalId_nodeA_nodeB_on_allMasters_(layer, diagonal_id, node_a, node_b, on, all_masters),
        strict,
    )


def set_hinge_corners(layer, diagonal_id, node_a, node_b, on=True, all_masters=False, strict=None):
    return _wrap(
        _api.setHingeCornersOnLayer_diagonalId_nodeA_nodeB_on_allMasters_(layer, diagonal_id, node_a, node_b, on, all_masters),
        strict,
    )


# -- Extras ------------------------------------------------------------

def add_extras(layer, diagonal_id, nodes, all_masters=False, strict=None):
    return _wrap(_api.addExtrasOnLayer_diagonalId_nodes_allMasters_(layer, diagonal_id, _nodes(nodes), all_masters), strict)


def remove_extras(layer, nodes, all_masters=False, strict=None):
    return _wrap(_api.removeExtrasOnLayer_nodes_allMasters_(layer, _nodes(nodes), all_masters), strict)


# -- Tag flags ---------------------------------------------------------

def set_curve_extension(layer, node, ratio, all_masters=False, strict=None):
    """Store a curve-extension ratio in [0, 1] on ``node``: 0 limits the
    curve (no extension – the tool’s Toggle Limit Curve), 1 removes the
    override (the default full extension). See the curve-centre control
    in the tool."""
    return _wrap(_api.setCurveExtensionOnLayer_node_ratio_allMasters_(layer, node, float(ratio), all_masters), strict)


def set_no_curve_correction(layer, node_a, node_b, on, all_masters=False, strict=None):
    return _wrap(
        _api.setNoCurveCorrectionOnLayer_nodeA_nodeB_on_allMasters_(layer, node_a, node_b, on, all_masters),
        strict,
    )


def set_inktrap(layer, node_a, node_b, on, all_masters=False, strict=None):
    """Toggle Inktrap on the straight segment between ``node_a`` and
    ``node_b`` (directly-connected, unsmooth on-curve endpoints)."""
    return _wrap(
        _api.setInktrapOnLayer_nodeA_nodeB_on_allMasters_(layer, node_a, node_b, on, all_masters),
        strict,
    )


def set_snap_y(layer, node, retain, all_masters=False, strict=None):
    """Set or remove the Y-Snap tag on ``node``: ``retain=True`` keeps its
    y through the correction, ``False`` (or ``None``) removes the tag."""
    return _wrap(
        _api.setSnapYOnLayer_node_retain_allMasters_(layer, node, bool(retain), all_masters),
        strict,
    )


def set_terminal(layer, node_a, node_b, on, all_masters=False, strict=None):
    """Set the Terminal override on the segment between ``node_a`` and
    ``node_b``: ``on=True`` forces it to be a terminal, ``False`` opts it
    out, ``None`` removes the override (back to auto)."""
    if on is None:
        return _wrap(_api.clearTerminalOnLayer_nodeA_nodeB_allMasters_(layer, node_a, node_b, all_masters), strict)
    return _wrap(
        _api.setTerminalOnLayer_nodeA_nodeB_on_allMasters_(layer, node_a, node_b, on, all_masters),
        strict,
    )


def set_terminal_angle(layer, node_a, node_b, value, all_masters=False, strict=None):
    """Give the terminal between ``node_a`` and ``node_b`` its own Keep
    terminals → Angle: ``value`` (0–1) replaces the filter’s amount for
    this terminal only; ``None`` removes the override. What the tagger’s
    diamond knob writes."""
    return _wrap(
        _api.setTerminalAngleOnLayer_nodeA_nodeB_value_allMasters_(
            layer, node_a, node_b, None if value is None else float(value), all_masters),
        strict,
    )


def set_terminal_position(layer, node_a, node_b, value, all_masters=False, strict=None):
    """Give the terminal between ``node_a`` and ``node_b`` its own Keep
    terminals → Position: ``value`` replaces the filter’s amount for this
    terminal only – 0 where the curve correction carries the cut, 1 where
    a plain slant puts it, and anything in −1–2 to overshoot either way;
    ``None`` removes the override. What the tagger’s round knob writes."""
    return _wrap(
        _api.setTerminalPositionOnLayer_nodeA_nodeB_value_allMasters_(
            layer, node_a, node_b, None if value is None else float(value), all_masters),
        strict,
    )


# -- Anchor links ------------------------------------------------------

def link_anchor(layer, anchor_name, node, all_masters=False, strict=None):
    return _wrap(_api.linkAnchorOnLayer_anchorName_node_allMasters_(layer, anchor_name, node, all_masters), strict)


def unlink_anchor(layer, anchor_name, node, all_masters=False, strict=None):
    return _wrap(_api.unlinkAnchorOnLayer_anchorName_node_allMasters_(layer, anchor_name, node, all_masters), strict)


# -- Bulk --------------------------------------------------------------

def auto_tag(layer, strict=None):
    """Run the diagonal auto-tagger on ``layer`` (active-layer only)."""
    return _wrap(_api.autoTagOnLayer_(layer), strict)


def auto_link_anchors(layer, anchor_names=None, exclude=None, all_masters=False, strict=None):
    """Auto-link anchors on ``layer``: an x/y-intersection link onto a
    curve the anchor sits on, else a link to the nearest on-curve node.
    Already-linked anchors are left alone. ``anchor_names`` restricts the
    run to the anchors matching those patterns (``None`` = every anchor);
    ``exclude`` removes the anchors matching its patterns. Patterns take
    ``*`` wildcards: ``"*top*"`` covers ``top``, ``_top``, ``topright``,
    ``_topright``. ``all_masters`` auto-links every compatible master on
    its own geometry. ``.count`` is the number of anchors linked."""
    return _wrap(
        _api.autoLinkAnchorsOnLayer_anchorNames_excludeAnchorNames_allMasters_(
            layer,
            list(anchor_names) if anchor_names else [],
            list(exclude) if exclude else [],
            all_masters,
        ),
        strict,
    )


def resolve_corrupted(layer, all_masters=False, strict=None):
    return _wrap(_api.resolveCorruptedOnLayer_allMasters_(layer, all_masters), strict)


def clear_diagonals(layer, all_masters=False, strict=None):
    return _wrap(_api.clearDiagonalsOnLayer_allMasters_(layer, all_masters), strict)


def clear_tags(layer, all_masters=False, strict=None):
    return _wrap(_api.clearTagsOnLayer_allMasters_(layer, all_masters), strict)


def clear_anchor_links(layer, all_masters=False, strict=None):
    return _wrap(_api.clearAnchorLinksOnLayer_allMasters_(layer, all_masters), strict)


def clear(layer, diagonals=True, tags=True, anchor_links=True, all_masters=False, strict=None):
    """Clear a chosen set of kinds in one undo group."""
    return _wrap(_api.clearOnLayer_diagonals_tags_anchorLinks_allMasters_(layer, diagonals, tags, anchor_links, all_masters), strict)


def propagate_diagonals(layer, diagonal_ids=None, strict=None):
    """Propagate diagonals to compatible masters. ``diagonal_ids=None`` = all,
    else only those ids."""
    return _wrap(_api.propagateDiagonalsFromLayer_diagonalIds_(layer, list(diagonal_ids) if diagonal_ids else []), strict)


def propagate_tags(layer, nodes=None, strict=None):
    """Propagate tag flags. ``nodes=None`` = all (mirrors the source);
    a node list propagates only those nodes’ flags, additively."""
    return _wrap(_api.propagateTagsFromLayer_nodes_(layer, _nodes(nodes)), strict)


def propagate_anchor_links(layer, anchor_names=None, strict=None):
    """Propagate anchor links. ``anchor_names=None`` = all, else only
    those anchors, additively."""
    return _wrap(_api.propagateAnchorLinksFromLayer_anchorNames_(layer, list(anchor_names) if anchor_names else []), strict)


def propagate(layer, diagonals=True, tags=True, anchor_links=True, strict=None):
    """Propagate a chosen set of kinds (whole layer) in one undo group."""
    return _wrap(_api.propagateFromLayer_diagonals_tags_anchorLinks_(layer, diagonals, tags, anchor_links), strict)


# -- Cross-layer transfer ----------------------------------------------

def transfer(source_layer, target_layer, diagonals=True, tags=True,
             anchor_links=True, replace=True, strict=None):
    """Copy Italify metadata from ``source_layer`` onto ``target_layer`` –
    the only verb that crosses fonts.

    The two layers must *index-map* (same path / node counts, same
    on-/off-curve at each index); the call refuses with ``noCompatibleMasters``
    otherwise. ``replace=True`` (the default) mirrors the source exactly for
    the chosen kinds, clearing whatever the source doesn’t carry;
    ``replace=False`` is additive (the target keeps marks the source lacks).
    Unlike :func:`propagate`, which only reaches compatible masters of the
    *same* glyph, this takes an explicit target layer, so source and target
    may live in different fonts. ``.count`` is the number of kinds applied.

        import italify
        src = Glyphs.fonts[0]; dst = Glyphs.fonts[1]
        sid, did = src.masters[0].id, dst.masters[0].id
        for g in src.glyphs:
            t = dst.glyphs[g.name]
            if t:
                italify.transfer(g.layers[sid], t.layers[did])
    """
    return _wrap(
        _api.transferFromLayer_toLayer_diagonals_tags_anchorLinks_replace_(
            source_layer, target_layer, diagonals, tags, anchor_links, replace),
        strict,
    )


# -- Parameters --------------------------------------------------------

#: ``correct()`` keyword → the filter’s parameter name (the scoped-params
#: sub-key, which is also the ``Filter`` custom-parameter argument name).
_PARAMETER_KEYS = {
    "curve_correction": "curveCorrection",
    "diagonal_correction": "diagonalCorrection",
    "stem_compensation": "stemCompensation",
    "keep_terminal_angle": "keepTerminalAngle",
    "keep_terminal_position": "keepTerminalPosition",
}


def resolved_parameters(layer, fallback=None):
    """The filter parameters in effect for ``layer``, as a dict keyed like
    :func:`correct`’s keyword arguments.

    Each parameter resolves independently through the per-scope cascade
    the filter dialog’s *Save for:* popup writes – layer → glyph → group →
    master → font – exactly as the filter resolves it. A parameter no
    scope sets takes ``fallback[name]`` when given, else the filter
    dialog’s current app-wide value.

    The result splats straight into :func:`correct`, which runs a layer
    with its own scoped parameters::

        import italify
        for layer in Glyphs.font.selectedLayers:
            italify.correct(layer, angle=layer.italicAngle,
                            **italify.resolved_parameters(layer))

    A read: it writes nothing and is never refused."""
    base = {}
    for name, value in (fallback or {}).items():
        if name not in _PARAMETER_KEYS:
            raise TypeError(
                f"unknown parameter {name!r} (expected one of {', '.join(_PARAMETER_KEYS)})")
        base[_PARAMETER_KEYS[name]] = float(value)
    raw = _api.resolvedParametersForLayer_fallback_(layer, base)
    return {name: float(raw[key]) for name, key in _PARAMETER_KEYS.items()}


# -- Correction --------------------------------------------------------

def correct(layer, angle, curve_correction=1.0, diagonal_correction=1.0,
            stem_compensation=0.0, keep_terminal_angle=0.0,
            keep_terminal_position=1.0,
            tagged_diagonals_only=True, strict=None):
    """Run the full Italify pass on an **upright** ``layer``: shear-aware
    outline correction driven by the layer’s diagonal tags, then the slant
    itself – the same pass the filter’s Apply button and export run,
    with the parameters given explicitly instead of read from the dialog
    or the per-scope ``userData`` cascade.

    The one verb that moves geometry (everything else in this module
    authors metadata). The whole pass is one undo step. To run a layer
    with the parameters saved for it, splat :func:`resolved_parameters`
    into the call.

    *Parameters* mirror the filter dialog: ``angle`` in degrees;
    ``curve_correction`` / ``diagonal_correction`` / ``stem_compensation``
    are 0.0–1.0 strengths; ``keep_terminal_angle`` /
    ``keep_terminal_position`` (0.0–1.0) are the dialog’s two Keep
    terminals sliders – how much of a terminal’s upright cut angle
    survives, and whether the cut stays where a plain slant puts it (1.0,
    the default) or rides along its adjoining curves with the curve
    correction (0.0). A terminal with its own :func:`set_terminal_angle`
    / :func:`set_terminal_position` value ignores the respective amount;
    and
    ``tagged_diagonals_only`` restricts diagonal correction to
    tagged diagonals. The other advanced settings (flatten
    intersections, terminal auto-detection, …) are not parameters:
    the pass follows the app’s *Settings → Advanced*, as the dialog does.

        import italify
        layer = Glyphs.font.selectedLayers[0]
        italify.correct(layer, angle=10, curve_correction=0.6,
                        diagonal_correction=0.85, stem_compensation=0)

    Refuses with ``masterNotActivated`` on a license-enforced build when
    the layer’s master hasn’t been activated with a credit."""
    return _wrap(
        _api.correctLayer_angle_curveCorrectionFactor_diagonalCorrectionFactor_stemCompensationFactor_keepTerminalAngle_keepTerminalPosition_taggedDiagonalsOnly_(
            layer, angle, curve_correction, diagonal_correction,
            stem_compensation, keep_terminal_angle, keep_terminal_position,
            tagged_diagonals_only),
        strict,
    )


# -- Diagonal objects ------------------------------------------------------

class ItalifyDiagonal:
    """A live handle to one diagonal, identified by ``(layer, diagonal_id)``.

    Reads are **properties** (``corners``, ``extras``, ``is_corrupted``,
    ``is_flipped``, ``anchored_edge``, ``hinge_corners``); writes are
    **methods** that return an :class:`ItalifyResult` and keep the module
    verbs’ ``all_masters`` / ``strict`` knobs. Every accessor is the
    module-level verb of the same name with ``(layer, diagonal_id)`` already
    bound, so the handle adds no behaviour of its own – it only spares you
    threading the pair through each call.

    It never caches: a property is read from the engine on every access,
    so a diagonal deleted out from under the handle reports empty ``corners``
    and ``exists == False`` rather than going stale.

    Build one with :func:`diagonal` / :func:`diagonals`, or read ``.diagonal`` off a
    successful :func:`add_diagonal` result.
    """

    __slots__ = ("_layer", "_id")

    def __init__(self, layer, diagonal_id):
        self._layer = layer
        self._id = str(diagonal_id)

    # -- Identity --

    @property
    def id(self):
        """The diagonal’s UUID string."""
        return self._id

    @property
    def layer(self):
        """The ``GSLayer`` this handle is bound to."""
        return self._layer

    @property
    def exists(self):
        """True while this diagonal is still tagged on the layer."""
        return self._id in diagonal_ids(self._layer)

    def __eq__(self, other):
        # Two handles match when they name the same diagonal on the same layer.
        return (isinstance(other, ItalifyDiagonal)
                and self._id == other._id
                and self._layer is other._layer)

    def __hash__(self):
        # Consistent with __eq__ (equal handles share a UUID diagonal id) while
        # not leaning on GSLayer’s own hashing semantics.
        return hash(self._id)

    def __repr__(self):
        return f"<ItalifyDiagonal {self._id}>"

    # -- Reads (properties; each is the module verb of the same name) --

    @property
    def corners(self):
        """The (up to four) corner ``GSNode``s of the diagonal."""
        return corners(self._layer, self._id)

    @property
    def extras(self):
        """The non-corner member nodes (on- and off-curve)."""
        return extras(self._layer, self._id)

    @property
    def is_corrupted(self):
        """True if the diagonal’s tags no longer form a valid frame."""
        return is_corrupted(self._layer, self._id)

    @property
    def is_flipped(self):
        """True if the diagonal’s axis is flipped."""
        return is_flipped(self._layer, self._id)

    @property
    def anchored_edge(self):
        """The anchored edge’s two corner nodes as a tuple, or None."""
        return anchored_edge(self._layer, self._id)

    @property
    def hinge_corners(self):
        """The hinge pair’s two corner nodes as a tuple, or None."""
        return hinge_corners(self._layer, self._id)

    # -- Writes (methods; return ItalifyResult, like the free verbs) --

    def set_flipped(self, flipped, all_masters=False, strict=None):
        """Set the diagonal’s flip-axis flag."""
        return set_flipped(self._layer, self._id, flipped,
                           all_masters=all_masters, strict=strict)

    def set_anchored_edge(self, node_a, node_b, on=True, all_masters=False, strict=None):
        """Pin (or, with ``on=False``, clear) the anchored edge formed by
        two adjacent corners of the diagonal."""
        return set_anchored_edge(self._layer, self._id, node_a, node_b,
                                 on=on, all_masters=all_masters, strict=strict)

    def set_hinge_corners(self, node_a, node_b, on=True, all_masters=False, strict=None):
        """Pin (or clear) two diagonally-opposed corners as a hinge."""
        return set_hinge_corners(self._layer, self._id, node_a, node_b,
                                 on=on, all_masters=all_masters, strict=strict)

    def add_extras(self, nodes, all_masters=False, strict=None):
        """Add ``nodes`` as extras of this diagonal."""
        return add_extras(self._layer, self._id, nodes,
                          all_masters=all_masters, strict=strict)

    def remove_extras(self, nodes, all_masters=False, strict=None):
        """Remove ``nodes`` from whichever diagonal owns them (this diagonal when
        they are this diagonal’s extras)."""
        return remove_extras(self._layer, nodes,
                             all_masters=all_masters, strict=strict)

    def propagate(self, strict=None):
        """Mirror this diagonal onto every compatible master of the glyph.

        Sugar for :func:`propagate_diagonals` restricted to this diagonal’s id;
        it reaches compatible masters of the *same* glyph (use
        :func:`transfer` to cross fonts). ``propagate_diagonals`` is
        inherently all-masters and has no ``all_masters`` knob, so
        neither does this."""
        return propagate_diagonals(self._layer, [self._id], strict=strict)

    def delete(self, all_masters=False, strict=None):
        """Remove this diagonal’s tags."""
        return delete_diagonal(self._layer, self._id,
                           all_masters=all_masters, strict=strict)


def diagonal(layer, diagonal_id):
    """An :class:`ItalifyDiagonal` handle for ``diagonal_id`` on ``layer``.

    A handle, not a snapshot – the diagonal need not exist yet (check
    ``.exists``); the handle reads through to the engine on every access.
    """
    return ItalifyDiagonal(layer, diagonal_id)


def diagonals(layer):
    """Every tagged diagonal on ``layer`` as a list of :class:`ItalifyDiagonal`."""
    return [ItalifyDiagonal(layer, sid) for sid in diagonal_ids(layer)]
