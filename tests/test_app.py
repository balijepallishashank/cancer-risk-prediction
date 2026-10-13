import unittest
import os
import sys

# Ensure repository root is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from cancer_project.app import app, FEATURE_CONFIG, calculate_risk_score
from api.index import app as vercel_app

class CancerPredictionAppTests(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.vercel_client = vercel_app.test_client()

    def test_01_landing_page_loads(self):
        """Verify home page loads successfully with 200 OK and expected content."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Cancer Risk Assessment', response.data)
        self.assertIn(b'Dr. Nanda Rajaneesh', response.data)
        self.assertIn(b'/survey', response.data)

    def test_02_survey_page_loads(self):
        """Verify survey page loads with 200 OK and contains all canonical form fields."""
        response = self.client.get('/survey')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Lifestyle Risk Survey', response.data)
        for field in FEATURE_CONFIG.keys():
            self.assertIn(f'name="{field}"'.encode('utf-8'), response.data)

    def test_03_predict_get_redirects_to_survey(self):
        """Verify direct GET request to /predict redirects to /survey instead of 405 error."""
        response = self.client.get('/predict', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Location'].endswith('/survey'))

    def test_04_valid_prediction_high_risk(self):
        """Verify valid submission with high risk factors produces elevated risk category."""
        high_risk_data = {
            'smoking': '2',
            'alcohol': '3',
            'redmeat': '2',
            'pollution': '1',
            'autoimmune': '1',
            'diabetes': '1',
            'exercise': '0',
            'fruitsveggies': '0',
            'sleephours': '5',
            'mentalhealth': '3'
        }
        # Expected calculation:
        # smoking: 2*3=6, alcohol: 3*3=9, redmeat: 2*2=4, pollution: 1*2=2,
        # autoimmune: 1*2=2, diabetes: 1*2=2, exercise: 0*-1=0, fruitsveggies: 0*-1=0,
        # sleephours: 5*-1=-5, mentalhealth: 3*-1=-3
        # Total = 6+9+4+2+2+2-5-3 = 17 (> 7 -> Elevated / High Risk)
        response = self.client.post('/predict', data=high_risk_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Elevated Lifestyle Risk Score', response.data)
        self.assertIn(b'Score: 17', response.data)
        self.assertIn(b'Retake Survey', response.data)
        self.assertIn(b'Back to Home', response.data)
        self.assertIn(b'Medical Disclaimer', response.data)

    def test_05_valid_prediction_low_risk(self):
        """Verify healthy lifestyle inputs produce low risk category."""
        low_risk_data = {
            'smoking': '0',
            'alcohol': '0',
            'redmeat': '0',
            'pollution': '0',
            'autoimmune': '0',
            'diabetes': '0',
            'exercise': '3',
            'fruitsveggies': '2',
            'sleephours': '8',
            'mentalhealth': '0'
        }
        # Calculation:
        # 0 + 0 + 0 + 0 + 0 + 0 - 3 - 2 - 8 - 0 = -13 (<= 0 -> Healthy / Low Risk)
        response = self.client.post('/predict', data=low_risk_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Healthy Lifestyle Profile', response.data)
        self.assertIn(b'Score: -13', response.data)

    def test_06_missing_field_handled_gracefully(self):
        """Verify missing form fields return 400 with helpful validation message, not 500."""
        incomplete_data = {
            'smoking': '1',
            'alcohol': '1'
            # Remaining 8 fields missing
        }
        response = self.client.post('/predict', data=incomplete_data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Please review the following', response.data)
        self.assertIn(b'Please provide an answer for', response.data)

    def test_07_invalid_numeric_input_handled_gracefully(self):
        """Verify non-numeric input returns 400 without crashing."""
        invalid_data = {
            'smoking': 'not-a-number',
            'alcohol': '1',
            'redmeat': '1',
            'pollution': '0',
            'autoimmune': '0',
            'diabetes': '0',
            'exercise': '2',
            'fruitsveggies': '1',
            'sleephours': '8',
            'mentalhealth': '1'
        }
        response = self.client.post('/predict', data=invalid_data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Invalid numeric input for', response.data)

    def test_08_out_of_range_input_handled_gracefully(self):
        """Verify out-of-range input returns 400 without crashing."""
        out_of_range_data = {
            'smoking': '99',  # max is 2
            'alcohol': '1',
            'redmeat': '1',
            'pollution': '0',
            'autoimmune': '0',
            'diabetes': '0',
            'exercise': '2',
            'fruitsveggies': '1',
            'sleephours': '8',
            'mentalhealth': '1'
        }
        response = self.client.post('/predict', data=out_of_range_data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'must be between', response.data)

    def test_09_security_headers_present(self):
        """Verify all standard HTTP security headers are set."""
        response = self.client.get('/')
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.headers.get('X-Frame-Options'), 'SAMEORIGIN')
        self.assertEqual(response.headers.get('X-XSS-Protection'), '1; mode=block')
        self.assertEqual(response.headers.get('Referrer-Policy'), 'strict-origin-when-cross-origin')

    def test_10_static_assets_serve_correctly(self):
        """Verify CSS and image static files serve with 200 OK."""
        css_resp = self.client.get('/static/style.css')
        self.assertEqual(css_resp.status_code, 200)

        img_resp = self.client.get('/static/images/cancer-book.jpg')
        self.assertEqual(img_resp.status_code, 200)

    def test_11_vercel_entrypoint_compatibility(self):
        """Verify api.index entrypoint functions identically to cancer_project.app."""
        response = self.vercel_client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Cancer Risk Assessment', response.data)

        survey_resp = self.vercel_client.get('/survey')
        self.assertEqual(survey_resp.status_code, 200)

if __name__ == '__main__':
    unittest.main()
