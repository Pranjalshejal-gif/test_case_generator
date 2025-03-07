from flask import Flask, request, Response, render_template
import google.generativeai as genai
import pandas as pd
import json
import os

app = Flask(__name__)

# Set up Gemini API Key
GEMINI_API_KEY = "AIzaSyDMel3d4igbE_Zc_vfAekW7tQNP9bPdZzw"  # Replace with your actual API Key
genai.configure(api_key=GEMINI_API_KEY)


def generate_test_cases(prompt, num_cases=5):
    """
    Generate structured test cases using Gemini AI.
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-pro-latest")
        response = model.generate_content(f"""
            Generate {num_cases} structured test cases for: {prompt}.
            Return the test cases in JSON format with the following keys: 
            TCID, Test Summary, Description, Test Type, Test Step, Test Data, Expected Result, Labels, Priority.
        """)

        if not response or not hasattr(response, 'text'):
            return {"error": "Invalid response from Gemini API"}

        # Parse JSON response
        try:
            test_cases = json.loads(response.text)
            return test_cases
        except json.JSONDecodeError:
            return {"error": "Failed to parse AI response", "details": response.text}

    except Exception as e:
        return {"error": f"Error generating test cases: {str(e)}"}

def convert_to_csv(test_cases):
    """
    Convert test cases JSON data to CSV format.
    """
    df = pd.DataFrame(test_cases)
    csv_output = df.to_csv(index=False)
    return csv_output

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    topic = data.get("topic")
    num_cases = int(data.get("num_cases", 5))

    test_cases = generate_test_cases(topic, num_cases)

    if "error" in test_cases:
        return test_cases, 500

    csv_data = convert_to_csv(test_cases)

    response = Response(csv_data, mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=test_cases.csv'
    return response

if __name__ == "__main__":
    app.run(debug=True)
