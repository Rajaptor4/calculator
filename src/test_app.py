import json
import unittest
from app import app, db, Calculation
from unittest.mock import patch


class TestApp(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @patch('app.db.session.add')
    @patch('app.db.session.commit')
    def test_calculate_add_with_mock(self, mock_commit, mock_add):
        response = self.app.post('/calculate', json={'num1': 2, 'num2': 3, 'operation': 'add'})
        data = json.loads(response.data)

        mock_add.assert_called()
        mock_commit.assert_called()
        self.assertEqual(data['result'], 5)

    def test_calculate_add(self):
        response = self.app.post('/calculate', json={'num1': 2, 'num2': 3, 'operation': 'add'})
        data = json.loads(response.data)
        self.assertEqual(data['result'], 5)

    def test_calculate_subtract(self):
        response = self.app.post('/calculate', json={'num1': 5, 'num2': 3, 'operation': 'subtract'})
        data = json.loads(response.data)
        self.assertEqual(data['result'], 2)

    def test_calculate_multiply(self):
        response = self.app.post('/calculate', json={'num1': 2, 'num2': 3, 'operation': 'multiply'})
        data = json.loads(response.data)
        self.assertEqual(data['result'], 6)

    def test_calculate_divide(self):
        response = self.app.post('/calculate', json={'num1': 6, 'num2': 3, 'operation': 'divide'})
        data = json.loads(response.data)
        self.assertEqual(data['result'], 2)

    def test_calculate_divide_by_zero(self):
        response = self.app.post('/calculate', json={'num1': 6, 'num2': 0, 'operation': 'divide'})
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Cannot divide by zero')

    def test_stats(self):
        self.app.post('/calculate', json={'num1': 2, 'num2': 3, 'operation': 'add'})
        self.app.post('/calculate', json={'num1': 5, 'num2': 3, 'operation': 'subtract'})
        response = self.app.get('/stats')
        data = json.loads(response.data)
        self.assertEqual(data['most_frequent_operation'], 'add')
        self.assertEqual(data['average_result'], 3.5)

    def test_integration_calculate_and_stats(self):
        response = self.app.post('/api/calculate', json={'num1': 5, 'num2': 3, 'operation': 'add'})
        data = json.loads(response.data)
        self.assertEqual(data['result'], 8)

        response = self.app.get('/api/stats')
        data = json.loads(response.data)
        self.assertEqual(data['most_frequent_operation'], 'add')
        self.assertEqual(data['average_result'], 8.0)

if __name__ == '__main__':
    unittest.main()
