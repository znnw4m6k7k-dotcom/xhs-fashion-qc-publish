#!/usr/bin/env python3
"""Validate an offline Xiaohongshu fashion run manifest.

This script never calls RedBeacon, a browser, a social platform, or an image model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


SCHEMA = "xhs-fashion-qc-publish/v2"


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"manifest not found: {path}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("manifest root must be an object")
    return data


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def string_list(value: Any) -> bool:
    return isinstance(value, list) and all(nonempty_text(item) for item in value)


def validate(args: argparse.Namespace, data: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if data.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA!r}")
    if not nonempty_text(data.get("run_id")):
        errors.append("run_id is required")

    account = data.get("account")
    if not isinstance(account, dict) or not isinstance(account.get("id"), int) or account["id"] <= 0:
        errors.append("account.id must be a positive integer")
    elif args.expected_account_id is not None and account["id"] != args.expected_account_id:
        errors.append(f"account.id must be {args.expected_account_id}, got {account['id']}")

    product = data.get("product")
    if not isinstance(product, dict) or not nonempty_text(product.get("name")):
        errors.append("product.name is required")
    refs = product.get("source_refs") if isinstance(product, dict) else None
    if not isinstance(refs, list) or not refs:
        errors.append("product.source_refs must contain at least one authoritative source path")
    else:
        for index, ref in enumerate(refs, start=1):
            if not nonempty_text(ref) or not Path(ref).is_file():
                errors.append(f"product.source_refs[{index}] is not a readable local file")

    truth_card = product.get("truth_card") if isinstance(product, dict) else None
    if not isinstance(truth_card, dict):
        errors.append("product.truth_card is required")
    else:
        for key in ("verified", "unknowns", "avoid"):
            if not string_list(truth_card.get(key)):
                errors.append(f"product.truth_card.{key} must be a list of strings")
        if not truth_card.get("verified"):
            errors.append("product.truth_card.verified must contain at least one fact")

    selling_points = data.get("selling_points")
    if args.require_selling_points:
        provided = selling_points.get("provided") if isinstance(selling_points, dict) else None
        if not string_list(provided) or not provided:
            errors.append("selling_points.provided must contain at least one user-provided selling point")
    elif selling_points is not None and not isinstance(selling_points, dict):
        errors.append("selling_points must be an object when present")

    generation = data.get("generation")
    if not isinstance(generation, dict) or generation.get("provider") != "native-image-generation":
        errors.append("generation.provider must be 'native-image-generation'")
    if not isinstance(generation, dict) or generation.get("redbeacon_fallback_used") is not False:
        errors.append("generation.redbeacon_fallback_used must be false")
    if not isinstance(generation, dict) or generation.get("platform_generation_points_used") != 0:
        errors.append("generation.platform_generation_points_used must be 0")
    if isinstance(generation, dict):
        if generation.get("count") != args.expected_count:
            errors.append(f"generation.count must be {args.expected_count}")
        if generation.get("aspect_ratio") != "3:4":
            errors.append("generation.aspect_ratio must be '3:4'")
        roles = generation.get("series_roles")
        expected_roles = ["street"] * 5 + ["mirror_selfie"]
        if roles != expected_roles:
            errors.append("generation.series_roles must be five street images followed by one mirror_selfie")

    qc = data.get("qc")
    items = qc.get("items") if isinstance(qc, dict) else None
    if not isinstance(qc, dict) or not nonempty_text(qc.get("reviewer")):
        errors.append("qc.reviewer is required")
    if not isinstance(items, list) or len(items) != args.expected_count:
        actual = len(items) if isinstance(items, list) else 0
        errors.append(f"qc.items must contain exactly {args.expected_count} items, got {actual}")
        items = []

    seen_paths: set[Path] = set()
    seen_digests: set[str] = set()
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            errors.append(f"qc.items[{index}] must be an object")
            continue
        if item.get("grade") != "A":
            errors.append(f"qc.items[{index}] must be grade A")
        path_value = item.get("path")
        if not nonempty_text(path_value):
            errors.append(f"qc.items[{index}].path is required")
            continue
        path = Path(path_value)
        if not path.is_file() or path.is_symlink():
            errors.append(f"qc.items[{index}].path must be a regular local file, not a symlink")
            continue
        resolved = path.resolve()
        if resolved in seen_paths:
            errors.append(f"qc.items[{index}].path duplicates another accepted image")
        seen_paths.add(resolved)
        file_digest = digest(path)
        if file_digest in seen_digests:
            errors.append(f"qc.items[{index}] duplicates another accepted image by SHA-256")
        seen_digests.add(file_digest)

    if args.require_copy:
        copy = data.get("copy")
        tags = copy.get("tags") if isinstance(copy, dict) else None
        if not isinstance(copy, dict) or not nonempty_text(copy.get("title")):
            errors.append("copy.title is required for handoff")
        if not isinstance(copy, dict) or not nonempty_text(copy.get("body")):
            errors.append("copy.body is required for handoff")
        if not string_list(tags) or not tags:
            errors.append("copy.tags must be a non-empty list of strings for handoff")
        if isinstance(copy, dict) and copy.get("source") != "product-truth-and-user-selling-points":
            errors.append("copy.source must be product-truth-and-user-selling-points")

    if args.require_redbeacon:
        redbeacon = data.get("redbeacon")
        if not isinstance(redbeacon, dict):
            errors.append("redbeacon object is required for handoff")
        else:
            rb_account_id = redbeacon.get("account_id")
            if not isinstance(rb_account_id, int) or rb_account_id <= 0:
                errors.append("redbeacon.account_id must be a positive integer")
            elif args.expected_account_id is not None and rb_account_id != args.expected_account_id:
                errors.append(f"redbeacon.account_id must be {args.expected_account_id}, got {rb_account_id}")
            if redbeacon.get("entry_mode") not in {"self-add-review", "host-work-package"}:
                errors.append("redbeacon.entry_mode must be self-add-review or host-work-package")
            if not nonempty_text(redbeacon.get("review_record_id")):
                errors.append("redbeacon.review_record_id is required after review handoff")
            if redbeacon.get("generation_route_used") is not False:
                errors.append("redbeacon.generation_route_used must be false")
            if redbeacon.get("platform_generation_points_used") != 0:
                errors.append("redbeacon.platform_generation_points_used must be 0")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Xiaohongshu fashion run manifest.")
    parser.add_argument("--manifest", required=True, type=Path, help="UTF-8 JSON run manifest")
    parser.add_argument("--expected-count", type=int, default=6, help="required number of A-grade images")
    parser.add_argument("--expected-account-id", type=int, help="optional account guard")
    parser.add_argument("--require-selling-points", action="store_true", help="require user-provided selling points")
    parser.add_argument("--require-copy", action="store_true", help="require title, body, tags, and copy source")
    parser.add_argument("--require-redbeacon", action="store_true", help="require explicit self-add or work-package review state")
    args = parser.parse_args()

    if args.expected_count < 1:
        parser.error("--expected-count must be at least 1")

    try:
        data = load_manifest(args.manifest)
        errors = validate(args, data)
    except ValueError as exc:
        errors = [str(exc)]

    result = {
        "ok": not errors,
        "state": "READY_FOR_REDBEACON_HANDOFF" if not errors and not args.require_redbeacon else (
            "READY_FOR_REDBEACON_REVIEW" if not errors else "BLOCKED"
        ),
        "errors": errors,
        "manifest": str(args.manifest),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
