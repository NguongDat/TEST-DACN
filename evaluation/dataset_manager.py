"""Dataset Manager for DACN D.0 Labeled Evaluation Benchmark.

Provides programmatic data management:
- Loading and saving JSONL evaluation cases.
- Schema verification and integrity validation.
- Filtering, querying, and searching cases.
- Dataset summary statistics and label distribution.
- Stratified train/val/test dataset splitting.
"""
from __future__ import annotations

import collections
import copy
import json
from pathlib import Path
import random
from typing import Any, Dict, List, Optional, Set
import jsonschema

DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parent / "schemas" / "eval_case.schema.json"
DEFAULT_DATASET_PATH = Path(__file__).resolve().parent / "data" / "evaluation_cases.jsonl"


class DatasetManager:
    """Manages labeled benchmark dataset for AI Agent evaluation."""

    def __init__(
        self,
        dataset_path: Optional[Path] = None,
        schema_path: Optional[Path] = None
    ) -> None:
        self.dataset_path = Path(dataset_path or DEFAULT_DATASET_PATH)
        self.schema_path = Path(schema_path or DEFAULT_SCHEMA_PATH)
        self._cases: Dict[str, Dict[str, Any]] = {}
        self._schema: Optional[Dict[str, Any]] = None
        self._validator: Optional[jsonschema.Draft202012Validator] = None

        self._load_schema()
        if self.dataset_path.exists():
            self.load()

    def _load_schema(self) -> None:
        if self.schema_path.exists():
            with open(self.schema_path, "r", encoding="utf-8") as f:
                self._schema = json.load(f)
            self._validator = jsonschema.Draft202012Validator(self._schema)

    def load(self, path: Optional[Path] = None) -> int:
        """Loads evaluation cases from JSONL file."""
        target_path = Path(path or self.dataset_path)
        self._cases.clear()
        if not target_path.exists():
            return 0

        with open(target_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    case = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"JSON decode error at line {line_no}: {exc}") from exc
                
                cid = case.get("case_id")
                if not cid:
                    raise ValueError(f"Missing case_id at line {line_no}")
                if cid in self._cases:
                    raise ValueError(f"Duplicate case_id '{cid}' found at line {line_no}")
                
                self._cases[cid] = case

        return len(self._cases)

    def save(self, path: Optional[Path] = None) -> int:
        """Saves current evaluation cases back to JSONL file."""
        target_path = Path(path or self.dataset_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            for case in self._cases.values():
                f.write(json.dumps(case, ensure_ascii=False) + "\n")
        return len(self._cases)

    def validate_case(self, case: Dict[str, Any]) -> List[str]:
        """Validates a single case against eval_case.schema.json."""
        if not self._validator:
            return ["Schema validator is not initialized"]
        return [err.message for err in self._validator.iter_errors(case)]

    def validate_all(self) -> Dict[str, List[str]]:
        """Validates all loaded cases. Returns mapping of case_id -> list of errors."""
        errors: Dict[str, List[str]] = {}
        for cid, case in self._cases.items():
            errs = self.validate_case(case)
            if errs:
                errors[cid] = errs
        return errors

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a deepcopy of a case by ID."""
        case = self._cases.get(case_id)
        return copy.deepcopy(case) if case else None

    def list_cases(
        self,
        category: Optional[str] = None,
        action_type: Optional[str] = None,
        search: Optional[str] = None,
        is_mock: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Filters cases based on multiple criteria."""
        results = []
        for case in self._cases.values():
            if category and case.get("category") != category:
                continue
            if is_mock is not None and case.get("is_mock") != is_mock:
                continue
            
            exp_action = case.get("expected_action", {})
            if action_type and exp_action.get("action_type") != action_type:
                continue

            if search:
                term = search.lower()
                text = (
                    f"{case.get('case_id', '')} "
                    f"{case.get('name', '')} "
                    f"{case.get('description', '')} "
                    f"{case.get('reason', '')}"
                ).lower()
                if term not in text:
                    continue

            results.append(copy.deepcopy(case))
        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Computes comprehensive summary statistics for the dataset."""
        total = len(self._cases)
        categories = collections.Counter()
        actions = collections.Counter()
        tools_called = collections.Counter()
        evidence_origins = collections.Counter()
        trust_levels = collections.Counter()
        phases = collections.Counter()
        mock_count = 0
        total_evidence_facets = 0

        for case in self._cases.values():
            categories[case.get("category", "unknown")] += 1
            if case.get("is_mock"):
                mock_count += 1
            
            cstate = case.get("case_state", {})
            phases[cstate.get("workflow_phase", "UNKNOWN")] += 1

            act = case.get("expected_action", {})
            act_type = act.get("action_type", "UNKNOWN")
            actions[act_type] += 1
            if act_type == "CALL_TOOL":
                tools_called[act.get("tool_id", "unspecified")] += 1

            evidence_list = case.get("evidence", [])
            total_evidence_facets += len(evidence_list)
            for ev in evidence_list:
                evidence_origins[ev.get("content_origin", "unknown")] += 1
                trust_levels[ev.get("trust_level", "unknown")] += 1

        return {
            "total_cases": total,
            "mock_cases": mock_count,
            "mock_percentage": (mock_count / total * 100) if total else 0.0,
            "total_evidence_facets": total_evidence_facets,
            "avg_evidence_per_case": round(total_evidence_facets / total, 2) if total else 0.0,
            "categories": dict(categories),
            "workflow_phases": dict(phases),
            "actions": dict(actions),
            "tools_called": dict(tools_called),
            "evidence_origins": dict(evidence_origins),
            "trust_levels": dict(trust_levels),
        }

    def split_dataset(
        self,
        train_ratio: float = 0.6,
        val_ratio: float = 0.2,
        test_ratio: float = 0.2,
        seed: int = 42
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Splits cases into stratified train/val/test splits based on category."""
        if not (0.99 <= (train_ratio + val_ratio + test_ratio) <= 1.01):
            raise ValueError("Ratios must sum to 1.0")

        rng = random.Random(seed)
        by_category = collections.defaultdict(list)
        for case in self._cases.values():
            by_category[case.get("category", "unknown")].append(copy.deepcopy(case))

        splits = {"train": [], "val": [], "test": []}

        for cat_cases in by_category.values():
            rng.shuffle(cat_cases)
            n = len(cat_cases)
            n_train = int(round(n * train_ratio))
            n_val = int(round(n * val_ratio))
            
            train_items = cat_cases[:n_train]
            val_items = cat_cases[n_train:n_train + n_val]
            test_items = cat_cases[n_train + n_val:]

            # Ensure at least 1 item in train if available
            if not train_items and cat_cases:
                train_items.append(cat_cases[0])

            splits["train"].extend(train_items)
            splits["val"].extend(val_items)
            splits["test"].extend(test_items)

        return splits

