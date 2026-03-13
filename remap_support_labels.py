#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path
from types import ModuleType


def _install_cgi_compat():
    """Provide the minimal cgi.escape API expected by older ete3 code."""
    if "cgi" in sys.modules:
        return
    cgi_module = ModuleType("cgi")
    cgi_module.escape = html.escape
    sys.modules["cgi"] = cgi_module


def _load_tree(tree_text: str):
    _install_cgi_compat()
    from ete3 import Tree

    return Tree(tree_text, format=1)


def _canonical_split(descendant_leaves, all_leaves):
    descendant_side = frozenset(descendant_leaves)
    other_side = frozenset(all_leaves - descendant_side)
    if not descendant_side or not other_side:
        return None

    left = tuple(sorted(descendant_side))
    right = tuple(sorted(other_side))
    if len(left) < len(right):
        return left
    if len(right) < len(left):
        return right
    return left if left <= right else right


def _build_split_to_label_map(tree):
    all_leaves = frozenset(tree.get_leaf_names())
    split_map = {}
    collisions = []

    for node in tree.traverse("postorder"):
        if node.is_root():
            continue
        label = (node.name or "").strip()
        if not label:
            continue
        split_key = _canonical_split(node.get_leaf_names(), all_leaves)
        if split_key is None:
            continue
        existing = split_map.get(split_key)
        if existing is not None and existing != label:
            collisions.append((split_key, existing, label))
            continue
        split_map[split_key] = label

    return split_map, collisions


def _resolve_root_child_duplicates(tree, split_map, *, suppress_duplicates: bool):
    if not suppress_duplicates:
        return
    if len(tree.children) != 2:
        return

    children_by_split = {}
    all_leaves = frozenset(tree.get_leaf_names())
    for child in tree.children:
        split_key = _canonical_split(child.get_leaf_names(), all_leaves)
        if split_key is None:
            continue
        children_by_split.setdefault(split_key, []).append(child)

    for split_key, children in children_by_split.items():
        if len(children) < 2:
            continue
        keep_child = min(children, key=lambda node: (len(node.get_leaf_names()), tuple(sorted(node.get_leaf_names()))))
        for child in children:
            child.name = split_map.get(split_key, "") if child is keep_child else ""


def remap_support_labels(original_tree_text: str, display_tree_text: str, *, suppress_root_duplicate_labels: bool = True):
    original_tree = _load_tree(original_tree_text)
    display_tree = _load_tree(display_tree_text)

    original_leaves = frozenset(original_tree.get_leaf_names())
    display_leaves = frozenset(display_tree.get_leaf_names())
    if original_leaves != display_leaves:
        missing_in_display = sorted(original_leaves - display_leaves)
        missing_in_original = sorted(display_leaves - original_leaves)
        raise ValueError(
            "Leaf sets do not match between original and display trees.\n"
            f"Missing in display: {missing_in_display}\n"
            f"Missing in original: {missing_in_original}"
        )

    split_map, collisions = _build_split_to_label_map(original_tree)
    all_leaves = frozenset(display_tree.get_leaf_names())
    mapped_count = 0
    unmatched_count = 0

    for node in display_tree.traverse("postorder"):
        if node.is_root():
            node.name = ""
            continue
        split_key = _canonical_split(node.get_leaf_names(), all_leaves)
        if split_key is None:
            node.name = ""
            continue
        label = split_map.get(split_key, "")
        if label:
            mapped_count += 1
        else:
            unmatched_count += 1
        node.name = label

    _resolve_root_child_duplicates(
        display_tree,
        split_map,
        suppress_duplicates=suppress_root_duplicate_labels,
    )

    return display_tree.write(format=1), {
        "split_count": len(split_map),
        "mapped_nodes": mapped_count,
        "unmatched_nodes": unmatched_count,
        "collisions": collisions,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Remap support labels from an original IQ-TREE treefile onto a display tree using leaf bipartitions."
    )
    parser.add_argument("--original-tree", required=True, help="Original IQ-TREE treefile with support labels")
    parser.add_argument("--display-tree", required=True, help="Display tree (for example midpoint-rooted) to overwrite")
    parser.add_argument("--output", help="Path to write the relabeled display tree. Defaults to stdout.")
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Do not print summary information to stderr.",
    )
    parser.add_argument(
        "--keep-root-duplicate-labels",
        action="store_true",
        help="Keep the same support label on both root-adjacent branches, similar to FigTree.",
    )
    args = parser.parse_args()

    original_tree_text = Path(args.original_tree).read_text(encoding="utf-8").strip()
    display_tree_text = Path(args.display_tree).read_text(encoding="utf-8").strip()
    remapped_text, stats = remap_support_labels(
        original_tree_text,
        display_tree_text,
        suppress_root_duplicate_labels=not args.keep_root_duplicate_labels,
    )

    if args.output:
        Path(args.output).write_text(remapped_text + "\n", encoding="utf-8")
    else:
        sys.stdout.write(remapped_text + "\n")

    if not args.quiet:
        print(
            f"split_count={stats['split_count']} mapped_nodes={stats['mapped_nodes']} unmatched_nodes={stats['unmatched_nodes']}",
            file=sys.stderr,
        )
        if stats["collisions"]:
            print(f"collisions={len(stats['collisions'])}", file=sys.stderr)
            for split_key, first_label, second_label in stats["collisions"]:
                print(
                    f"collision split={split_key} kept={first_label!r} ignored={second_label!r}",
                    file=sys.stderr,
                )


if __name__ == "__main__":
    main()
