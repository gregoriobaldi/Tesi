import unittest
from app import is_prime, factorial, app

class TestAppFunctions(unittest.TestCase):
    def test_is_prime(self):
        self.assertFalse(is_prime(-1))
        self.assertFalse(is_prime(0))
        self.assertFalse(is_prime(1))
        self.assertTrue(is_prime(2))
        self.assertTrue(is_prime(3))
        self.assertFalse(is_prime(4))
        self.assertTrue(is_prime(13))
        self.assertFalse(is_prime(100))

    def test_factorial(self):
        self.assertEqual(factorial(0), 1)
        self.assertEqual(factorial(1), 1)
        self.assertEqual(factorial(5), 120)
        self.assertEqual(factorial(10), 3628800)
        self.assertEqual(factorial(19), 121645100408832000)
        self.assertEqual(factorial(20), "too large")
        self.assertEqual(factorial(100), "too large")
        with self.assertRaises(ValueError):
            factorial(-5)

class TestFlaskApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_home_get(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Even or Odd Checker', response.data)

    def test_home_post_even(self):
        response = self.app.post('/', data={'number': '4'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Even or Odd: Even', response.data)
        self.assertIn(b'Factorial: 24', response.data)
        self.assertIn(b'Prime: False', response.data)

    def test_home_post_odd_prime(self):
        response = self.app.post('/', data={'number': '7'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Even or Odd: Odd', response.data)
        self.assertIn(b'Factorial: 5040', response.data)
        self.assertIn(b'Prime: True', response.data)

    def test_history_page(self):
        response = self.app.get('/history')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'History of Inputs', response.data)

if __name__ == '__main__':
    unittest.main()