"""CLI Tool for DACN D.0 Benchmark: Case Inspection, Evaluation, and Report Export.

Commands:
  list    : List labeled evaluation cases with category/action filters.
  view    : Display detailed inspection view of a specific case by ID.
  stats   : Show summary statistics of labeled benchmark data.
  eval    : Run evaluation on Agent and calculate detailed metrics.
  export  : Export comprehensive evaluation reports in JSON, Markdown, HTML, and CSV.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

# Ensure repository root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from evaluation.dataset_manager import DatasetManager
from evaluation.evaluate_agent import (
    baseline_d0_agent,
    evaluate_case,
    load_ember_validator,
)
from evaluation.metrics import MetricsCalculator

REPORTS_DIR = Path(__file__).resolve().parent / "reports"


def format_table(headers: List[str], rows: List[List[str]]) -> str:
    """Formats rows into an ASCII terminal table."""
    widths = [len(h) for h in headers]
    for row in rows:
        for idx, col in enumerate(row):
            widths[idx] = max(widths[idx], len(str(col)))

    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    header_str = "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"

    lines = [sep, header_str, sep]
    for row in rows:
        line_str = "| " + " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(row)) + " |"
        lines.append(line_str)
    lines.append(sep)
    return "\n".join(lines)


def cmd_list(args: argparse.Namespace) -> None:
    dm = DatasetManager()
    cases = dm.list_cases(
        category=args.category,
        action_type=args.action,
        search=args.search,
        is_mock=True if args.mock_only else None,
    )

    if not cases:
        print("No cases found matching the criteria.")
        return

    headers = ["Case ID", "Category", "Name", "Expected Action", "Mock"]
    rows = []
    for c in cases:
        act = c.get("expected_action", {})
        act_str = act.get("action_type", "")
        if act.get("tool_id"):
            act_str += f" ({act.get('tool_id')})"
        rows.append([
            c.get("case_id", ""),
            c.get("category", ""),
            c.get("name", "")[:35],
            act_str,
            "YES" if c.get("is_mock") else "NO",
        ])

    print(f"\n[DACN D.0 Benchmark] Labeled Evaluation Cases ({len(cases)} items):")
    print(format_table(headers, rows))


def cmd_view(args: argparse.Namespace) -> None:
    dm = DatasetManager()
    case = dm.get_case(args.case_id)
    if not case:
        print(f"Error: Case ID '{args.case_id}' not found.")
        sys.exit(1)

    print("\n" + "=" * 76)
    print(f" CASE INSPECTION: {case['case_id']} - {case['name']}")
    print("=" * 76)
    print(f"Category       : {case.get('category')}")
    print(f"Is Mock Data   : {case.get('is_mock')} (Marked test fixture)")
    print(f"Description    : {case.get('description')}")
    print("-" * 76)
    print("CASE STATE:")
    cs = case.get("case_state", {})
    print(f"  - Workflow Phase     : {cs.get('workflow_phase')}")
    print(f"  - Revision           : {cs.get('revision')}")
    print(f"  - Reputation Status  : {cs.get('reputation_status')}")
    tref = cs.get("target_ref", {})
    print(f"  - Target Kind        : {tref.get('kind')}")
    print(f"  - Identity Strength  : {tref.get('identity_strength')}")
    print(f"  - Observed Details   : {json.dumps(tref.get('observed', {}))}")
    print(f"  - Verified Digest    : {json.dumps(tref.get('verified_digest'))}")
    print("-" * 76)
    print("EVIDENCE COLLECTED:")
    evidence = case.get("evidence", [])
    if not evidence:
        print("  (None collected yet)")
    else:
        for idx, ev in enumerate(evidence, 1):
            print(f"  [{idx}] Facet: {ev.get('facet')} | Status: {ev.get('status')} | Trust: {ev.get('trust_level')}")
            print(f"      Origin: {ev.get('content_origin')} | Coverage: {ev.get('coverage')}")
            if ev.get("value") is not None:
                val_str = json.dumps(ev.get("value"))
                if len(val_str) > 80:
                    val_str = val_str[:80] + "..."
                print(f"      Value: {val_str}")
            if ev.get("error"):
                print(f"      Error: {ev.get('error')}")
    print("-" * 76)
    print("ALLOWED TOOLS (POLICY):")
    allowed = case.get("allowed_tools", [])
    print(f"  {allowed if allowed else 'None (Empty policy)'}")
    print("-" * 76)
    print("EXPECTED NEXT ACTION:")
    act = case.get("expected_action", {})
    print(f"  - Action Type        : {act.get('action_type')}")
    if act.get("tool_id"):
        print(f"  - Tool ID            : {act.get('tool_id')}")
        print(f"  - Arguments          : {json.dumps(act.get('arguments', {}))}")
        print(f"  - Budget             : {json.dumps(act.get('budget', {}))}")
    if act.get("approval_request"):
        print(f"  - Approval Request   : {json.dumps(act.get('approval_request'))}")
    if act.get("stop_reason"):
        print(f"  - Stop Reason        : {act.get('stop_reason')}")
    print("-" * 76)
    print("WORKFLOW RATIONALE (D.0):")
    print(f"  {case.get('reason')}")
    print("=" * 76 + "\n")


def cmd_stats(args: argparse.Namespace) -> None:
    dm = DatasetManager()
    stats = dm.get_statistics()

    print("\n" + "=" * 70)
    print("      DACN D.0 BENCHMARK LABELED DATASET STATISTICS")
    print("=" * 70)
    print(f"Total Labeled Cases    : {stats['total_cases']}")
    print(f"Mock Data Percentage   : {stats['mock_percentage']}% ({stats['mock_cases']} cases marked is_mock)")
    print(f"Total Evidence Facets  : {stats['total_evidence_facets']} (avg {stats['avg_evidence_per_case']}/case)")
    print("-" * 70)

    print("\n[1] Distribution by Category:")
    for cat, count in sorted(stats["categories"].items()):
        pct = (count / stats["total_cases"] * 100) if stats["total_cases"] else 0
        print(f"  - {cat:<22}: {count:>2} cases ({pct:5.1f}%)")

    print("\n[2] Distribution by Workflow Phase:")
    for phase, count in sorted(stats["workflow_phases"].items()):
        print(f"  - {phase:<22}: {count:>2} cases")

    print("\n[3] Distribution by Expected Action:")
    for act, count in sorted(stats["actions"].items()):
        print(f"  - {act:<22}: {count:>2} cases")

    print("\n[4] Distribution by Evidence Origin & Trust:")
    for origin, count in sorted(stats["evidence_origins"].items()):
        print(f"  - Origin '{origin}': {count}")
    for trust, count in sorted(stats["trust_levels"].items()):
        print(f"  - Trust '{trust}': {count}")
    print("=" * 70 + "\n")


def evaluate_all(dataset_path: Optional[Path] = None) -> MetricsCalculator:
    dm = DatasetManager(dataset_path=dataset_path)
    calc = MetricsCalculator()
    ember_validator = load_ember_validator()

    for case in dm.list_cases():
        agent_action = baseline_d0_agent(case)
        passed, issues = evaluate_case(case, agent_action, ember_validator)
        calc.record_case_result(case, agent_action, passed, issues)

    return calc


def cmd_eval(args: argparse.Namespace) -> None:
    calc = evaluate_all(args.dataset)
    summary = calc.compute_summary()
    meta = summary["metadata"]
    sec = summary["security_and_compliance"]
    act = summary["action_classification"]
    cats = summary["category_breakdown"]

    print("\n" + "=" * 76)
    print("      DACN D.0 AGENT BENCHMARK EVALUATION METRICS REPORT")
    print("=" * 76)
    print(f"Overall Accuracy       : {meta['overall_accuracy_pct']}% ({meta['overall_passed']}/{meta['total_cases']})")
    print(f"Composite Score        : {meta['composite_score_pct']} / 100")
    print(f"Policy Compliance Rate : {sec['policy_compliance_rate_pct']}% (Violations: {sec['policy_violations_count']})")
    print(f"Schema Conformity Rate : {sec['schema_conformity_rate_pct']}% (Errors: {sec['schema_errors_count']})")
    print(f"Prompt Injection Def.  : {sec['injection_defense_rate_pct']}% (Defended: {sec['injection_attacks_tested']})")
    print(f"Tool Selection Accuracy: {sec['tool_selection_accuracy_pct']}%")
    print(f"Stop / Escalation Acc. : {sec['stop_escalation_accuracy_pct']}%")
    print("-" * 76)
    print("Action Classification Metrics:")
    act_headers = ["Action Type", "Precision", "Recall", "F1-Score", "Support"]
    act_rows = [
        [lbl, f"{s['precision']:.3f}", f"{s['recall']:.3f}", f"{s['f1_score']:.3f}", str(s['support'])]
        for lbl, s in act["per_class"].items()
    ]
    act_rows.append(["Macro Avg", f"{act['macro_precision']:.3f}", f"{act['macro_recall']:.3f}", f"{act['macro_f1']:.3f}", str(meta['total_cases'])])
    print(format_table(act_headers, act_rows))
    print("-" * 76)
    print("Category Breakdown:")
    cat_headers = ["Category", "Total", "Passed", "Failed", "Accuracy"]
    cat_rows = [
        [cat, str(s["total"]), str(s["passed"]), str(s["failed"]), f"{s['accuracy_pct']}%"]
        for cat, s in cats.items()
    ]
    print(format_table(cat_headers, cat_rows))
    print("=" * 76 + "\n")


def cmd_export(args: argparse.Namespace) -> None:
    output_dir = Path(args.output or REPORTS_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    calc = evaluate_all(args.dataset)

    exported_files = []
    formats = args.formats.split(",") if args.formats else ["json", "md", "html", "csv"]

    summary = calc.compute_summary()

    # JSON export
    if "json" in formats:
        json_file = output_dir / "benchmark_report.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        exported_files.append(json_file)

    # Markdown export
    if "md" in formats or "markdown" in formats:
        md_file = output_dir / "benchmark_report.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(calc.to_markdown())
        exported_files.append(md_file)

    # HTML export
    if "html" in formats:
        html_file = output_dir / "benchmark_report.html"
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(calc.to_html())
        exported_files.append(html_file)

    # CSV export
    if "csv" in formats:
        csv_file = output_dir / "benchmark_cases.csv"
        with open(csv_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "case_id", "category", "name", "expected_action", "predicted_action",
                "expected_tool", "predicted_tool", "passed", "issues"
            ])
            for c in summary["cases"]:
                writer.writerow([
                    c["case_id"],
                    c["category"],
                    c["name"],
                    c["expected_action"],
                    c["predicted_action"],
                    c["expected_tool"] or "",
                    c["predicted_tool"] or "",
                    "PASS" if c["passed"] else "FAIL",
                    "; ".join(c["issues"]),
                ])
        exported_files.append(csv_file)

    # Word DOCX export
    if "docx" in formats or "doc" in formats:
        try:
            from evaluation.export_docx import create_docx_report
            docx_file = output_dir / "Bao_Cao_Danh_Gia_AI_Agent_Dat.docx"
            create_docx_report(docx_file)
            exported_files.append(docx_file)
        except Exception as exc:
            print(f"Warning: Could not export DOCX ({exc})")

    print(f"\n[DACN D.0 Benchmark] Successfully exported {len(exported_files)} report file(s) to: {output_dir.resolve()}")
    for p in exported_files:
        print(f"  - {p.name}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DACN D.0 Benchmark CLI: Manage data, compute metrics, inspect cases, and export reports."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # list
    p_list = subparsers.add_parser("list", help="List labeled cases with optional filters")
    p_list.add_argument("--category", type=str, help="Filter by scenario category")
    p_list.add_argument("--action", type=str, help="Filter by expected action type")
    p_list.add_argument("--search", type=str, help="Search keyword in ID, name, or description")
    p_list.add_argument("--mock-only", action="store_true", help="Show only mock cases")

    # view
    p_view = subparsers.add_parser("view", help="Inspect detailed information of a specific case")
    p_view.add_argument("case_id", type=str, help="Case identifier (e.g., EVAL-001)")

    # stats
    subparsers.add_parser("stats", help="Display summary statistics of labeled dataset")

    # eval
    p_eval = subparsers.add_parser("eval", help="Run benchmark evaluation and print metrics")
    p_eval.add_argument("--dataset", type=Path, help="Custom dataset path")

    # export
    p_export = subparsers.add_parser("export", help="Export benchmark evaluation reports")
    p_export.add_argument("--output", type=Path, help="Directory to save exported reports")
    p_export.add_argument(
        "--formats",
        type=str,
        default="json,md,html,csv,docx",
        help="Comma-separated formats: json,md,html,csv,docx",
    )
    p_export.add_argument("--dataset", type=Path, help="Custom dataset path")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "list":
        cmd_list(args)
    elif args.command == "view":
        cmd_view(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "eval":
        cmd_eval(args)
    elif args.command == "export":
        cmd_export(args)


if __name__ == "__main__":
    main()
