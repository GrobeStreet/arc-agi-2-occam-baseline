"""ARC representation-expansion grammar v3.

This module extends the small diagnostic DSL in ``dsl.py`` with generic ARC
transformations registered before the v3 training-holdout benchmark. It remains a
deterministic, CPU-only enumerator. Every candidate must reproduce all fitted
demonstrations exactly before it is allowed to predict a test grid.
"""
from __future__ import annotations

from collections import Counter
from itertools import product
from typing import Any, Callable

import numpy as np
from scipy import ndimage

import dsl as v2


ArrayFn = Callable[[np.ndarray], np.ndarray | None]


def _ok(value: Any) -> bool:
    return isinstance(value, np.ndarray) and value.ndim == 2 and value.size > 0


def _bg(grid: np.ndarray) -> int:
    values, counts = np.unique(grid, return_counts=True)
    return int(values[np.argmax(counts)])


def _dominant_non_bg(grid: np.ndarray) -> int | None:
    background = _bg(grid)
    values = grid[grid != background]
    if values.size == 0:
        return None
    colors, counts = np.unique(values, return_counts=True)
    return int(colors[np.argmax(counts)])


def _bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    coordinates = np.argwhere(mask)
    if not coordinates.size:
        return None
    row0, col0 = coordinates.min(axis=0)
    row1, col1 = coordinates.max(axis=0) + 1
    return int(row0), int(row1), int(col0), int(col1)


def _crop_mask(grid: np.ndarray, mask: np.ndarray) -> np.ndarray | None:
    box = _bbox(mask)
    if box is None:
        return None
    row0, row1, col0, col1 = box
    return grid[row0:row1, col0:col1].copy()


def _gravity(grid: np.ndarray, direction: str) -> np.ndarray:
    background = _bg(grid)
    output = np.full_like(grid, background)
    height, width = grid.shape
    if direction in {"left", "right"}:
        for row in range(height):
            values = grid[row, grid[row] != background]
            if direction == "left":
                output[row, : len(values)] = values
            elif len(values):
                output[row, width - len(values) :] = values
    else:
        for col in range(width):
            values = grid[grid[:, col] != background, col]
            if direction == "up":
                output[: len(values), col] = values
            elif len(values):
                output[height - len(values) :, col] = values
    return output


def _compress_rows(grid: np.ndarray) -> np.ndarray | None:
    background = _bg(grid)
    keep = np.any(grid != background, axis=1)
    return grid[keep].copy() if np.any(keep) else None


def _compress_cols(grid: np.ndarray) -> np.ndarray | None:
    background = _bg(grid)
    keep = np.any(grid != background, axis=0)
    return grid[:, keep].copy() if np.any(keep) else None


def _compress_both(grid: np.ndarray) -> np.ndarray | None:
    rows = _compress_rows(grid)
    return _compress_cols(rows) if rows is not None else None


def _strip_uniform_border(grid: np.ndarray) -> np.ndarray | None:
    if min(grid.shape) <= 2:
        return None
    border = np.concatenate([grid[0], grid[-1], grid[1:-1, 0], grid[1:-1, -1]])
    if border.size and np.all(border == border[0]):
        return grid[1:-1, 1:-1].copy()
    return None


def _symmetry(grid: np.ndarray, mode: str) -> np.ndarray | None:
    background = _bg(grid)
    if mode == "horizontal":
        other = np.fliplr(grid)
    elif mode == "vertical":
        other = np.flipud(grid)
    elif mode == "rotational":
        other = np.rot90(grid, 2)
    else:
        return None
    output = grid.copy()
    output[output == background] = other[output == background]
    return output


def _connect_same(grid: np.ndarray, axis: str) -> np.ndarray:
    background = _bg(grid)
    output = grid.copy()
    if axis in {"horizontal", "both"}:
        for row in range(grid.shape[0]):
            for color in np.unique(grid[row]):
                if color == background:
                    continue
                positions = np.flatnonzero(grid[row] == color)
                if len(positions) >= 2:
                    output[row, positions.min() : positions.max() + 1] = color
    if axis in {"vertical", "both"}:
        for col in range(grid.shape[1]):
            for color in np.unique(grid[:, col]):
                if color == background:
                    continue
                positions = np.flatnonzero(grid[:, col] == color)
                if len(positions) >= 2:
                    output[positions.min() : positions.max() + 1, col] = color
    return output


def _extend_markers(grid: np.ndarray, axis: str) -> np.ndarray:
    background = _bg(grid)
    output = grid.copy()
    if axis in {"horizontal", "both"}:
        for row in range(grid.shape[0]):
            values = grid[row][grid[row] != background]
            colors = np.unique(values)
            if len(colors) == 1:
                output[row, :] = colors[0]
    if axis in {"vertical", "both"}:
        for col in range(grid.shape[1]):
            values = grid[:, col][grid[:, col] != background]
            colors = np.unique(values)
            if len(colors) == 1:
                output[:, col] = colors[0]
    return output


def _components(grid: np.ndarray, connectivity: int) -> list[dict[str, Any]]:
    background = _bg(grid)
    structure = ndimage.generate_binary_structure(2, 1 if connectivity == 4 else 2)
    labels, count = ndimage.label(grid != background, structure=structure)
    records: list[dict[str, Any]] = []
    for label in range(1, count + 1):
        mask = labels == label
        box = _bbox(mask)
        if box is None:
            continue
        row0, row1, col0, col1 = box
        colors, color_counts = np.unique(grid[mask], return_counts=True)
        records.append(
            {
                "mask": mask,
                "size": int(mask.sum()),
                "bbox": box,
                "area": int((row1 - row0) * (col1 - col0)),
                "density": float(mask.sum() / ((row1 - row0) * (col1 - col0))),
                "dominant": int(colors[np.argmax(color_counts)]),
                "row0": row0,
                "col0": col0,
            }
        )
    return records


def _select_component(
    grid: np.ndarray, connectivity: int, selector: str
) -> dict[str, Any] | None:
    records = _components(grid, connectivity)
    if not records:
        return None
    if selector == "largest":
        return max(records, key=lambda record: (record["size"], -record["row0"], -record["col0"]))
    if selector == "smallest":
        return min(records, key=lambda record: (record["size"], record["row0"], record["col0"]))
    if selector in {"uniqueSmall", "uniqueLarge"}:
        frequencies = Counter(record["size"] for record in records)
        unique = [record for record in records if frequencies[record["size"]] == 1]
        if not unique:
            return None
        return (
            min(unique, key=lambda record: (record["size"], record["row0"], record["col0"]))
            if selector == "uniqueSmall"
            else max(unique, key=lambda record: (record["size"], -record["row0"], -record["col0"]))
        )
    if selector == "densest":
        return max(records, key=lambda record: (record["density"], record["size"]))
    if selector == "sparsest":
        return min(records, key=lambda record: (record["density"], -record["size"]))
    return None


def _component_factory(connectivity: int, selector: str, action: str) -> ArrayFn:
    def transform(grid: np.ndarray) -> np.ndarray | None:
        record = _select_component(grid, connectivity, selector)
        if record is None:
            return None
        background = _bg(grid)
        mask = record["mask"]
        if action == "keep":
            output = np.full_like(grid, background)
            output[mask] = grid[mask]
            return output
        if action == "remove":
            output = grid.copy()
            output[mask] = background
            return output
        if action == "crop":
            return _crop_mask(grid, mask)
        return None

    return transform


def _keep_color_factory(color: int, crop: bool = False, remove: bool = False) -> ArrayFn:
    def transform(grid: np.ndarray) -> np.ndarray | None:
        mask = grid == color
        if not np.any(mask):
            return None
        if remove:
            output = grid.copy()
            output[mask] = _bg(grid)
            return output
        output = np.full_like(grid, _bg(grid))
        output[mask] = color
        return _crop_mask(output, mask) if crop else output

    return transform


def _mask_color_factory(color: int) -> ArrayFn:
    def transform(grid: np.ndarray) -> np.ndarray | None:
        background = _bg(grid)
        if not np.any(grid != background):
            return None
        return np.where(grid != background, color, background).astype(grid.dtype)

    return transform


def _fill_holes_factory(color: int) -> ArrayFn:
    def transform(grid: np.ndarray) -> np.ndarray | None:
        background = _bg(grid)
        mask = grid != background
        if not np.any(mask):
            return None
        filled = ndimage.binary_fill_holes(mask)
        output = grid.copy()
        output[filled & ~mask] = color
        return output

    return transform


def _bbox_factory(color: int, outline: bool) -> ArrayFn:
    def transform(grid: np.ndarray) -> np.ndarray | None:
        background = _bg(grid)
        box = _bbox(grid != background)
        if box is None:
            return None
        row0, row1, col0, col1 = box
        output = grid.copy()
        if outline:
            output[row0, col0:col1] = color
            output[row1 - 1, col0:col1] = color
            output[row0:row1, col0] = color
            output[row0:row1, col1 - 1] = color
        else:
            output[row0:row1, col0:col1] = color
        return output

    return transform


def _recolor_components_factory(color: int, connectivity: int) -> ArrayFn:
    def transform(grid: np.ndarray) -> np.ndarray | None:
        records = _components(grid, connectivity)
        if not records:
            return None
        output = grid.copy()
        for record in records:
            output[record["mask"]] = color
        return output

    return transform


def _split_panels(grid: np.ndarray) -> tuple[np.ndarray, np.ndarray] | None:
    height, width = grid.shape
    background = _bg(grid)
    candidates: list[tuple[int, float, np.ndarray, np.ndarray]] = []
    for row in range(1, height - 1):
        if np.all(grid[row] == grid[row, 0]):
            top, bottom = grid[:row], grid[row + 1 :]
            if top.shape == bottom.shape and top.size:
                non_bg = int(grid[row, 0] != background)
                candidates.append((-non_bg, abs(row - height / 2), top, bottom))
    for col in range(1, width - 1):
        if np.all(grid[:, col] == grid[0, col]):
            left, right = grid[:, :col], grid[:, col + 1 :]
            if left.shape == right.shape and left.size:
                non_bg = int(grid[0, col] != background)
                candidates.append((-non_bg, abs(col - width / 2), left, right))
    if not candidates:
        if width % 2 == 0:
            return grid[:, : width // 2], grid[:, width // 2 :]
        if height % 2 == 0:
            return grid[: height // 2], grid[height // 2 :]
        return None
    candidates.sort(key=lambda item: (item[0], item[1]))
    return candidates[0][2].copy(), candidates[0][3].copy()


def _panel_factory(mode: str, fill: int | None = None) -> ArrayFn:
    def transform(grid: np.ndarray) -> np.ndarray | None:
        panels = _split_panels(grid)
        if panels is None:
            return None
        first, second = panels
        background = _bg(grid)
        if mode == "first":
            return first.copy()
        if mode == "second":
            return second.copy()
        first_mask = first != background
        second_mask = second != background
        if mode == "overlayFirst":
            return np.where(first_mask, first, second).astype(grid.dtype)
        if mode == "overlaySecond":
            return np.where(second_mask, second, first).astype(grid.dtype)
        if mode == "xorPreserve":
            return np.where(first_mask & ~second_mask, first, np.where(second_mask & ~first_mask, second, background)).astype(grid.dtype)
        if mode == "andPreserve":
            return np.where(first_mask & second_mask, first, background).astype(grid.dtype)
        if mode == "diffFirst":
            return np.where(first_mask & ~second_mask, first, background).astype(grid.dtype)
        if mode == "diffSecond":
            return np.where(second_mask & ~first_mask, second, background).astype(grid.dtype)
        if mode in {"AND", "OR", "XOR"} and fill is not None:
            if mode == "AND":
                mask = first_mask & second_mask
            elif mode == "OR":
                mask = first_mask | second_mask
            else:
                mask = first_mask ^ second_mask
            return np.where(mask, fill, background).astype(grid.dtype)
        return None

    return transform


def _count_factory(connectivity: int, color: int, mode: str) -> ArrayFn:
    def transform(grid: np.ndarray) -> np.ndarray | None:
        count = len(_components(grid, connectivity))
        if count <= 0 or count > 30:
            return None
        background = _bg(grid)
        if mode == "row":
            return np.full((1, count), color, dtype=grid.dtype)
        if mode == "col":
            return np.full((count, 1), color, dtype=grid.dtype)
        if mode == "square":
            return np.full((count, count), color, dtype=grid.dtype)
        if mode == "diag":
            output = np.full((count, count), background, dtype=grid.dtype)
            np.fill_diagonal(output, color)
            return output
        return None

    return transform


def _pack_components_factory(
    connectivity: int, axis: str, sort_mode: str, gap: int
) -> ArrayFn:
    def transform(grid: np.ndarray) -> np.ndarray | None:
        records = _components(grid, connectivity)
        if len(records) < 2:
            return None
        background = _bg(grid)
        if sort_mode == "position":
            records.sort(key=lambda record: (record["row0"], record["col0"]))
        elif sort_mode == "sizeAsc":
            records.sort(key=lambda record: (record["size"], record["row0"], record["col0"]))
        else:
            records.sort(key=lambda record: (-record["size"], record["row0"], record["col0"]))
        pieces: list[np.ndarray] = []
        for record in records:
            row0, row1, col0, col1 = record["bbox"]
            piece = np.full((row1 - row0, col1 - col0), background, dtype=grid.dtype)
            mask = record["mask"][row0:row1, col0:col1]
            source = grid[row0:row1, col0:col1]
            piece[mask] = source[mask]
            pieces.append(piece)
        if axis == "horizontal":
            height = max(piece.shape[0] for piece in pieces)
            width = sum(piece.shape[1] for piece in pieces) + gap * (len(pieces) - 1)
            output = np.full((height, width), background, dtype=grid.dtype)
            cursor = 0
            for piece in pieces:
                output[: piece.shape[0], cursor : cursor + piece.shape[1]] = piece
                cursor += piece.shape[1] + gap
            return output
        width = max(piece.shape[1] for piece in pieces)
        height = sum(piece.shape[0] for piece in pieces) + gap * (len(pieces) - 1)
        output = np.full((height, width), background, dtype=grid.dtype)
        cursor = 0
        for piece in pieces:
            output[cursor : cursor + piece.shape[0], : piece.shape[1]] = piece
            cursor += piece.shape[0] + gap
        return output

    return transform


def _block_mode_reduce(grid: np.ndarray, ratio: tuple[int, int]) -> np.ndarray | None:
    row_factor, col_factor = ratio
    if grid.shape[0] % row_factor or grid.shape[1] % col_factor:
        return None
    output = np.empty((grid.shape[0] // row_factor, grid.shape[1] // col_factor), dtype=grid.dtype)
    for row in range(output.shape[0]):
        for col in range(output.shape[1]):
            block = grid[
                row * row_factor : (row + 1) * row_factor,
                col * col_factor : (col + 1) * col_factor,
            ]
            values, counts = np.unique(block, return_counts=True)
            output[row, col] = values[np.argmax(counts)]
    return output


def _compose(first: ArrayFn, second: ArrayFn) -> ArrayFn:
    def transform(grid: np.ndarray) -> np.ndarray | None:
        intermediate = first(grid)
        return second(intermediate) if _ok(intermediate) else None

    return transform


def build_programs(train_pairs: list[tuple[np.ndarray, np.ndarray]]) -> list[tuple[str, ArrayFn]]:
    programs: list[tuple[str, ArrayFn]] = list(v2.build_programs(train_pairs))

    core: dict[str, ArrayFn] = {
        "gravityUp": lambda grid: _gravity(grid, "up"),
        "gravityLeft": lambda grid: _gravity(grid, "left"),
        "gravityRight": lambda grid: _gravity(grid, "right"),
        "compressRows": _compress_rows,
        "compressCols": _compress_cols,
        "compressBoth": _compress_both,
        "stripUniformBorder": _strip_uniform_border,
        "symHorizontal": lambda grid: _symmetry(grid, "horizontal"),
        "symVertical": lambda grid: _symmetry(grid, "vertical"),
        "symRotational": lambda grid: _symmetry(grid, "rotational"),
        "connectSameH": lambda grid: _connect_same(grid, "horizontal"),
        "connectSameV": lambda grid: _connect_same(grid, "vertical"),
        "connectSameBoth": lambda grid: _connect_same(grid, "both"),
        "extendMarkersH": lambda grid: _extend_markers(grid, "horizontal"),
        "extendMarkersV": lambda grid: _extend_markers(grid, "vertical"),
        "extendMarkersBoth": lambda grid: _extend_markers(grid, "both"),
        "panelFirst": _panel_factory("first"),
        "panelSecond": _panel_factory("second"),
        "panelOverlayFirst": _panel_factory("overlayFirst"),
        "panelOverlaySecond": _panel_factory("overlaySecond"),
        "panelXorPreserve": _panel_factory("xorPreserve"),
        "panelAndPreserve": _panel_factory("andPreserve"),
        "panelDiffFirst": _panel_factory("diffFirst"),
        "panelDiffSecond": _panel_factory("diffSecond"),
    }

    for connectivity in (4, 8):
        for selector in ("largest", "smallest", "uniqueSmall", "uniqueLarge", "densest", "sparsest"):
            for action in ("keep", "crop", "remove"):
                core[f"cc{connectivity}_{action}_{selector}"] = _component_factory(
                    connectivity, selector, action
                )
        for axis in ("horizontal", "vertical"):
            for sort_mode in ("position", "sizeAsc", "sizeDesc"):
                for gap in (0, 1):
                    core[f"pack{connectivity}_{axis}_{sort_mode}_gap{gap}"] = _pack_components_factory(
                        connectivity, axis, sort_mode, gap
                    )

    programs.extend(core.items())

    for color in range(1, 10):
        programs.extend(
            [
                (f"keepColor:{color}", _keep_color_factory(color)),
                (f"cropColor:{color}", _keep_color_factory(color, crop=True)),
                (f"removeColor:{color}", _keep_color_factory(color, remove=True)),
                (f"maskNonBg:{color}", _mask_color_factory(color)),
                (f"fillHoles:{color}", _fill_holes_factory(color)),
                (f"fillBBox:{color}", _bbox_factory(color, outline=False)),
                (f"outlineBBox:{color}", _bbox_factory(color, outline=True)),
                (f"recolorCC4:{color}", _recolor_components_factory(color, 4)),
                (f"recolorCC8:{color}", _recolor_components_factory(color, 8)),
                (f"panelAND:{color}", _panel_factory("AND", color)),
                (f"panelOR:{color}", _panel_factory("OR", color)),
                (f"panelXOR:{color}", _panel_factory("XOR", color)),
            ]
        )
        for connectivity in (4, 8):
            for mode in ("row", "col", "square", "diag"):
                programs.append(
                    (
                        f"countCC{connectivity}_{mode}:{color}",
                        _count_factory(connectivity, color, mode),
                    )
                )

    dominant = _dominant_non_bg(train_pairs[0][0]) if train_pairs else None
    if dominant is not None:
        programs.append(("maskDominant", _mask_color_factory(dominant)))

    ratio = v2.derive_ratio(train_pairs, "reduce")
    if ratio and ratio != (1, 1):
        programs.append(
            (
                f"reduceMode{ratio}",
                lambda grid, reduction=ratio: _block_mode_reduce(grid, reduction),
            )
        )

    # Limited geometry compositions around parameter-free operations. Fixed-color
    # programs are deliberately excluded to keep the search finite and auditable.
    composable_names = {
        name
        for name in core
        if not name.startswith("pack") and "extendMarkers" not in name
    }
    for geom_name, geom_fn in v2.GEOM.items():
        if geom_name == "id":
            continue
        for name in sorted(composable_names):
            fn = core[name]
            programs.append((f"{name}∘{geom_name}", _compose(geom_fn, fn)))
            programs.append((f"{geom_name}∘{name}", _compose(fn, geom_fn)))

    # Deduplicate exact names while retaining deterministic first occurrence.
    seen: set[str] = set()
    unique: list[tuple[str, ArrayFn]] = []
    for name, fn in programs:
        if name in seen:
            continue
        seen.add(name)
        unique.append((name, fn))
    return unique


def passes_demos(fn: ArrayFn, pairs: list[tuple[np.ndarray, np.ndarray]]) -> bool:
    return v2.passes_demos(fn, pairs)


def complexity(name: str) -> int:
    depth = name.count("∘") + 1
    parameterized = int(
        any(
            token in name
            for token in (
                ":",
                "color",
                "Color",
                "count",
                "fill",
                "outline",
                "recolor",
                "pack",
                "reduceMode",
            )
        )
    )
    structural = int(name.startswith("cc") or name.startswith("panel"))
    return depth + parameterized + structural
