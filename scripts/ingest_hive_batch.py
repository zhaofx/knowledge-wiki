#!/usr/bin/env python3
"""Batch-ingest Hive tables via `bytedcli hive detail/ddl/lineage`.

Reads the qualified-name list from raw/tables/search_*.json, dispatches
detail/DDL/lineage in batches of `--batch` tables, and writes:

  - raw/tables/by_table/{db}.{table}.json      (normalized metadata)
  - raw/tables/by_table/{db}.{table}.raw.json  (bytedcli full response)
  - raw/sql/sql/{db}.{table}.ddl.sql
  - raw/sql/sql_index.json                     (idempotent per (kind,path))
  - raw/lineage/by_guid/{guid}.json            (full lineage snapshot)
  - raw/lineage/table_lineage_edges.json       (dedup by from_guid+to_guid+edge_kind)
  - raw/lineage/_pending.json                  (per-table retry history)
  - raw/tables/hive_tables_meta.json           (batch index)

Failures on any single stage are logged to `_pending.json` and do not
abort the run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "knowledge"
RAW_TABLES = KB / "raw" / "tables"
RAW_TABLES_BY = RAW_TABLES / "by_table"
RAW_SQL = KB / "raw" / "sql" / "sql"
RAW_SQL_INDEX = KB / "raw" / "sql" / "sql_index.json"
RAW_LINEAGE = KB / "raw" / "lineage"
RAW_LINEAGE_BY_GUID = RAW_LINEAGE / "by_guid"
RAW_LINEAGE_EDGES = RAW_LINEAGE / "table_lineage_edges.json"
RAW_LINEAGE_PENDING = RAW_LINEAGE / "_pending.json"
META_INDEX = RAW_TABLES / "hive_tables_meta.json"

ASSET_URL_TMPL = (
    "https://data.bytedance.net/coral/datamap/detail"
    "?groupName=default&qualifiedName=HiveTable%3A%2F%2F%2F{db}%2F{table}%400"
)
LINEAGE_URL_TMPL = "https://data.bytedance.net/coral/lineage?guid={guid}"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_of(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class TableRef:
    db: str
    table: str

    @property
    def qn(self) -> str:
        return f"{self.db}.{self.table}"


def run_bytedcli_json(args: list[str], timeout: int = 120) -> tuple[bool, Any, str]:
    """Return (ok, parsed_json_or_none, stderr_or_message)."""
    cmd = ["bytedcli", "--json", *args]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired as exc:
        return False, None, f"timeout after {timeout}s: {exc}"
    if proc.returncode != 0:
        return False, None, proc.stderr.strip() or proc.stdout.strip()
    stdout = proc.stdout.strip()
    if not stdout:
        return False, None, "empty stdout"
    try:
        return True, json.loads(stdout), ""
    except json.JSONDecodeError as exc:
        return False, None, f"json decode failed: {exc}; first 200 chars={stdout[:200]!r}"


def run_bytedcli_text(args: list[str], timeout: int = 120) -> tuple[bool, str, str]:
    """For commands that emit non-JSON output (e.g. `hive ddl` prints SQL)."""
    cmd = ["bytedcli", *args]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired as exc:
        return False, "", f"timeout after {timeout}s: {exc}"
    if proc.returncode != 0:
        return False, "", proc.stderr.strip() or proc.stdout.strip()
    return True, proc.stdout, ""


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default


def dump_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def infer_layer(table: str) -> str:
    prefix = table.split("_", 1)[0].lower()
    return {
        "ads": "ADS", "dws": "DWS", "dwd": "DWD", "dim": "DIM",
        "ods": "ODS", "app": "APP", "dm": "DM", "t": "T", "bmq": "BMQ",
    }.get(prefix, "Other")


def normalize_detail(ref: TableRef, raw: dict[str, Any], region: str, source_url: str) -> dict[str, Any]:
    """Convert `bytedcli hive detail --json` payload to our schema."""
    data = raw.get("data") or {}
    attrs = data.get("attributes") or {}
    guid = data.get("guid") or attrs.get("guid")
    columns_raw = attrs.get("columns") or []
    partitions_raw = attrs.get("partitions") or []

    def col(c: dict[str, Any], is_partition: bool) -> dict[str, Any]:
        cattrs = c.get("attributes") or c
        return {
            "name": cattrs.get("name") or c.get("name"),
            "type": cattrs.get("type") or c.get("type"),
            "comment": cattrs.get("comment") or c.get("comment"),
            "is_partition": is_partition,
            "is_nullable": cattrs.get("isNullable", cattrs.get("nullable", True)),
        }

    columns = [col(c, False) for c in columns_raw]
    partitions = [col(c, True) for c in partitions_raw]

    latest_partition = attrs.get("latestPartitionName") or attrs.get("latestPartition")
    dorado_ids = []
    for producer in (attrs.get("producerTasks") or []):
        pid = producer.get("taskId") or producer.get("id")
        if pid:
            dorado_ids.append(str(pid))

    return {
        "db": ref.db,
        "table": ref.table,
        "qualified_name": ref.qn,
        "qualified_name_dataleap": attrs.get("qualifiedName"),
        "guid": guid,
        "region": region,
        "owner": attrs.get("owner"),
        "department": attrs.get("departmentPath") or attrs.get("department"),
        "layer": infer_layer(ref.table),
        "storage_format": attrs.get("storageFormat"),
        "table_type": attrs.get("tableType"),
        "location": attrs.get("location"),
        "latest_partition": latest_partition,
        "producer_dorado_task_ids": dorado_ids,
        "description": attrs.get("description") or attrs.get("comment"),
        "partitions": partitions,
        "columns_count": len(columns),
        "columns": columns,
        "asset_url": ASSET_URL_TMPL.format(db=ref.db, table=ref.table),
        "source_tool": "bytedcli hive detail",
        "source_url": source_url,
        "captured_at": utc_iso(),
        "raw_response_path": f"raw/tables/by_table/{ref.qn}.raw.json",
    }


def collapse_lineage_edges(
    ref: TableRef,
    center_guid: str,
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Fold HiveTable→DoradoTask→HiveTable into direct Hive→Hive edges.

    Only edges whose endpoints are HiveTable are retained.
    """
    data = payload.get("data") or {}
    relations = data.get("relations") or []
    nodes = data.get("nodes") or data.get("guidEntityMap") or {}
    if isinstance(nodes, list):
        nodes = {n.get("guid"): n for n in nodes if isinstance(n, dict)}

    def node_qn(guid: str) -> str | None:
        node = nodes.get(guid) or {}
        attrs = node.get("attributes") or {}
        parent = attrs.get("parentName") or node.get("parentName")
        name = attrs.get("name") or node.get("name")
        if parent and name:
            return f"{parent}.{name}"
        qn = attrs.get("qualifiedName") or node.get("qualifiedName")
        if isinstance(qn, str) and "://" in qn:
            _, _, rest = qn.partition("://")
            rest = rest.strip("/")
            if "@" in rest:
                rest = rest.split("@", 1)[0]
            parts = [p for p in rest.split("/") if p]
            if len(parts) >= 2:
                return f"{parts[0]}.{parts[1]}"
        return None

    def is_hive(guid: str) -> bool:
        node = nodes.get(guid) or {}
        return (node.get("typeName") or node.get("type")) == "HiveTable"

    def is_task(guid: str) -> bool:
        node = nodes.get(guid) or {}
        return (node.get("typeName") or node.get("type")) == "DoradoTask"

    # Build task-fan-in/out maps.
    task_inputs: dict[str, list[str]] = {}
    task_outputs: dict[str, list[str]] = {}
    for rel in relations:
        src = rel.get("fromEntityId") or rel.get("from") or rel.get("source")
        dst = rel.get("toEntityId") or rel.get("to") or rel.get("target")
        if not src or not dst:
            continue
        if is_hive(src) and is_task(dst):
            task_inputs.setdefault(dst, []).append(src)
        elif is_task(src) and is_hive(dst):
            task_outputs.setdefault(src, []).append(dst)

    edges: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for task_guid, inputs in task_inputs.items():
        for out_guid in task_outputs.get(task_guid, []):
            for in_guid in inputs:
                if in_guid == out_guid:
                    continue
                key = (in_guid, out_guid)
                if key in seen:
                    continue
                seen.add(key)
                task_node = nodes.get(task_guid) or {}
                task_attrs = task_node.get("attributes") or {}
                edge = {
                    "from_qn": node_qn(in_guid),
                    "from_guid": in_guid,
                    "to_qn": node_qn(out_guid),
                    "to_guid": out_guid,
                    "direction": (
                        "downstream" if in_guid == center_guid
                        else "upstream" if out_guid == center_guid
                        else "peer"
                    ),
                    "hop": 1,
                    "edge_kind": "table_lineage",
                    "via_task_guid": task_guid,
                    "via_task_name": task_attrs.get("name") or task_attrs.get("displayText"),
                    "source_tool": "bytedcli hive lineage",
                    "source_url": LINEAGE_URL_TMPL.format(guid=center_guid),
                    "captured_at": utc_iso(),
                    "captured_for": ref.qn,
                }
                edges.append(edge)
    return edges


def load_edges_index() -> tuple[list[dict[str, Any]], dict[tuple[str, str, str], int]]:
    raw = load_json(RAW_LINEAGE_EDGES, [])
    if isinstance(raw, dict) and "edges" in raw:
        edges = raw["edges"]
    elif isinstance(raw, list):
        edges = raw
    else:
        edges = []
    idx: dict[tuple[str, str, str], int] = {}
    for i, e in enumerate(edges):
        key = (e.get("from_guid") or e.get("from_qn"),
               e.get("to_guid") or e.get("to_qn"),
               e.get("edge_kind"))
        idx[key] = i
    return edges, idx


def upsert_edges(edges: list[dict[str, Any]], new_edges: list[dict[str, Any]]) -> tuple[int, int]:
    edges_idx: dict[tuple[str, str, str], int] = {}
    for i, e in enumerate(edges):
        key = (e.get("from_guid") or e.get("from_qn"),
               e.get("to_guid") or e.get("to_qn"),
               e.get("edge_kind"))
        edges_idx[key] = i
    added, updated = 0, 0
    for edge in new_edges:
        key = (edge.get("from_guid") or edge.get("from_qn"),
               edge.get("to_guid") or edge.get("to_qn"),
               edge.get("edge_kind"))
        if key in edges_idx:
            existing = edges[edges_idx[key]]
            existing["captured_at"] = edge["captured_at"]
            if edge.get("via_task_guid"):
                existing.setdefault("via_task_guid", edge["via_task_guid"])
                existing.setdefault("via_task_name", edge.get("via_task_name"))
            updated += 1
        else:
            edges.append(edge)
            edges_idx[key] = len(edges) - 1
            added += 1
    return added, updated


def update_sql_index(ref: TableRef, sha: str, line_count: int) -> None:
    idx = load_json(RAW_SQL_INDEX, [])
    if not isinstance(idx, list):
        idx = []
    rel = f"raw/sql/sql/{ref.qn}.ddl.sql"
    row = {
        "kind": "ddl",
        "path": rel,
        "db": ref.db,
        "table": ref.table,
        "produces_tables": [ref.qn],
        "sha256": sha,
        "line_count": line_count,
        "source_tool": "bytedcli hive ddl",
        "captured_at": utc_iso(),
    }
    replaced = False
    for i, r in enumerate(idx):
        if r.get("path") == rel:
            idx[i] = row
            replaced = True
            break
    if not replaced:
        idx.append(row)
    dump_json(RAW_SQL_INDEX, idx)


def update_meta_index(ref: TableRef, guid: str | None, owner: str | None) -> None:
    meta = load_json(META_INDEX, {"generated_at": utc_iso(), "tables": []})
    if not isinstance(meta, dict):
        meta = {"generated_at": utc_iso(), "tables": []}
    tables = meta.setdefault("tables", [])
    rel = f"raw/tables/by_table/{ref.qn}.json"
    row = {
        "qualified_name": ref.qn,
        "guid": guid,
        "owner": owner,
        "path": rel,
    }
    replaced = False
    for i, r in enumerate(tables):
        if r.get("qualified_name") == ref.qn:
            tables[i] = row
            replaced = True
            break
    if not replaced:
        tables.append(row)
    meta["generated_at"] = utc_iso()
    dump_json(META_INDEX, meta)


def append_pending(ref: TableRef, stage: str, message: str) -> None:
    pending = load_json(RAW_LINEAGE_PENDING, {"pending": []})
    if not isinstance(pending, dict):
        pending = {"pending": []}
    pending.setdefault("pending", []).append({
        "qualified_name": ref.qn,
        "stage": stage,
        "message": message,
        "captured_at": utc_iso(),
    })
    dump_json(RAW_LINEAGE_PENDING, pending)


def ingest_one(ref: TableRef, region: str, lineage_depth: int) -> dict[str, Any]:
    result = {"qn": ref.qn, "detail": False, "ddl": False, "lineage": False,
              "edges_added": 0, "edges_updated": 0, "errors": []}
    detail_url = ASSET_URL_TMPL.format(db=ref.db, table=ref.table)

    # ---- detail ----
    ok, payload, err = run_bytedcli_json(["hive", "detail", ref.db, ref.table, "-r", region])
    if not ok:
        result["errors"].append(f"detail: {err}")
        append_pending(ref, "detail", err)
        return result
    normalized = normalize_detail(ref, payload, region, detail_url)
    dump_json(RAW_TABLES_BY / f"{ref.qn}.raw.json", payload)
    dump_json(RAW_TABLES_BY / f"{ref.qn}.json", normalized)
    guid = normalized.get("guid")
    update_meta_index(ref, guid, normalized.get("owner"))
    result["detail"] = True

    # ---- ddl ----
    ok, sql_text, err = run_bytedcli_text(["hive", "ddl", ref.db, ref.table, "-r", region])
    if not ok:
        result["errors"].append(f"ddl: {err}")
        append_pending(ref, "ddl", err)
    else:
        header = (
            "-- source_tool: bytedcli hive ddl\n"
            f"-- source_url:  {detail_url}\n"
            f"-- captured_at: {utc_iso()}\n"
            "-- kind:        ddl\n"
        )
        body = sql_text if sql_text.endswith("\n") else sql_text + "\n"
        full = header + body
        path = RAW_SQL / f"{ref.qn}.ddl.sql"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(full, encoding="utf-8")
        update_sql_index(ref, sha256_of(full), full.count("\n"))
        result["ddl"] = True

    # ---- lineage ----
    if not guid:
        msg = "missing guid, cannot fetch lineage"
        result["errors"].append(f"lineage: {msg}")
        append_pending(ref, "lineage", msg)
        return result
    ok, payload, err = run_bytedcli_json(["hive", "lineage", guid, "-r", region, "-d", str(lineage_depth)], timeout=180)
    if not ok:
        result["errors"].append(f"lineage: {err}")
        append_pending(ref, "lineage", err)
        return result
    dump_json(RAW_LINEAGE_BY_GUID / f"{guid}.json", payload)
    new_edges = collapse_lineage_edges(ref, guid, payload)
    edges, _ = load_edges_index()
    added, updated = upsert_edges(edges, new_edges)
    dump_json(RAW_LINEAGE_EDGES, edges)
    result["lineage"] = True
    result["edges_added"] = added
    result["edges_updated"] = updated
    return result


def chunks(seq: list, size: int) -> Iterable[list]:
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def load_manifest(path: Path, dry_limit: int | None) -> list[TableRef]:
    payload = load_json(path, None)
    if not payload:
        raise SystemExit(f"manifest {path} not found or empty")
    refs = [TableRef(db=t["db"], table=t["table"]) for t in payload["tables"]]
    return refs[:dry_limit] if dry_limit else refs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(RAW_TABLES / "search_tcs_ai_resources_20260707.json"))
    parser.add_argument("--batch", type=int, default=10)
    parser.add_argument("--region", default="cn")
    parser.add_argument("--lineage-depth", type=int, default=1)
    parser.add_argument("--start", type=int, default=0, help="0-based table index to start from")
    parser.add_argument("--limit", type=int, default=0, help="max tables in this run (0 = all)")
    parser.add_argument("--skip-existing", action="store_true", help="skip tables whose by_table/*.json already exists")
    args = parser.parse_args()

    refs = load_manifest(Path(args.manifest), None)
    if args.start:
        refs = refs[args.start:]
    if args.limit:
        refs = refs[:args.limit]

    if args.skip_existing:
        refs = [r for r in refs if not (RAW_TABLES_BY / f"{r.qn}.json").exists()]

    print(f"[plan] {len(refs)} tables to ingest, batch={args.batch}, region={args.region}, depth={args.lineage_depth}")
    stats = {"total": len(refs), "success": 0, "partial": 0, "failed": 0,
             "edges_added": 0, "edges_updated": 0}
    started = time.time()
    for batch_no, batch in enumerate(chunks(refs, args.batch), start=1):
        print(f"\n=== batch {batch_no} ({len(batch)} tables) ===")
        for ref in batch:
            t0 = time.time()
            r = ingest_one(ref, args.region, args.lineage_depth)
            dt = time.time() - t0
            if r["detail"] and r["ddl"] and r["lineage"]:
                stats["success"] += 1
                status = "OK"
            elif r["detail"]:
                stats["partial"] += 1
                status = "PARTIAL"
            else:
                stats["failed"] += 1
                status = "FAIL"
            stats["edges_added"] += r["edges_added"]
            stats["edges_updated"] += r["edges_updated"]
            print(f"  [{status:7s}] {ref.qn} ({dt:.1f}s) edges +{r['edges_added']}/{r['edges_updated']}"
                  + (f"  errors={r['errors']}" if r["errors"] else ""))
        elapsed = time.time() - started
        print(f"[batch {batch_no}] cumulative success={stats['success']} partial={stats['partial']} failed={stats['failed']} elapsed={elapsed:.1f}s")

    total = time.time() - started
    print("\n=== summary ===")
    print(json.dumps(stats, indent=2))
    print(f"elapsed {total:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
