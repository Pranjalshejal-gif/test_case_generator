from flask import Flask, request, jsonify, render_template, send_file
import google.generativeai as genai
import json
import re
import csv
import os
import fitz  # PyMuPDF for PDF text extraction
from datetime import datetime

app = Flask(__name__)

# Configure Gemini AI API
GEMINI_API_KEY = "AIzaSyCzqoM83e7dcghJ8Ky-nfydKwl4KPANF04"
genai.configure(api_key=GEMINI_API_KEY)

# Jenkins workspace path (adjust if needed)
WORKSPACE = os.getenv("WORKSPACE", "/var/lib/jenkins/workspace/Test_Suit")
if not os.path.exists(WORKSPACE):
    os.makedirs(WORKSPACE)


def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    try:
        doc = fitz.open(pdf_path)
        text = "\n".join(page.get_text("text") for page in doc).strip()
        return text if text else None
    except Exception as e:
        return None


def generate_test_cases(prompt, num_cases=5):
    """Generate test cases using Google Gemini AI."""
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        detailed_prompt = f"""
        Generate {num_cases} detailed test cases for: {prompt}.
        Each test case should include:
        - "Test Case ID": A unique identifier.
        - "Test Case Name": A descriptive name.
        - "Request": The API request payload.
        - "Response": The expected API response payload.
        - "Request Headers": The headers used in the request.
        - "Response Headers": The headers received in the response.
        - "Expected Message": The expected message outcome.
        - "Error Code": Any potential error code.
        - "Error Message": The error message details.
        Return ONLY the JSON array, without any extra text.
        """
        response = model.generate_content(detailed_prompt)
        return response.text.strip() if response and response.text else {"error": "No response from AI."}
    except Exception as e:
        return {"error": f"Error generating test cases: {str(e)}"}


def parse_test_cases(ai_output):
    """Parses AI output into JSON format."""
    try:
        cleaned_output = re.sub(r"```json|```", "", ai_output).strip()
        return json.loads(cleaned_output) if cleaned_output.startswith("[") and cleaned_output.endswith("]") else {"error": "Invalid JSON format."}
    except json.JSONDecodeError as e:
        return {"error": f"Error parsing AI output: {str(e)}"}


def save_as_csv(test_cases, user_filename):
    """Saves parsed test cases to a CSV file."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{user_filename}_{timestamp}.csv"
    filepath = os.path.join(WORKSPACE, filename)
    csv_headers = ["Test Case No", "Test Step", "Test Type", "Test Summary", "Test Data", "Expected Result"]

    try:
        with open(filepath, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=csv_headers)
            writer.writeheader()
            for index, case in enumerate(test_cases, start=1):
                test_data = {
                    "Request": case.get("Request", ""),
                    "Response": case.get("Response", ""),
                    "Request Headers": case.get("Request Headers", ""),
                    "Response Headers": case.get("Response Headers", "")
                }
                expected_result = {
                    "Expected Message": case.get("Expected Message", ""),
                    "Error Code": case.get("Error Code", ""),
                    "Error Message": case.get("Error Message", "")
                }
                writer.writerow({
                    "Test Case No": index,
                    "Test Step": case.get("Test Case ID", ""),
                    "Test Type": "Manual",
                    "Test Summary": case.get("Test Case Name", ""),
                    "Test Data": json.dumps(test_data),
                    "Expected Result": json.dumps(expected_result)
                })
        return filepath
    except Exception as e:
        return {"error": f"Error saving CSV: {str(e)}"}


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    """Generates test cases from text input."""
    data = request.json
    topic = data.get("topic")
    num_cases = int(data.get("num_cases", 5))
    user_filename = data.get("filename", "test_cases")

    if not topic:
        return jsonify({"error": "No topic provided."}), 400

    ai_output = generate_test_cases(topic, num_cases)
    if isinstance(ai_output, dict) and "error" in ai_output:
        return jsonify(ai_output), 500

    parsed_test_cases = parse_test_cases(ai_output)
    if isinstance(parsed_test_cases, dict) and "error" in parsed_test_cases:
        return jsonify(parsed_test_cases), 500

    csv_filepath = save_as_csv(parsed_test_cases, user_filename)
    return jsonify({"message": "Test cases generated successfully!", "csv_filename": os.path.basename(csv_filepath), "csv_filepath": csv_filepath})


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
