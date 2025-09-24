import unittest
from app import app, is_prime, factorial, history

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        history.clear()

    def test_is_prime(self):
        self.assertFalse(is_prime(1))
        self.assertTrue(is_prime(2))
        self.assertTrue(is_prime(7))
        self.assertFalse(is_prime(8))

    def test_factorial(self):
        self.assertEqual(factorial(5), 120)
        self.assertEqual(factorial(0), 1)
        self.assertEqual(factorial(20), "too large")

    def test_home_get(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Enter an integer', response.data)

    def test_home_post_valid(self):
        response = self.app.post('/', data={'number': '5'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'odd', response.data)
        self.assertIn(b'120', response.data)
        self.assertIn(b'Yes', response.data)

    def test_home_post_invalid(self):
        response = self.app.post('/', data={'number': 'abc'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'valid integer', response.data)

    def test_history_empty(self):
        response = self.app.get('/history')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'No history', response.data)

    def test_history_with_data(self):
        self.app.post('/', data={'number': '4'})
        response = self.app.get('/history')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'even', response.data)

    def test_history_limit(self):
        for i in range(12):
            self.app.post('/', data={'number': str(i)})
        self.assertEqual(len(history), 10)

if __name__ == '__main__':
    unittest.main()