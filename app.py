from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import json
import re
from datetime import datetime
import csv
 
app = Flask(__name__)
 
# Set up the Gemini API Key
genai.configure(api_key="AIzaSyAU8yxgRk9k2_b7W6tlOotvgyVnNs4_31E")  # Replace with actual API key
 
def generate_test_cases(prompt, num_cases=5):
    """
    Generate detailed test cases using Google Gemini AI, formatted as JSON.
    """
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        detailed_prompt = f"""
        Generate {num_cases} detailed test cases for: {prompt}.
        For each test case, provide:
        - A concise Test Scenario.
        - Specific Test Data to be used.
        - The Expected Result of the test.
        - The test case number.
 
        Format the response as a JSON array of test cases, where each test case is a JSON object with keys:
        "Test Summary", "data", "expected", "number".
        """
        response = model.generate_content(detailed_prompt)
        return response.text if response and response.text else "No response received."
    except Exception as e:
        return f"Error generating test cases: {str(e)}"
 
# def parse_test_cases(ai_output):
#     """
#     Cleans AI output and parses it as JSON.
#     """
#     try:
#         cleaned_output = re.sub(r'```json|```', '', ai_output).strip()
#         if cleaned_output.startswith("[") and cleaned_output.endswith("]"):
#             json_data = json.loads(cleaned_output)
#             test_cases = []
#             for case in json_data:
#                 test_data = ", ".join([f"{key}: {value}" for key, value in case['data'].items()])
#                 expected_result = ", ".join([f"{key}: {value}" for key, value in case['expected'].items()])
                
#                 test_case = {
#                     "Test Case No": f"TC{case['number']:03}",
#                     "Test Step": f"TCTC{case['number']:03}",
#                     "Test Type": "Manual",  # Always "Manual" for every test case
#                     "Test Summary": case["scenario"],  # Changed from "Test Scenario" to "Test Summary"
#                     "Test Data": test_data,
#                     "Expected Result": expected_result
#                 }
#                 test_cases.append(test_case)
#             return test_cases
#         else:
#             raise ValueError("AI response is not a valid JSON array.")
#     except (json.JSONDecodeError, ValueError, KeyError) as e:
#         print(f"Error parsing AI output: {e}")
#         return []
 
def parse_test_cases(ai_output):
    """
    Cleans AI output and parses it as JSON.
    """
    try:
        # Remove Markdown-style code blocks if present
        cleaned_output = re.sub(r"```json|```", "", ai_output).strip()
 
        # Ensure it's valid JSON before parsing
        if cleaned_output.startswith("[") and cleaned_output.endswith("]"):
            json_data = json.loads(cleaned_output)
            test_cases = []
            for case in json_data:
                test_data = ", ".join([f"{key}: {value}" for key, value in case['data'].items()])
                expected_result = ", ".join([f"{key}: {value}" for key, value in case['expected'].items()])
 
                test_case = {
                    "Test Case No": case["number"],
                    "Test Step": case["number"],  # Moved from "Test Case ID"
                    "Test Type": "Manual",  # Always "Manual"
                    "Test Summary": case["Test Summary"],  # Renamed from "Test Scenario"
                    "Test Data": test_data,
                    "Expected Result": expected_result
                }
                test_cases.append(test_case)
            return test_cases
        else:
            raise ValueError("AI response is not a valid JSON array.")
 
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        print(f"Error parsing AI output: {e}")
        return []
 
def save_test_cases_to_json(test_cases):
    """
    Save the test cases (list of dictionaries) to a JSON file.
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"test_cases_{timestamp}.json"
        with open(filename, "w", encoding='utf-8') as f:
            json.dump(test_cases, f, indent=4, ensure_ascii=False)
        return filename
    except Exception as e:
        return f"Error saving test cases to JSON: {str(e)}"
 
def convert_json_to_csv(json_filename):
    """
    Convert the JSON test cases file to a CSV file.
    """
    try:
        csv_filename = json_filename.replace(".json", ".csv")
        with open(json_filename, "r", encoding='utf-8') as json_file:
            test_cases = json.load(json_file)
        with open(csv_filename, "w", newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=test_cases[0].keys())
            writer.writeheader()
            writer.writerows(test_cases)
        return csv_filename
    except Exception as e:
        return f"Error converting JSON to CSV: {str(e)}"
 
@app.route('/')
def home():
    return render_template('index.html')
 
@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    topic = data.get("topic")
    num_cases = int(data.get("num_cases", 5))
 
    if not topic:
        return jsonify({"error": "No topic provided. Please provide a topic."}), 400
 
    ai_output = generate_test_cases(topic, num_cases)
    if "Error" in ai_output or "No response" in ai_output:
        return jsonify({"error": ai_output}), 500
 
    test_cases = parse_test_cases(ai_output)
    if not test_cases:
        return jsonify({"error": "Failed to parse test cases."}), 500
 
    json_file = save_test_cases_to_json(test_cases)
    if "Error" in json_file:
        return jsonify({"error": json_file}), 500
 
    csv_file = convert_json_to_csv(json_file)
    if "Error" in csv_file:
        return jsonify({"error": csv_file}), 500
 
    return jsonify({
        "message": "Test cases generated and saved.",
        "json_filename": json_file,
        "csv_filename": csv_file,
        "test_cases": test_cases
    })
 
if __name__ == "__main__":
    app.run(debug=True)
 