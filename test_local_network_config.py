import importlib.util
import os
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MODULE_PATH = ROOT / 'bilol.py'


def load_module():
    spec = importlib.util.spec_from_file_location('bilol_module', MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules['bilol_module'] = module
    spec.loader.exec_module(module)
    return module


class LocalNetworkConfigTests(unittest.TestCase):
    def setUp(self):
        os.environ['CLIENT_URL'] = 'http://192.168.43.59:5000'
        os.environ['TFC_API_URL'] = 'http://192.168.43.59:5000'

    def test_local_network_origins_include_lan_ip(self):
        mod = load_module()
        origins = mod.build_local_origins()

        self.assertIn('http://192.168.43.59:5000', origins)
        self.assertIn('http://localhost:3000', origins)
        self.assertIn('http://127.0.0.1:3000', origins)

    def test_build_local_origins_handles_ip_from_host(self):
        os.environ.pop('CLIENT_URL', None)
        mod = load_module()
        origins = mod.build_local_origins()

        self.assertIn('http://192.168.43.59:5000', origins)

    def test_same_host_lan_requests_are_allowed_without_api_key(self):
        import app as app_module
        client = app_module.app.test_client()
        response = client.post(
            '/api/orders/new',
            base_url='http://192.168.43.59:5000',
            json={
                'customer': 'Test User',
                'customer_id': 'TEST-1',
                'food': 'Test food',
                'price': '25',
                'phone': '987654321',
                'delivery_type': 'pickup',
                'payment_method': 'cash',
                'delivery_address': ''
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()['ok'])


if __name__ == '__main__':
    unittest.main()
