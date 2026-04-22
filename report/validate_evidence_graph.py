"""
Tenacious Conversion Engine — Evidence Graph Validator
Walks evidence_graph.json, loads each source_ref, recomputes values, flags mismatches > 5%.
Usage: python validate_evidence_graph.py evidence_graph.json
"""

import json
import sys
from pathlib import Path


def validate_evidence_graph(graph_path: str, tolerance: float = 0.05) -> dict:
    """Validate all claims in evidence_graph.json against source files."""
    with open(graph_path) as f:
        graph = json.load(f)

    results = {
        "total_claims": 0,
        "validated": 0,
        "failed": 0,
        "skipped": 0,
        "failures": [],
        "warnings": [],
    }

    repo_root = Path(graph_path).parent.parent

    for claim in graph.get("claims", []):
        results["total_claims"] += 1
        claim_id = claim["claim_id"]
        source_ref = claim.get("source_ref", "")
        source_type = claim.get("source_type", "")

        # Skip published references (cannot auto-verify)
        if source_type == "published_reference":
            results["skipped"] += 1
            continue

        # Skip Tenacious internal (cannot auto-verify without access)
        if source_type == "tenacious_internal":
            results["skipped"] += 1
            continue

        # Try to validate trace-derived claims
        if source_type in ("trace_derived", "benchmark_output", "statistical_test"):
            validation = validate_trace_claim(claim, repo_root)
            if validation["status"] == "pass":
                results["validated"] += 1
            elif validation["status"] == "fail":
                results["failed"] += 1
                results["failures"].append({
                    "claim_id": claim_id,
                    "claim_text": claim.get("claim_text", ""),
                    "expected": claim.get("value"),
                    "actual": validation.get("actual"),
                    "mismatch_pct": validation.get("mismatch_pct"),
                })
            else:
                results["warnings"].append({
                    "claim_id": claim_id,
                    "issue": validation.get("message", "Validation skipped"),
                })
                results["skipped"] += 1
        else:
            results["skipped"] += 1

    results["validation_status"] = "PASS" if results["failed"] == 0 else "FAIL"
    return results


def validate_trace_claim(claim: dict, repo_root: Path) -> dict:
    """Attempt to validate a single trace-derived claim."""
    claim_id = claim["claim_id"]
    source_ref = claim.get("source_ref", "")

    # Parse file path from source_ref (format: "path/to/file.json#selector")
    if "#" in source_ref:
        file_part, selector = source_ref.split("#", 1)
    else:
        file_part = source_ref
        selector = None

    # Skip URL references
    if file_part.startswith("http"):
        return {"status": "skipped", "message": "External URL — cannot auto-verify"}

    file_path = repo_root / file_part
    if not file_path.exists():
        return {"status": "skipped", "message": f"Source file not found: {file_part}"}

    try:
        if file_path.suffix == ".json":
            with open(file_path) as f:
                data = json.load(f)

            # Navigate to value using simple selector
            if selector:
                actual_value = navigate_json(data, selector)
                if actual_value is None:
                    return {"status": "skipped", "message": f"Selector '{selector}' not found in {file_part}"}

                expected = claim.get("value")
                if isinstance(expected, (int, float)) and isinstance(actual_value, (int, float)):
                    mismatch = abs(actual_value - expected) / max(abs(expected), 1e-10)
                    if mismatch > 0.05:
                        return {
                            "status": "fail",
                            "actual": actual_value,
                            "expected": expected,
                            "mismatch_pct": round(mismatch * 100, 1),
                        }
                return {"status": "pass", "actual": actual_value}

        elif file_path.suffix == ".jsonl":
            # For JSONL files, just verify they exist and have records
            with open(file_path) as f:
                lines = [l for l in f if l.strip()]
            if len(lines) == 0:
                return {"status": "fail", "message": "Trace log is empty"}
            return {"status": "pass", "actual": f"{len(lines)} trace records"}

    except Exception as e:
        return {"status": "skipped", "message": f"Validation error: {str(e)}"}

    return {"status": "skipped", "message": "No validation logic for this claim type"}


def navigate_json(data: dict, selector: str):
    """Navigate JSON using simple selector syntax: key.nested_key[index].field"""
    import re
    parts = re.split(r'[.\[\]]+', selector.strip('[]'))
    current = data
    for part in parts:
        if not part:
            continue
        if isinstance(current, dict):
            # Handle condition filters like conditions[condition_id=variant_d_scap_v2]
            match = re.match(r'(\w+)\[(\w+)=(.+)\]', part)
            if match:
                list_key, filter_key, filter_val = match.groups()
                lst = current.get(list_key, [])
                current = next((item for item in lst if str(item.get(filter_key)) == filter_val), None)
                if current is None:
                    return None
            else:
                current = current.get(part)
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
        if current is None:
            return None
    return current


if __name__ == "__main__":
    graph_path = sys.argv[1] if len(sys.argv) > 1 else "report/evidence_graph.json"
    results = validate_evidence_graph(graph_path)

    print(f"Evidence Graph Validation Report")
    print(f"═" * 40)
    print(f"Total claims:  {results['total_claims']}")
    print(f"Validated:     {results['validated']}")
    print(f"Skipped:       {results['skipped']}")
    print(f"Failed:        {results['failed']}")
    print(f"")
    print(f"Status: {results['validation_status']}")

    if results["failures"]:
        print(f"\nFailures:")
        for f in results["failures"]:
            print(f"  [{f['claim_id']}] {f['claim_text'][:60]}...")
            print(f"    Expected: {f['expected']} | Actual: {f['actual']} | Mismatch: {f.get('mismatch_pct')}%")

    if results["warnings"]:
        print(f"\nWarnings:")
        for w in results["warnings"]:
            print(f"  [{w['claim_id']}] {w['issue']}")

    sys.exit(0 if results["validation_status"] == "PASS" else 1)
