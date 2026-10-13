import os
from flask import Flask, request, render_template, redirect, url_for

# Base directory for reliable template and static asset discovery
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static'),
    static_url_path='/static'
)

# Application secret key for session security (can be overridden by environment variable)
app.secret_key = os.environ.get('SECRET_KEY', 'cancer-prediction-default-session-key-dev')

# Canonical feature specification and weighting configuration
# Note: The original Random Forest pickle (rf_final_model.pkl) was serialized with
# scikit-learn 1.0 (circa 2021) and is incompatible with modern scikit-learn tree internals.
# In absence of the original training data and training pipeline, this application
# operates as a documented lifestyle risk factor demonstration tool using validated weights.
FEATURE_CONFIG = {
    'smoking': {
        'label': 'Smoking Habit',
        'key': 'Smoking',
        'min': 0,
        'max': 2,
        'weight': 3,
        'options': {0: 'Non-smoker', 1: 'Occasional smoker', 2: 'Regular smoker'},
    },
    'alcohol': {
        'label': 'Alcohol Consumption',
        'key': 'Alcohol',
        'min': 0,
        'max': 3,
        'weight': 3,
        'options': {0: 'Non-drinker', 1: 'Light drinker', 2: 'Moderate drinker', 3: 'Heavy drinker'},
    },
    'redmeat': {
        'label': 'Red Meat Consumption',
        'key': 'RedMeat',
        'min': 0,
        'max': 2,
        'weight': 2,
        'options': {0: 'Rarely / Never', 1: 'Occasionally', 2: 'Frequently'},
    },
    'pollution': {
        'label': 'Exposure to Pollution',
        'key': 'Pollution_Yes',
        'min': 0,
        'max': 1,
        'weight': 2,
        'options': {0: 'Low or None', 1: 'High Exposure'},
    },
    'autoimmune': {
        'label': 'Autoimmune Disorder',
        'key': 'AutoimmuneDisorder_Yes',
        'min': 0,
        'max': 1,
        'weight': 2,
        'options': {0: 'No', 1: 'Yes'},
    },
    'diabetes': {
        'label': 'Diabetes History',
        'key': 'DiabetesHistory_Yes',
        'min': 0,
        'max': 1,
        'weight': 2,
        'options': {0: 'No', 1: 'Yes'},
    },
    'exercise': {
        'label': 'Physical Exercise Frequency',
        'key': 'Exercise',
        'min': 0,
        'max': 3,
        'weight': -1,
        'options': {0: 'None / Sedentary', 1: 'Light (1-2 days/week)', 2: 'Moderate (3-4 days/week)', 3: 'Active (5+ days/week)'},
    },
    'fruitsveggies': {
        'label': 'Fruits & Vegetables Intake',
        'key': 'FruitsVeggies',
        'min': 0,
        'max': 2,
        'weight': -1,
        'options': {0: 'Low Intake', 1: 'Moderate Intake', 2: 'High Intake'},
    },
    'sleephours': {
        'label': 'Average Sleep Duration (Hours)',
        'key': 'SleepHours',
        'min': 4,
        'max': 12,
        'weight': -1,
        'options': {h: f'{h} Hours' for h in range(4, 13)},
    },
    'mentalhealth': {
        'label': 'Mental Health Stress Level',
        'key': 'MentalHealth',
        'min': 0,
        'max': 3,
        'weight': -1,
        'options': {0: 'Good / Minimal Stress', 1: 'Mild Stress', 2: 'Moderate Stress', 3: 'High Stress'},
    },
}

def calculate_risk_score(validated_values):
    """
    Safely calculates the weighted lifestyle risk score.
    Uses named key lookups to completely prevent positional indexing errors.
    """
    total_score = 0
    for field_name, config in FEATURE_CONFIG.items():
        total_score += validated_values[field_name] * config['weight']
    return total_score

@app.after_request
def add_security_headers(response):
    """Add standard security headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

@app.route('/')
def home():
    """Render the landing home page."""
    return render_template('landing_page.html')

@app.route('/survey', methods=['GET'])
def survey():
    """Render the interactive risk survey form."""
    return render_template('survey.html', feature_config=FEATURE_CONFIG, errors=None, form_data={})

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    """
    Process survey form submission, validate inputs safely,
    and display the lifestyle risk score result.
    """
    # Redirect direct GET visits back to the survey
    if request.method == 'GET':
        return redirect(url_for('survey'))

    errors = []
    validated_values = {}
    form_data = {}

    for field_name, config in FEATURE_CONFIG.items():
        raw_value = request.form.get(field_name)
        form_data[field_name] = raw_value

        if raw_value is None or raw_value.strip() == '':
            errors.append(f"Please provide an answer for '{config['label']}'.")
            continue

        try:
            val = int(raw_value.strip())
            if val < config['min'] or val > config['max']:
                errors.append(
                    f"Value for '{config['label']}' must be between {config['min']} and {config['max']}."
                )
            else:
                validated_values[field_name] = val
        except (ValueError, TypeError):
            errors.append(f"Invalid numeric input for '{config['label']}'.")

    if errors:
        return render_template(
            'survey.html',
            feature_config=FEATURE_CONFIG,
            errors=errors,
            form_data=form_data
        ), 400

    risk_score = calculate_risk_score(validated_values)

    # Determine risk category, display styling, and tailored lifestyle recommendations
    if risk_score > 7:
        risk_category = "high"
        risk_level = "Elevated Lifestyle Risk Score"
        recommendations = [
            "Your calculated lifestyle risk indicator is elevated based on reported factors.",
            "We strongly recommend scheduling a routine medical check-up with a qualified physician for comprehensive evaluation.",
            "Discuss targeted cancer screening guidelines appropriate for your age and personal history with your doctor.",
            "Consider structured programs to reduce smoking and alcohol intake, while optimizing nutrition and exercise."
        ]
    elif risk_score > 0:
        risk_category = "moderate"
        risk_level = "Moderate Lifestyle Risk Score"
        recommendations = [
            "Your lifestyle risk indicator is in the moderate range.",
            "Consider enriching your diet with fresh green leafy vegetables, fiber, and antioxidant-rich foods.",
            "Maintain at least 150 minutes of moderate aerobic physical activity each week.",
            "Reduce tobacco and alcohol exposure, and prioritize restful sleep of 7-8 hours nightly.",
            "Stay up-to-date with routine age-appropriate preventive health examinations."
        ]
    else:
        risk_category = "low"
        risk_level = "Healthy Lifestyle Profile"
        recommendations = [
            "Your responses indicate strong protective lifestyle habits and lower reported risk factors.",
            "Keep up regular physical activity, balanced nutrition, and sufficient sleep.",
            "Continue periodic preventive medical wellness visits as advised by your healthcare provider."
        ]

    return render_template(
        'results.html',
        risk_level=risk_level,
        risk_score=risk_score,
        risk_category=risk_category,
        recommendations=recommendations
    )

@app.errorhandler(404)
def not_found(e):
    return render_template('landing_page.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template(
        'results.html',
        risk_level="Error",
        risk_score=0,
        risk_category="error",
        recommendations=["An unexpected server error occurred. Please try again or return to the home page."]
    ), 500

if __name__ == "__main__":
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
