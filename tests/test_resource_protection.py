import json
import sys
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import URLError

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app import create_app
from app.database.db import db
from app.models.product import Product
from app.models.order import Order
from app.models.user import User
from app.utils.jwt_handler import generate_token
from app.utils.resource_guard import get_resource_health, is_resource_critical


def make_metrics_payload(cpu=50, memory=55, filesystem=45, pod_memory=40, risk_level="NORMAL"):
    def status_for(usage):
        if usage >= 90:
            return "CRITICAL"
        if usage >= 80:
            return "WARNING"
        return "NORMAL"

    return {
        "metrics": [
            {
                "resource_type": "cpu",
                "resource_name": "CPU Usage",
                "current_usage": cpu,
                "status": status_for(cpu),
                "warning_threshold": 80,
                "critical_threshold": 90,
                "trend": "stable",
                "risk_level": "CRITICAL" if cpu >= 90 else ("WARNING" if cpu >= 80 else risk_level),
            },
            {
                "resource_type": "memory",
                "resource_name": "System Memory",
                "current_usage": memory,
                "status": status_for(memory),
                "warning_threshold": 80,
                "critical_threshold": 90,
                "trend": "stable",
                "risk_level": "CRITICAL" if memory >= 90 else ("WARNING" if memory >= 80 else risk_level),
            },
            {
                "resource_type": "filesystem",
                "resource_name": "Filesystem Storage",
                "current_usage": filesystem,
                "status": status_for(filesystem),
                "warning_threshold": 80,
                "critical_threshold": 90,
                "trend": "stable",
                "risk_level": "CRITICAL" if filesystem >= 90 else ("WARNING" if filesystem >= 80 else risk_level),
            },
            {
                "resource_type": "pod_memory",
                "resource_name": "Pod Memory",
                "current_usage": pod_memory,
                "status": status_for(pod_memory),
                "warning_threshold": 80,
                "critical_threshold": 90,
                "trend": "stable",
                "risk_level": "CRITICAL" if pod_memory >= 90 else ("WARNING" if pod_memory >= 80 else risk_level),
            },
        ]
    }


def mock_response(payload):
    mock = MagicMock()
    mock.read.return_value = json.dumps(payload).encode("utf-8")
    mock.__enter__.return_value = mock
    mock.__exit__.return_value = None
    return mock


class TestResourceHealthUnit(unittest.TestCase):
    @patch.dict("os.environ", {"LOGSHERLOCK_URL": ""})
    def test_no_logsherlock_url(self):
        health = get_resource_health()
        self.assertFalse(health["monitoring_available"])
        self.assertEqual(health["overall_status"], "UNKNOWN")
        self.assertIn("temporarily unavailable", health["customer_message"].lower())
        self.assertFalse(is_resource_critical(health))

    @patch("app.utils.resource_guard.urlopen")
    @patch.dict("os.environ", {"LOGSHERLOCK_URL": "http://mock-logsherlock"})
    def test_normal_metrics(self, mock_urlopen):
        payload = make_metrics_payload(cpu=45, memory=50, filesystem=60, pod_memory=40)
        mock_urlopen.return_value = mock_response(payload)

        health = get_resource_health()
        self.assertTrue(health["monitoring_available"])
        self.assertEqual(health["overall_status"], "NORMAL")
        self.assertFalse(is_resource_critical(health))

    @patch("app.utils.resource_guard.urlopen")
    @patch.dict("os.environ", {"LOGSHERLOCK_URL": "http://mock-logsherlock"})
    def test_warning_metrics(self, mock_urlopen):
        payload = make_metrics_payload(cpu=84, memory=60, filesystem=50, pod_memory=45)
        mock_urlopen.return_value = mock_response(payload)

        health = get_resource_health()
        self.assertTrue(health["monitoring_available"])
        self.assertEqual(health["overall_status"], "WARNING")
        self.assertIn("Service Performance Warning", health["customer_message"])
        self.assertFalse(is_resource_critical(health))

    @patch("app.utils.resource_guard.urlopen")
    @patch.dict("os.environ", {"LOGSHERLOCK_URL": "http://mock-logsherlock"})
    def test_critical_cpu(self, mock_urlopen):
        payload = make_metrics_payload(cpu=93, memory=60, filesystem=50, pod_memory=45)
        mock_urlopen.return_value = mock_response(payload)

        health = get_resource_health()
        self.assertTrue(health["monitoring_available"])
        self.assertEqual(health["overall_status"], "CRITICAL")
        self.assertIn("Service Temporarily Restricted", health["customer_message"])
        self.assertTrue(is_resource_critical(health))

    @patch("app.utils.resource_guard.urlopen")
    @patch.dict("os.environ", {"LOGSHERLOCK_URL": "http://mock-logsherlock"})
    def test_critical_memory(self, mock_urlopen):
        payload = make_metrics_payload(cpu=50, memory=94, filesystem=50, pod_memory=45)
        mock_urlopen.return_value = mock_response(payload)

        health = get_resource_health()
        self.assertEqual(health["overall_status"], "CRITICAL")
        self.assertTrue(is_resource_critical(health))

    @patch("app.utils.resource_guard.urlopen")
    @patch.dict("os.environ", {"LOGSHERLOCK_URL": "http://mock-logsherlock"})
    def test_critical_filesystem(self, mock_urlopen):
        payload = make_metrics_payload(cpu=50, memory=50, filesystem=91, pod_memory=45)
        mock_urlopen.return_value = mock_response(payload)

        health = get_resource_health()
        self.assertEqual(health["overall_status"], "CRITICAL")
        self.assertTrue(is_resource_critical(health))

    @patch("app.utils.resource_guard.urlopen")
    @patch.dict("os.environ", {"LOGSHERLOCK_URL": "http://mock-logsherlock"})
    def test_critical_pod_memory(self, mock_urlopen):
        payload = make_metrics_payload(cpu=50, memory=50, filesystem=50, pod_memory=92)
        mock_urlopen.return_value = mock_response(payload)

        health = get_resource_health()
        self.assertEqual(health["overall_status"], "CRITICAL")
        self.assertTrue(is_resource_critical(health))

    @patch("app.utils.resource_guard.urlopen")
    @patch.dict("os.environ", {"LOGSHERLOCK_URL": "http://mock-logsherlock"})
    def test_connection_error_returns_unknown_gracefully(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("Connection refused")

        health = get_resource_health()
        self.assertFalse(health["monitoring_available"])
        self.assertEqual(health["overall_status"], "UNKNOWN")
        self.assertFalse(is_resource_critical(health))

    @patch("app.utils.resource_guard.urlopen")
    @patch.dict("os.environ", {"LOGSHERLOCK_URL": "http://mock-logsherlock"})
    def test_timeout_returns_unknown_gracefully(self, mock_urlopen):
        mock_urlopen.side_effect = TimeoutError("Request timed out")

        health = get_resource_health()
        self.assertFalse(health["monitoring_available"])
        self.assertEqual(health["overall_status"], "UNKNOWN")
        self.assertFalse(is_resource_critical(health))

    @patch("app.utils.resource_guard.urlopen")
    @patch.dict("os.environ", {"LOGSHERLOCK_URL": "http://mock-logsherlock"})
    def test_malformed_json_returns_unknown_gracefully(self, mock_urlopen):
        mock = MagicMock()
        mock.read.return_value = b"<html>Service Unavailable</html>"
        mock.__enter__.return_value = mock
        mock.__exit__.return_value = None
        mock_urlopen.return_value = mock

        health = get_resource_health()
        self.assertFalse(health["monitoring_available"])
        self.assertEqual(health["overall_status"], "UNKNOWN")
        self.assertFalse(is_resource_critical(health))


class TestServiceProtectionIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

        with cls.app.app_context():
            user = User.query.filter_by(username="admin").first()
            if not user:
                user = User(username="admin", password="hashed_password", role="admin")
                db.session.add(user)
                db.session.commit()
            cls.token = generate_token(user)

    def setUp(self):
        with self.app.app_context():
            # Ensure a product with known stock exists
            product = Product.query.filter_by(name="Protection Test Product").first()
            if not product:
                product = Product(
                    name="Protection Test Product",
                    description="Used for automated testing",
                    price=29.99,
                    stock=20
                )
                db.session.add(product)
                db.session.commit()
            else:
                product.stock = 20
                db.session.commit()
            self.product_id = product.id

    def test_normal_metrics_order_succeeds(self):
        with patch("app.routes.orders.get_resource_health") as mock_health:
            mock_health.return_value = {
                "monitoring_available": True,
                "overall_status": "NORMAL",
                "customer_message": "All monitored resources are operating within normal limits.",
                "resources": []
            }

            initial_orders_count = len(self.client.get("/orders").get_json()["orders"])

            response = self.client.post(
                "/orders",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"product_id": self.product_id, "quantity": 2}
            )

            self.assertEqual(response.status_code, 201)
            data = response.get_json()
            self.assertTrue(data["success"])
            self.assertEqual(data["order"]["quantity"], 2)

            # Verify stock decremented
            with self.app.app_context():
                p = Product.query.get(self.product_id)
                self.assertEqual(p.stock, 18)

            # Verify order count incremented
            after_orders_count = len(self.client.get("/orders").get_json()["orders"])
            self.assertEqual(after_orders_count, initial_orders_count + 1)

    def test_warning_metrics_order_succeeds(self):
        with patch("app.routes.orders.get_resource_health") as mock_health:
            mock_health.return_value = {
                "monitoring_available": True,
                "overall_status": "WARNING",
                "customer_message": "Service Performance Warning — Some system resources are under pressure.",
                "resources": [{"resource_name": "CPU Usage", "current_usage": 85, "status": "WARNING"}]
            }

            response = self.client.post(
                "/orders",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"product_id": self.product_id, "quantity": 1}
            )

            self.assertEqual(response.status_code, 201)
            self.assertTrue(response.get_json()["success"])

            with self.app.app_context():
                p = Product.query.get(self.product_id)
                self.assertEqual(p.stock, 19)

    def test_critical_cpu_blocks_order(self):
        with patch("app.routes.orders.get_resource_health") as mock_health, \
             patch("app.routes.orders.log_event") as mock_log:
            mock_health.return_value = {
                "monitoring_available": True,
                "overall_status": "CRITICAL",
                "customer_message": "Service Temporarily Restricted — Some operations are temporarily unavailable due to a system resource issue. Please try again shortly.",
                "resources": [{"resource_name": "CPU Usage", "current_usage": 94, "status": "CRITICAL"}]
            }

            orders_before = len(self.client.get("/orders").get_json()["orders"])

            response = self.client.post(
                "/orders",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"product_id": self.product_id, "quantity": 2}
            )

            self.assertEqual(response.status_code, 503)
            data = response.get_json()
            self.assertFalse(data["success"])
            self.assertIn("Service Temporarily Restricted", data["message"])

            # Stock must NOT decrease
            with self.app.app_context():
                p = Product.query.get(self.product_id)
                self.assertEqual(p.stock, 20)

            # Order record must NOT be created
            orders_after = len(self.client.get("/orders").get_json()["orders"])
            self.assertEqual(orders_after, orders_before)

            # Log event must record ORDER_FAILED with RESOURCE_CRITICAL
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            self.assertEqual(call_args[0][0], "ORDER_FAILED")
            self.assertEqual(call_args[1]["reason"], "RESOURCE_CRITICAL")
            self.assertIn("CPU Usage (94%)", call_args[1]["affected_resources"])

    def test_critical_system_memory_blocks_order(self):
        with patch("app.routes.orders.get_resource_health") as mock_health:
            mock_health.return_value = {
                "monitoring_available": True,
                "overall_status": "CRITICAL",
                "customer_message": "Service Temporarily Restricted — Some operations are temporarily unavailable due to a system resource issue. Please try again shortly.",
                "resources": [{"resource_name": "System Memory", "current_usage": 92, "status": "CRITICAL"}]
            }

            response = self.client.post(
                "/orders",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"product_id": self.product_id, "quantity": 3}
            )

            self.assertEqual(response.status_code, 503)
            with self.app.app_context():
                p = Product.query.get(self.product_id)
                self.assertEqual(p.stock, 20)

    def test_critical_filesystem_blocks_order(self):
        with patch("app.routes.orders.get_resource_health") as mock_health:
            mock_health.return_value = {
                "monitoring_available": True,
                "overall_status": "CRITICAL",
                "customer_message": "Service Temporarily Restricted — Some operations are temporarily unavailable due to a system resource issue. Please try again shortly.",
                "resources": [{"resource_name": "Filesystem Storage", "current_usage": 96, "status": "CRITICAL"}]
            }

            response = self.client.post(
                "/orders",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"product_id": self.product_id, "quantity": 1}
            )

            self.assertEqual(response.status_code, 503)
            with self.app.app_context():
                p = Product.query.get(self.product_id)
                self.assertEqual(p.stock, 20)

    def test_critical_pod_memory_blocks_order(self):
        with patch("app.routes.orders.get_resource_health") as mock_health:
            mock_health.return_value = {
                "monitoring_available": True,
                "overall_status": "CRITICAL",
                "customer_message": "Service Temporarily Restricted — Some operations are temporarily unavailable due to a system resource issue. Please try again shortly.",
                "resources": [{"resource_name": "Pod Memory", "current_usage": 91, "status": "CRITICAL"}]
            }

            response = self.client.post(
                "/orders",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"product_id": self.product_id, "quantity": 1}
            )

            self.assertEqual(response.status_code, 503)
            with self.app.app_context():
                p = Product.query.get(self.product_id)
                self.assertEqual(p.stock, 20)

    def test_resource_recovery_allows_orders(self):
        # 1. State is CRITICAL -> blocked
        with patch("app.routes.orders.get_resource_health") as mock_health:
            mock_health.return_value = {
                "overall_status": "CRITICAL",
                "resources": [{"resource_name": "CPU Usage", "current_usage": 95, "status": "CRITICAL"}]
            }
            res_blocked = self.client.post(
                "/orders",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"product_id": self.product_id, "quantity": 1}
            )
            self.assertEqual(res_blocked.status_code, 503)

        # 2. State recovers to NORMAL -> allowed
        with patch("app.routes.orders.get_resource_health") as mock_health:
            mock_health.return_value = {
                "overall_status": "NORMAL",
                "resources": [{"resource_name": "CPU Usage", "current_usage": 40, "status": "NORMAL"}]
            }
            res_recovered = self.client.post(
                "/orders",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"product_id": self.product_id, "quantity": 1}
            )
            self.assertEqual(res_recovered.status_code, 201)
            self.assertTrue(res_recovered.get_json()["success"])

    def test_logsherlock_unavailable_does_not_block_orders(self):
        with patch("app.routes.orders.get_resource_health") as mock_health:
            mock_health.return_value = {
                "monitoring_available": False,
                "overall_status": "UNKNOWN",
                "customer_message": "Resource monitoring is temporarily unavailable.",
                "resources": []
            }

            response = self.client.post(
                "/orders",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"product_id": self.product_id, "quantity": 1}
            )

            self.assertEqual(response.status_code, 201)
            self.assertTrue(response.get_json()["success"])

    def test_health_route_accessible_during_critical(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "healthy")

    def test_resource_health_endpoint_accessible(self):
        with patch("app.routes.main.get_resource_health") as mock_health:
            mock_health.return_value = {
                "monitoring_available": True,
                "overall_status": "CRITICAL",
                "customer_message": "Service Temporarily Restricted — Some operations are temporarily unavailable due to a system resource issue. Please try again shortly.",
                "message": "Service Temporarily Restricted — Some operations are temporarily unavailable due to a system resource issue. Please try again shortly.",
                "resources": []
            }
            response = self.client.get("/resource-health")
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertTrue(data["success"])
            self.assertEqual(data["overall_status"], "CRITICAL")

    def test_standard_validation_preserved_when_critical(self):
        # Even if critical, invalid quantity or missing product validation executes
        with patch("app.routes.orders.get_resource_health") as mock_health:
            mock_health.return_value = {"overall_status": "CRITICAL", "resources": []}

            # Invalid product
            res_not_found = self.client.post(
                "/orders",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"product_id": 999999, "quantity": 1}
            )
            self.assertEqual(res_not_found.status_code, 404)

            # Invalid quantity
            res_bad_qty = self.client.post(
                "/orders",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"product_id": self.product_id, "quantity": 0}
            )
            self.assertEqual(res_bad_qty.status_code, 400)


if __name__ == "__main__":
    unittest.main()
