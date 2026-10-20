import json
import os
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen


def get_resource_health():
    """
    Read current resource metrics from LogSherlock.

    If LogSherlock is unavailable, DemoShop remains operational.
    Protected operations will be blocked only when a valid response
    reports a critical resource condition.
    """
    logsherlock_url = os.getenv("LOGSHERLOCK_URL", "").strip().rstrip("/")

    if not logsherlock_url:
        return {
            "monitoring_available": False,
            "overall_status": "UNKNOWN",
            "message": "Resource monitoring is temporarily unavailable. LogSherlock URL is not configured.",
            "customer_message": "Resource monitoring is temporarily unavailable.",
            "resources": [],
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    request = Request(
        f"{logsherlock_url}/monitoring/metrics",
        headers={"Accept": "application/json"},
        method="GET",
    )

    try:
        with urlopen(request, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))

        metrics = payload.get("metrics")

        if not isinstance(metrics, list) or not metrics:
            raise ValueError("LogSherlock returned no resource metrics.")

        resources = []

        for metric in metrics:
            usage_raw = metric.get("current_usage", 0)
            try:
                usage = float(usage_raw)
            except (TypeError, ValueError):
                usage = 0.0

            warning_raw = metric.get("warning_threshold", 80)
            try:
                warning_threshold = float(warning_raw)
            except (TypeError, ValueError):
                warning_threshold = 80.0

            critical_raw = metric.get("critical_threshold", 90)
            try:
                critical_threshold = float(critical_raw)
            except (TypeError, ValueError):
                critical_threshold = 90.0

            metric_status = str(metric.get("status", "")).upper()
            risk_level = str(metric.get("risk_level", "NORMAL")).upper()

            if usage >= critical_threshold or metric_status == "CRITICAL" or risk_level == "CRITICAL":
                status = "CRITICAL"
            elif (
                usage >= warning_threshold
                or metric_status in {"WARNING", "DEGRADED"}
                or risk_level in {"WARNING", "HIGH"}
            ):
                status = "WARNING"
            else:
                status = "NORMAL"

            display_usage = int(usage) if usage.is_integer() else round(usage, 1)

            resources.append({
                "resource_type": metric.get("resource_type", "unknown"),
                "resource_name": metric.get("resource_name", metric.get("resource_type", "unknown")),
                "current_usage": display_usage,
                "status": status,
                "trend": metric.get("trend", "unknown"),
                "warning_threshold": int(warning_threshold) if warning_threshold.is_integer() else warning_threshold,
                "critical_threshold": int(critical_threshold) if critical_threshold.is_integer() else critical_threshold,
            })

        critical_resources = [
            resource for resource in resources
            if resource["status"] == "CRITICAL"
        ]

        warning_resources = [
            resource for resource in resources
            if resource["status"] == "WARNING"
        ]

        if critical_resources:
            overall_status = "CRITICAL"
            customer_message = (
                "Service Temporarily Restricted — Some operations are "
                "temporarily unavailable due to a system resource issue. "
                "Please try again shortly."
            )
            message = customer_message
        elif warning_resources:
            overall_status = "WARNING"
            customer_message = (
                "Service Performance Warning — Some system resources are "
                "under pressure. DemoShop is monitoring the situation."
            )
            message = customer_message
        else:
            overall_status = "NORMAL"
            customer_message = "All monitored resources are operating within normal limits."
            message = customer_message

        return {
            "monitoring_available": True,
            "overall_status": overall_status,
            "message": message,
            "customer_message": customer_message,
            "resources": resources,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception:
        return {
            "monitoring_available": False,
            "overall_status": "UNKNOWN",
            "message": (
                "Resource monitoring is temporarily unavailable. "
                "DemoShop has not received a valid health status."
            ),
            "customer_message": "Resource monitoring is temporarily unavailable.",
            "resources": [],
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }


def is_resource_critical(health=None):
    """Return True if the overall resource status is CRITICAL."""
    if health is None:
        health = get_resource_health()
    return health.get("overall_status") == "CRITICAL"
