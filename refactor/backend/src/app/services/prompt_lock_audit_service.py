from __future__ import annotations

import json
from concurrent.futures import Future, ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from threading import Lock
from time import monotonic
from typing import Any
from uuid import uuid4

from app.persistence.sqlite_db import SQLiteDatabase


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PromptLockAuditService:
    """Audit service for prompt lock failures."""

    _GROUP_BY_ALLOWED = ("flow_id", "source_type", "reason")
    _TREND_GRANULARITY_ALLOWED = ("hour", "day")
    _TREND_SPLIT_BY_ALLOWED = ("reason",)
    _OVERVIEW_INCLUDE_ALLOWED = ("summary", "grouped", "trends")
    _OVERVIEW_CACHE_TTL_SEC_DEFAULT = 30
    _OVERVIEW_CACHE_MAX_SIZE_DEFAULT = 128
    _OVERVIEW_MODULE_TIMEOUT_SEC_DEFAULT = 0.0

    def __init__(
        self,
        database: SQLiteDatabase,
        overview_cache_ttl_sec: int = _OVERVIEW_CACHE_TTL_SEC_DEFAULT,
        overview_cache_max_size: int = _OVERVIEW_CACHE_MAX_SIZE_DEFAULT,
        overview_module_timeout_sec: float = _OVERVIEW_MODULE_TIMEOUT_SEC_DEFAULT,
        overview_module_timeouts_sec: dict[str, float] | None = None,
    ) -> None:
        self._database = database
        self._overview_cache_ttl_sec = max(int(overview_cache_ttl_sec), 0)
        self._overview_cache_max_size = max(int(overview_cache_max_size), 0)
        self._overview_module_timeout_sec = max(float(overview_module_timeout_sec), 0.0)
        self._overview_module_timeouts_sec = self._normalize_overview_module_timeouts(overview_module_timeouts_sec)
        self._overview_cache: dict[str, dict[str, Any]] = {}
        self._overview_cache_lock = Lock()
        self._overview_metrics_lock = Lock()
        self._overview_metrics = self._build_empty_overview_metrics_state()

    def record_event(
        self,
        flow_id: str,
        lock_mode: str,
        source_type: str,
        source_id: str | None,
        requested_prompt_refs: list[str],
        failures: list[Any],
    ) -> dict[str, Any]:
        event_id = str(uuid4())
        now = _utc_now()
        serialized_failures = [self._serialize_failure(item) for item in failures]
        with self._database.connection() as conn:
            conn.execute(
                """
                INSERT INTO prompt_lock_events (
                    event_id, flow_id, lock_mode, source_type, source_id,
                    requested_prompt_refs_json, failures_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    flow_id,
                    lock_mode,
                    source_type,
                    source_id,
                    self._database.json_dump(requested_prompt_refs),
                    self._database.json_dump(serialized_failures),
                    now,
                ),
            )
        self._invalidate_overview_cache()
        return {
            "event_id": event_id,
            "flow_id": flow_id,
            "lock_mode": lock_mode,
            "source_type": source_type,
            "source_id": source_id,
            "requested_prompt_refs": requested_prompt_refs,
            "failures": serialized_failures,
            "created_at": now,
        }

    def list_events(
        self,
        flow_id: str | None = None,
        source_type: str | None = None,
        last_hours: int | None = None,
        start_at: str | None = None,
        end_at: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        safe_limit = max(min(int(limit), 500), 1)
        created_after, created_before = self._resolve_time_range(
            last_hours=last_hours,
            start_at=start_at,
            end_at=end_at,
        )
        query = """
            SELECT
                event_id, flow_id, lock_mode, source_type, source_id,
                requested_prompt_refs_json, failures_json, created_at
            FROM prompt_lock_events
            WHERE 1 = 1
        """
        params: list[Any] = []
        if flow_id:
            query += " AND flow_id = ?"
            params.append(flow_id)
        if source_type:
            query += " AND source_type = ?"
            params.append(source_type)
        if created_after is not None:
            query += " AND created_at >= ?"
            params.append(created_after)
        if created_before is not None:
            query += " AND created_at <= ?"
            params.append(created_before)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(safe_limit)

        with self._database.connection() as conn:
            rows = conn.execute(query, params).fetchall()
        items = [self._serialize_row(row) for row in rows]
        return {"items": items, "count": len(items)}

    def summarize_failures(
        self,
        flow_id: str | None = None,
        source_type: str | None = None,
        last_hours: int | None = None,
        start_at: str | None = None,
        end_at: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        listed = self.list_events(
            flow_id=flow_id,
            source_type=source_type,
            last_hours=last_hours,
            start_at=start_at,
            end_at=end_at,
            limit=500,
        )["items"]
        counts: dict[str, int] = {}
        total_failures = 0
        for item in listed:
            for failure in item["failures"]:
                reason = str(failure.get("reason", "unknown"))
                counts[reason] = counts.get(reason, 0) + 1
                total_failures += 1
        sorted_counts = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        reason_counts = [{"reason": reason, "count": count} for reason, count in sorted_counts[: max(limit, 1)]]
        return {
            "total_events": len(listed),
            "total_failures": total_failures,
            "reason_counts": reason_counts,
        }

    def group_failures(
        self,
        flow_id: str | None = None,
        source_type: str | None = None,
        last_hours: int | None = None,
        start_at: str | None = None,
        end_at: str | None = None,
        group_by: list[str] | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        dimensions = self._normalize_group_by(group_by)
        safe_limit = max(min(int(limit), 500), 1)
        listed = self.list_events(
            flow_id=flow_id,
            source_type=source_type,
            last_hours=last_hours,
            start_at=start_at,
            end_at=end_at,
            limit=500,
        )["items"]

        counts: dict[tuple[str, ...], dict[str, Any]] = {}
        for item in listed:
            for failure in item["failures"]:
                grouped_item: dict[str, Any] = {}
                key_parts: list[str] = []
                for dim in dimensions:
                    value = self._resolve_group_dimension_value(dim=dim, event=item, failure=failure)
                    grouped_item[dim] = value
                    key_parts.append(value)
                key = tuple(key_parts)
                if key not in counts:
                    counts[key] = {**grouped_item, "count": 0}
                counts[key]["count"] += 1

        ranked = sorted(
            counts.values(),
            key=lambda item: (
                -int(item["count"]),
                tuple(str(item.get(dim, "")) for dim in dimensions),
            ),
        )
        items = ranked[:safe_limit]
        return {
            "group_by": dimensions,
            "total_groups": len(ranked),
            "items": items,
        }

    def failure_trends(
        self,
        flow_id: str | None = None,
        source_type: str | None = None,
        last_hours: int | None = None,
        start_at: str | None = None,
        end_at: str | None = None,
        granularity: str = "hour",
        split_by: str | None = None,
        reason_top_n: int | None = None,
        limit: int = 200,
    ) -> dict[str, Any]:
        resolved_granularity = self._normalize_granularity(granularity)
        resolved_split_by = self._normalize_trend_split_by(split_by)
        resolved_reason_top_n = self._normalize_reason_top_n(reason_top_n)
        if resolved_split_by != "reason":
            resolved_reason_top_n = None
        safe_limit = max(min(int(limit), 2000), 1)
        listed = self.list_events(
            flow_id=flow_id,
            source_type=source_type,
            last_hours=last_hours,
            start_at=start_at,
            end_at=end_at,
            limit=500,
        )["items"]
        buckets: dict[str, dict[str, Any]] = {}
        for event in listed:
            created_at = self._parse_datetime(str(event.get("created_at", "")), field_name="created_at")
            bucket_dt = self._truncate_datetime(created_at, granularity=resolved_granularity)
            bucket_key = bucket_dt.isoformat()
            if bucket_key not in buckets:
                buckets[bucket_key] = {
                    "bucket_start": bucket_key,
                    "event_count": 0,
                    "failure_count": 0,
                    "_reason_counts": {},
                }
            buckets[bucket_key]["event_count"] += 1
            failures = event.get("failures", [])
            buckets[bucket_key]["failure_count"] += len(failures)
            if resolved_split_by == "reason":
                reason_counts = buckets[bucket_key]["_reason_counts"]
                for failure in failures:
                    reason = str(failure.get("reason", "unknown"))
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1
        ranked = sorted(buckets.values(), key=lambda item: str(item["bucket_start"]))
        for item in ranked:
            reason_counts_map = item.pop("_reason_counts", {})
            if resolved_split_by == "reason":
                sorted_counts = sorted(reason_counts_map.items(), key=lambda kv: (-kv[1], kv[0]))
                if resolved_reason_top_n is not None:
                    sorted_counts = sorted_counts[:resolved_reason_top_n]
                item["reason_counts"] = [{"reason": reason, "count": count} for reason, count in sorted_counts]
        if len(ranked) > safe_limit:
            ranked = ranked[-safe_limit:]
        return {
            "granularity": resolved_granularity,
            "split_by": resolved_split_by,
            "reason_top_n": resolved_reason_top_n,
            "total_buckets": len(ranked),
            "items": ranked,
        }

    def build_overview(
        self,
        flow_id: str | None = None,
        source_type: str | None = None,
        last_hours: int | None = None,
        start_at: str | None = None,
        end_at: str | None = None,
        include: list[str] | None = None,
        summary_limit: int = 20,
        group_by: list[str] | None = None,
        grouped_limit: int = 100,
        granularity: str = "hour",
        split_by: str | None = None,
        reason_top_n: int | None = None,
        trend_limit: int = 200,
    ) -> dict[str, Any]:
        modules = self._normalize_overview_include(include)
        resolved_group_by = self._normalize_group_by(group_by) if "grouped" in modules else None
        resolved_granularity = self._normalize_granularity(granularity) if "trends" in modules else granularity
        resolved_split_by = self._normalize_trend_split_by(split_by) if "trends" in modules else split_by
        resolved_reason_top_n = self._normalize_reason_top_n(reason_top_n) if "trends" in modules else reason_top_n
        if "trends" in modules and resolved_split_by != "reason":
            resolved_reason_top_n = None
        cache_key = self._build_overview_cache_key(
            flow_id=flow_id,
            source_type=source_type,
            last_hours=last_hours,
            start_at=start_at,
            end_at=end_at,
            include=modules,
            summary_limit=summary_limit,
            group_by=resolved_group_by,
            grouped_limit=grouped_limit,
            granularity=resolved_granularity,
            split_by=resolved_split_by,
            reason_top_n=resolved_reason_top_n,
            trend_limit=trend_limit,
        )
        cached = self._load_overview_cache(cache_key)
        if cached is not None:
            self._record_overview_cache_hit_metrics()
            return cached
        payload: dict[str, Any] = {"include": modules, "degraded": False, "module_errors": []}
        module_outcomes: dict[str, str] = {module: "success" for module in modules}
        tasks: dict[str, Any] = {}
        if "summary" in modules:
            tasks["summary"] = lambda: self.summarize_failures(
                flow_id=flow_id,
                source_type=source_type,
                last_hours=last_hours,
                start_at=start_at,
                end_at=end_at,
                limit=summary_limit,
            )
        if "grouped" in modules:
            tasks["grouped"] = lambda: self.group_failures(
                flow_id=flow_id,
                source_type=source_type,
                last_hours=last_hours,
                start_at=start_at,
                end_at=end_at,
                group_by=resolved_group_by,
                limit=grouped_limit,
            )
        if "trends" in modules:
            tasks["trends"] = lambda: self.failure_trends(
                flow_id=flow_id,
                source_type=source_type,
                last_hours=last_hours,
                start_at=start_at,
                end_at=end_at,
                granularity=resolved_granularity,
                split_by=resolved_split_by,
                reason_top_n=resolved_reason_top_n,
                limit=trend_limit,
            )
        if len(tasks) <= 1:
            for module in modules:
                if module in tasks:
                    try:
                        payload[module] = tasks[module]()
                    except Exception:
                        module_outcomes[module] = "exception"
                        self._record_overview_execution_metrics(
                            modules=modules,
                            module_outcomes=module_outcomes,
                            degraded=True,
                        )
                        raise
        else:
            executor = ThreadPoolExecutor(max_workers=len(tasks))
            try:
                futures: dict[str, Future[Any]] = {
                    module: executor.submit(callable_task) for module, callable_task in tasks.items()
                }
                for module in modules:
                    if module not in futures:
                        continue
                    future = futures[module]
                    module_timeout_sec = self._resolve_overview_module_timeout_sec(module)
                    try:
                        if module_timeout_sec > 0:
                            payload[module] = future.result(timeout=module_timeout_sec)
                        else:
                            payload[module] = future.result()
                    except FuturesTimeoutError:
                        future.cancel()
                        module_outcomes[module] = "timeout"
                        payload["degraded"] = True
                        payload["module_errors"].append(
                            {
                                "module": module,
                                "code": "timeout",
                                "message": f"overview module timed out after {module_timeout_sec}s",
                            }
                        )
                        payload[module] = self._empty_overview_module_payload(
                            module=module,
                            group_by=resolved_group_by,
                            granularity=resolved_granularity,
                            split_by=resolved_split_by,
                            reason_top_n=resolved_reason_top_n,
                        )
                    except Exception as exc:
                        module_outcomes[module] = "exception"
                        payload["degraded"] = True
                        payload["module_errors"].append(
                            {
                                "module": module,
                                "code": "exception",
                                "message": str(exc) or exc.__class__.__name__,
                            }
                        )
                        payload[module] = self._empty_overview_module_payload(
                            module=module,
                            group_by=resolved_group_by,
                            granularity=resolved_granularity,
                            split_by=resolved_split_by,
                            reason_top_n=resolved_reason_top_n,
                        )
            finally:
                executor.shutdown(wait=False, cancel_futures=True)
        self._record_overview_execution_metrics(
            modules=modules,
            module_outcomes=module_outcomes,
            degraded=payload["degraded"] is True,
        )
        if payload["degraded"] is not True:
            self._save_overview_cache(cache_key, payload)
        return payload

    def get_overview_metrics(self) -> dict[str, Any]:
        with self._overview_metrics_lock:
            snapshot = deepcopy(self._overview_metrics)
        request_total = int(snapshot.get("request_total", 0))
        degraded_total = int(snapshot.get("degraded_total", 0))
        cache_hit_total = int(snapshot.get("cache_hit_total", 0))
        snapshot["degraded_rate"] = self._safe_ratio(degraded_total, request_total)
        snapshot["cache_hit_rate"] = self._safe_ratio(cache_hit_total, request_total)
        module_stats = snapshot.get("module_stats", {})
        for stats in module_stats.values():
            run_total = int(stats.get("run_total", 0))
            timeout_total = int(stats.get("timeout_total", 0))
            exception_total = int(stats.get("exception_total", 0))
            module_degraded_total = int(stats.get("degraded_total", 0))
            stats["timeout_rate"] = self._safe_ratio(timeout_total, run_total)
            stats["error_rate"] = self._safe_ratio(timeout_total + exception_total, run_total)
            stats["degraded_rate"] = self._safe_ratio(module_degraded_total, run_total)
        return snapshot

    def get_overview_metrics_prometheus(self) -> str:
        metrics = self.get_overview_metrics()
        lines: list[str] = []
        lines.extend(
            [
                "# HELP refactor_prompt_lock_overview_request_total Total overview requests.",
                "# TYPE refactor_prompt_lock_overview_request_total counter",
                f"refactor_prompt_lock_overview_request_total {int(metrics.get('request_total', 0))}",
                "# HELP refactor_prompt_lock_overview_degraded_total Total degraded overview responses.",
                "# TYPE refactor_prompt_lock_overview_degraded_total counter",
                f"refactor_prompt_lock_overview_degraded_total {int(metrics.get('degraded_total', 0))}",
                "# HELP refactor_prompt_lock_overview_cache_hit_total Total overview cache hits.",
                "# TYPE refactor_prompt_lock_overview_cache_hit_total counter",
                f"refactor_prompt_lock_overview_cache_hit_total {int(metrics.get('cache_hit_total', 0))}",
                "# HELP refactor_prompt_lock_overview_degraded_rate Overview degraded rate.",
                "# TYPE refactor_prompt_lock_overview_degraded_rate gauge",
                f"refactor_prompt_lock_overview_degraded_rate {float(metrics.get('degraded_rate', 0.0))}",
                "# HELP refactor_prompt_lock_overview_cache_hit_rate Overview cache hit rate.",
                "# TYPE refactor_prompt_lock_overview_cache_hit_rate gauge",
                f"refactor_prompt_lock_overview_cache_hit_rate {float(metrics.get('cache_hit_rate', 0.0))}",
            ]
        )
        module_stats = metrics.get("module_stats", {})
        module_metric_defs = (
            ("run_total", "counter"),
            ("success_total", "counter"),
            ("timeout_total", "counter"),
            ("exception_total", "counter"),
            ("degraded_total", "counter"),
            ("timeout_rate", "gauge"),
            ("error_rate", "gauge"),
            ("degraded_rate", "gauge"),
        )
        for metric_name, metric_type in module_metric_defs:
            prom_name = f"refactor_prompt_lock_overview_module_{metric_name}"
            lines.append(f"# HELP {prom_name} Overview module metric {metric_name}.")
            lines.append(f"# TYPE {prom_name} {metric_type}")
            for module in self._OVERVIEW_INCLUDE_ALLOWED:
                stats = module_stats.get(module, {})
                raw_value = stats.get(metric_name, 0)
                value = float(raw_value) if metric_type == "gauge" else int(raw_value)
                lines.append(f'{prom_name}{{module="{module}"}} {value}')
        return "\n".join(lines) + "\n"

    @classmethod
    def _normalize_overview_module_timeouts(cls, raw: dict[str, float] | None) -> dict[str, float]:
        if not raw:
            return {}
        normalized: dict[str, float] = {}
        for module, timeout in raw.items():
            module_name = str(module).strip().lower()
            if not module_name:
                continue
            if module_name not in cls._OVERVIEW_INCLUDE_ALLOWED:
                raise ValueError(
                    f"Unsupported overview module timeout key: {module_name}; "
                    f"allowed={','.join(cls._OVERVIEW_INCLUDE_ALLOWED)}"
                )
            normalized[module_name] = max(float(timeout), 0.0)
        return normalized

    def _resolve_overview_module_timeout_sec(self, module: str) -> float:
        module_timeout = self._overview_module_timeouts_sec.get(module)
        if module_timeout is not None and module_timeout > 0:
            return module_timeout
        return self._overview_module_timeout_sec

    @classmethod
    def _build_empty_overview_metrics_state(cls) -> dict[str, Any]:
        return {
            "request_total": 0,
            "degraded_total": 0,
            "cache_hit_total": 0,
            "updated_at": None,
            "module_stats": {
                module: {
                    "run_total": 0,
                    "success_total": 0,
                    "timeout_total": 0,
                    "exception_total": 0,
                    "degraded_total": 0,
                }
                for module in cls._OVERVIEW_INCLUDE_ALLOWED
            },
        }

    def _record_overview_cache_hit_metrics(self) -> None:
        with self._overview_metrics_lock:
            self._overview_metrics["request_total"] += 1
            self._overview_metrics["cache_hit_total"] += 1
            self._overview_metrics["updated_at"] = _utc_now()

    def _record_overview_execution_metrics(
        self,
        modules: list[str],
        module_outcomes: dict[str, str],
        degraded: bool,
    ) -> None:
        with self._overview_metrics_lock:
            self._overview_metrics["request_total"] += 1
            if degraded:
                self._overview_metrics["degraded_total"] += 1
            for module in modules:
                stats = self._overview_metrics["module_stats"].get(module)
                if stats is None:
                    continue
                stats["run_total"] += 1
                outcome = module_outcomes.get(module, "success")
                if outcome == "timeout":
                    stats["timeout_total"] += 1
                    stats["degraded_total"] += 1
                elif outcome == "exception":
                    stats["exception_total"] += 1
                    stats["degraded_total"] += 1
                else:
                    stats["success_total"] += 1
            self._overview_metrics["updated_at"] = _utc_now()

    @staticmethod
    def _safe_ratio(numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return numerator / denominator

    @staticmethod
    def _empty_overview_module_payload(
        module: str,
        group_by: list[str] | None,
        granularity: str,
        split_by: str | None,
        reason_top_n: int | None,
    ) -> dict[str, Any]:
        if module == "summary":
            return {"total_events": 0, "total_failures": 0, "reason_counts": []}
        if module == "grouped":
            return {"group_by": group_by or ["flow_id", "source_type", "reason"], "total_groups": 0, "items": []}
        if module == "trends":
            return {
                "granularity": granularity,
                "split_by": split_by,
                "reason_top_n": reason_top_n,
                "total_buckets": 0,
                "items": [],
            }
        return {}

    def _serialize_row(self, row: Any) -> dict[str, Any]:
        return {
            "event_id": row["event_id"],
            "flow_id": row["flow_id"],
            "lock_mode": row["lock_mode"],
            "source_type": row["source_type"],
            "source_id": row["source_id"],
            "requested_prompt_refs": self._database.json_load(row["requested_prompt_refs_json"], []),
            "failures": self._database.json_load(row["failures_json"], []),
            "created_at": row["created_at"],
        }

    @staticmethod
    def _serialize_failure(item: Any) -> dict[str, str]:
        if hasattr(item, "to_dict"):
            payload = item.to_dict()
            return {
                "prompt_ref": str(payload.get("prompt_ref", "")),
                "reason": str(payload.get("reason", "unknown")),
            }
        if isinstance(item, dict):
            return {
                "prompt_ref": str(item.get("prompt_ref", "")),
                "reason": str(item.get("reason", "unknown")),
            }
        return {
            "prompt_ref": "",
            "reason": str(item or "unknown"),
        }

    @staticmethod
    def _resolve_time_range(
        last_hours: int | None,
        start_at: str | None,
        end_at: str | None,
    ) -> tuple[str | None, str | None]:
        lower_bound: datetime | None = None
        if last_hours is not None and int(last_hours) > 0:
            lower_bound = datetime.now(timezone.utc) - timedelta(hours=int(last_hours))
        if start_at:
            parsed_start = PromptLockAuditService._parse_datetime(start_at, field_name="start_at")
            lower_bound = parsed_start if lower_bound is None else max(lower_bound, parsed_start)

        upper_bound: datetime | None = None
        if end_at:
            upper_bound = PromptLockAuditService._parse_datetime(end_at, field_name="end_at")

        if lower_bound is not None and upper_bound is not None and lower_bound > upper_bound:
            raise ValueError("start_at must be less than or equal to end_at")
        return (
            lower_bound.isoformat() if lower_bound is not None else None,
            upper_bound.isoformat() if upper_bound is not None else None,
        )

    @staticmethod
    def _parse_datetime(value: str, field_name: str) -> datetime:
        candidate = str(value).strip()
        if candidate.endswith("Z"):
            candidate = f"{candidate[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError as exc:
            raise ValueError(f"Invalid {field_name} datetime format: {value}") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    @classmethod
    def _normalize_group_by(cls, group_by: list[str] | None) -> list[str]:
        if not group_by:
            return ["flow_id", "source_type", "reason"]
        normalized: list[str] = []
        for raw in group_by:
            for token in str(raw).split(","):
                dim = token.strip()
                if not dim:
                    continue
                if dim not in cls._GROUP_BY_ALLOWED:
                    raise ValueError(
                        f"Unsupported group_by dimension: {dim}; allowed={','.join(cls._GROUP_BY_ALLOWED)}"
                    )
                if dim not in normalized:
                    normalized.append(dim)
        if not normalized:
            raise ValueError("group_by must contain at least one supported dimension")
        return normalized

    @staticmethod
    def _resolve_group_dimension_value(dim: str, event: dict[str, Any], failure: dict[str, Any]) -> str:
        if dim == "flow_id":
            return str(event.get("flow_id", ""))
        if dim == "source_type":
            return str(event.get("source_type", ""))
        if dim == "reason":
            return str(failure.get("reason", "unknown"))
        return ""

    @classmethod
    def _normalize_granularity(cls, granularity: str) -> str:
        value = str(granularity or "").strip().lower()
        if value in cls._TREND_GRANULARITY_ALLOWED:
            return value
        raise ValueError(f"Unsupported granularity: {granularity}; allowed={','.join(cls._TREND_GRANULARITY_ALLOWED)}")

    @classmethod
    def _normalize_trend_split_by(cls, split_by: str | None) -> str | None:
        if split_by is None:
            return None
        value = str(split_by).strip().lower()
        if value == "":
            return None
        if value in cls._TREND_SPLIT_BY_ALLOWED:
            return value
        raise ValueError(f"Unsupported split_by: {split_by}; allowed={','.join(cls._TREND_SPLIT_BY_ALLOWED)}")

    @staticmethod
    def _normalize_reason_top_n(reason_top_n: int | None) -> int | None:
        if reason_top_n is None:
            return None
        value = int(reason_top_n)
        if value <= 0:
            raise ValueError("reason_top_n must be greater than 0")
        return value

    @classmethod
    def _normalize_overview_include(cls, include: list[str] | None) -> list[str]:
        if not include:
            return list(cls._OVERVIEW_INCLUDE_ALLOWED)
        normalized: list[str] = []
        for raw in include:
            for token in str(raw).split(","):
                module = token.strip().lower()
                if not module:
                    continue
                if module not in cls._OVERVIEW_INCLUDE_ALLOWED:
                    raise ValueError(
                        f"Unsupported include module: {module}; " f"allowed={','.join(cls._OVERVIEW_INCLUDE_ALLOWED)}"
                    )
                if module not in normalized:
                    normalized.append(module)
        if not normalized:
            raise ValueError("include must contain at least one supported module")
        return normalized

    def _build_overview_cache_key(
        self,
        flow_id: str | None,
        source_type: str | None,
        last_hours: int | None,
        start_at: str | None,
        end_at: str | None,
        include: list[str],
        summary_limit: int,
        group_by: list[str] | None,
        grouped_limit: int,
        granularity: str,
        split_by: str | None,
        reason_top_n: int | None,
        trend_limit: int,
    ) -> str:
        payload = {
            "flow_id": flow_id,
            "source_type": source_type,
            "last_hours": last_hours,
            "start_at": start_at,
            "end_at": end_at,
            "include": include,
            "summary_limit": summary_limit,
            "group_by": group_by or [],
            "grouped_limit": grouped_limit,
            "granularity": granularity,
            "split_by": split_by,
            "reason_top_n": reason_top_n,
            "trend_limit": trend_limit,
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def _load_overview_cache(self, cache_key: str) -> dict[str, Any] | None:
        if self._overview_cache_ttl_sec <= 0 or self._overview_cache_max_size <= 0:
            return None
        with self._overview_cache_lock:
            cached = self._overview_cache.get(cache_key)
            if cached is None:
                return None
            cached_at = float(cached.get("cached_at", 0.0))
            if self._now_monotonic() - cached_at >= self._overview_cache_ttl_sec:
                self._overview_cache.pop(cache_key, None)
                return None
            return deepcopy(cached.get("payload", {}))

    def _save_overview_cache(self, cache_key: str, payload: dict[str, Any]) -> None:
        if self._overview_cache_ttl_sec <= 0 or self._overview_cache_max_size <= 0:
            return
        with self._overview_cache_lock:
            if cache_key in self._overview_cache:
                self._overview_cache.pop(cache_key)
            self._prune_expired_overview_cache_locked()
            self._overview_cache[cache_key] = {
                "cached_at": self._now_monotonic(),
                "payload": deepcopy(payload),
            }
            while len(self._overview_cache) > self._overview_cache_max_size:
                self._overview_cache.pop(next(iter(self._overview_cache)))

    def _invalidate_overview_cache(self) -> None:
        with self._overview_cache_lock:
            self._overview_cache.clear()

    def _prune_expired_overview_cache_locked(self) -> None:
        if self._overview_cache_ttl_sec <= 0:
            self._overview_cache.clear()
            return
        now = self._now_monotonic()
        expired_keys: list[str] = []
        for key, item in self._overview_cache.items():
            cached_at = float(item.get("cached_at", 0.0))
            if now - cached_at >= self._overview_cache_ttl_sec:
                expired_keys.append(key)
        for key in expired_keys:
            self._overview_cache.pop(key, None)

    @staticmethod
    def _now_monotonic() -> float:
        return monotonic()

    @staticmethod
    def _truncate_datetime(value: datetime, granularity: str) -> datetime:
        if granularity == "day":
            return value.replace(hour=0, minute=0, second=0, microsecond=0)
        return value.replace(minute=0, second=0, microsecond=0)
