#!/usr/bin/env python3
"""Run positive strategy publish->bind->rollback smoke flow against a running backend."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class ApiClient:
    base_url: str
    timeout_sec: float
    verbose: bool

    def call(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        expected: tuple[int, ...] = (200,),
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self.base_url}{path}"
        body: bytes | None = None
        headers: dict[str, str] = {}
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(url=url, data=body, headers=headers, method=method)
        status = -1
        raw = ""
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_sec) as response:
                status = response.status
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            status = exc.code
            raw = exc.read().decode("utf-8")

        payload_obj: dict[str, Any] = {}
        if raw.strip():
            try:
                loaded = json.loads(raw)
                if isinstance(loaded, dict):
                    payload_obj = loaded
                else:
                    payload_obj = {"raw": loaded}
            except json.JSONDecodeError:
                payload_obj = {"raw": raw}

        if self.verbose:
            mark = "PASS" if status in expected else "FAIL"
            print(f"[{mark}] {method} {path} -> {status}")

        if status not in expected:
            raise RuntimeError(f"{method} {path} -> {status}, payload={payload_obj}")
        return status, payload_obj


def _build_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Positive strategy publish smoke flow")
    parser.add_argument("--base-url", default="http://127.0.0.1:18000/api/v2", help="Backend API base URL")
    parser.add_argument("--timeout-sec", type=float, default=30.0, help="HTTP request timeout")
    parser.add_argument("--max-symbol-attempts", type=int, default=40, help="Max symbol attempts to hit publish gate")
    parser.add_argument("--samples-per-symbol", type=int, default=5, help="Analysis samples generated per symbol")
    parser.add_argument("--report-type", default="detailed", help="Analysis report_type")
    parser.add_argument("--quiet", action="store_true", help="Disable per-request logs")
    return parser.parse_args()


def main() -> int:
    args = _build_args()
    max_symbol_attempts = max(int(args.max_symbol_attempts), 1)
    samples_per_symbol = max(int(args.samples_per_symbol), 1)
    base_url = args.base_url.rstrip("/")
    client = ApiClient(
        base_url=base_url,
        timeout_sec=max(float(args.timeout_sec), 1.0),
        verbose=not args.quiet,
    )

    try:
        client.call("GET", "/health", expected=(200,))

        _, session = client.call(
            "POST",
            "/chat/sessions",
            payload={"user_id": "it-positive-flow", "memory_policy": "summary_v1"},
            expected=(201,),
        )
        session_id = str(session["session_id"])
        client.call(
            "POST",
            f"/chat/sessions/{session_id}/messages",
            payload={"content": "请总结交易策略思路"},
            expected=(200,),
        )

        _, memo = client.call(
            "POST",
            "/strategy/cognition/distill",
            payload={"session_id": session_id},
            expected=(201,),
        )
        memo_id = str(memo["memo_id"])
        client.call(
            "POST",
            f"/strategy/cognition/{memo_id}/review",
            payload={"action": "approve", "reviewer": "it-positive-flow"},
            expected=(200,),
        )
        _, strategy = client.call(
            "POST",
            "/strategy/extract",
            payload={"strategy_type": "analysis", "source_scope": "indexed_memos"},
            expected=(201,),
        )
        strategy_id = str(strategy["strategy_id"])

        winning_backtest: dict[str, Any] | None = None
        for idx in range(1, max_symbol_attempts + 1):
            symbol = f"PUBLISH{idx:03d}"
            for _ in range(samples_per_symbol):
                client.call(
                    "POST",
                    "/analysis/jobs",
                    payload={"symbol": symbol, "report_type": args.report_type},
                    expected=(202,),
                )
            _, backtest = client.call(
                "POST",
                "/backtest/jobs",
                payload={
                    "scope": "symbol",
                    "symbol": symbol,
                    "eval_window_days": 10,
                },
                expected=(202,),
            )
            backtest_job_id = str(backtest["job_id"])
            _, backtest_job = client.call("GET", f"/backtest/jobs/{backtest_job_id}", expected=(200,))

            metrics = backtest_job.get("metrics", {})
            sample_size = int(metrics.get("sample_size") or 0)
            win_rate = float(metrics.get("win_rate_pct") or 0.0)
            if args.quiet:
                print(
                    f"symbol={symbol} backtest_job={backtest_job_id} "
                    f"sample_size={sample_size} win_rate_pct={win_rate}"
                )
            if sample_size >= 5 and win_rate >= 50.0:
                winning_backtest = {
                    "symbol": symbol,
                    "backtest_job_id": backtest_job_id,
                    "metrics": metrics,
                }
                break

        if winning_backtest is None:
            raise RuntimeError("No passing backtest sample found; increase --max-symbol-attempts.")

        publish_status, publish = client.call(
            "POST",
            f"/strategy/{strategy_id}/publish",
            payload={"backtest_job_id": winning_backtest["backtest_job_id"]},
            expected=(200, 409),
        )
        if publish_status != 200:
            raise RuntimeError(f"Publish blocked by gate: {publish}")

        _, binding = client.call(
            "POST",
            f"/strategy/{strategy_id}/bind",
            payload={
                "flow_id": "chat_reply_v1",
                "prompt_refs": ["prompt.chat.reply@1"],
                "prompt_lock_mode": "lenient",
            },
            expected=(201,),
        )
        _, bindings = client.call("GET", "/strategy/bindings?flow_id=chat_reply_v1&limit=10", expected=(200,))
        _, rollback = client.call(
            "POST",
            f"/strategy/{strategy_id}/rollback",
            payload={"reason": "positive integration smoke"},
            expected=(200,),
        )

        summary = {
            "base_url": base_url,
            "strategy_id": strategy_id,
            "winning_backtest": winning_backtest,
            "publish_status": publish_status,
            "binding_id": binding.get("binding_id"),
            "bindings_count": bindings.get("count"),
            "rollback_status": rollback.get("status"),
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
