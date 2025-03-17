from flask import Flask, request, jsonify, render_template, send_file
import google.generativeai as genai
import json
import re
import csv
import os
import fitz  # PyMuPDF for PDF text extraction
from datetime import datetime

app = Flask(__name__)

# Hardcoded Gemini API Key (Not recommended for production)
GEMINI_API_KEY = "AIzaSyCzqoM83e7dcghJ8Ky-nfydKwl4KPANF04"
genai.configure(api_key=GEMINI_API_KEY)

# Define Jenkins workspace path
WORKSPACE = os.getenv("WORKSPACE", "/var/lib/jenkins/workspace/Test_Suit")


def extract_text_from_pdf(pdf_path):
    """Extracts text content from a PDF file."""
    try:
        doc = fitz.open(pdf_path)
        text = "".join(page.get_text("text") + "\n" for page in doc).strip()
        return text if text else None
    except Exception:
        return None


def generate_test_cases(prompt, num_cases=5):
    """Generate detailed test cases using Google Gemini AI, formatted as JSON."""
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        detailed_prompt = f"""
        Generate {num_cases} detailed test cases for: {prompt}.
        Each test case should include:
        - "Test Case ID": A unique identifier.
        - "Test Case Name": A descriptive name.
        - "Test Data": The input data.
        - "Expected Result": The expected outcome.
        Return ONLY the JSON array, without any extra text.
        """
        response = model.generate_content(detailed_prompt)
        return response.text.strip() if response and response.text else {"error": "No response from AI."}
    except Exception as e:
        return {"error": f"Error generating test cases: {str(e)}"}


def parse_test_cases(ai_output):
    """Parses AI output into a structured JSON list."""
    try:
        cleaned_output = re.sub(r"```json|```", "", ai_output).strip()
        return json.loads(cleaned_output) if cleaned_output.startswith("[") and cleaned_output.endswith("]") else {"error": "Invalid JSON format."}
    except (json.JSONDecodeError, ValueError) as e:
        return {"error": f"Error parsing AI output: {str(e)}"}


def save_as_csv(test_cases, user_filename):
    """Saves parsed test cases to a CSV file inside the Jenkins workspace."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{user_filename}_{timestamp}.csv"
    filepath = os.path.join(WORKSPACE, filename)
    csv_headers = ["Test Case No", "Test Step", "Test Type", "Test Summary", "Test Data", "Expected Result"]

    try:
        with open(filepath, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=csv_headers)
            writer.writeheader()
            for index, case in enumerate(test_cases, start=1):
                writer.writerow({
                    "Test Case No": index,
                    "Test Step": case.get("Test Case ID", ""),
                    "Test Type": "Manual",
                    "Test Summary": case.get("Test Case Name", ""),
                    "Test Data": json.dumps(case.get("Test Data", {})),
                    "Expected Result": json.dumps(case.get("Expected Result", {}))
                })
        return filepath
    except Exception as e:
        return {"error": f"Error saving CSV: {str(e)}"}


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
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


@app.route('/generate_pdf', methods=['POST'])
def generate_from_pdf():
    if 'pdf_file' not in request.files:
        return jsonify({"error": "No PDF file provided."}), 400

    pdf_file = request.files['pdf_file']
    user_prompt = request.form.get("prompt", "Generate test cases based on this document.")
    num_cases = int(request.form.get("num_cases", 5))
    user_filename = request.form.get("filename", "test_cases")
    pdf_path = os.path.join(WORKSPACE, pdf_file.filename)
    pdf_file.save(pdf_path)

    extracted_text = extract_text_from_pdf(pdf_path)
    if not extracted_text:
        return jsonify({"error": "Could not extract text from the uploaded PDF."}), 500

    ai_output = generate_test_cases(f"{user_prompt}\n{extracted_text}", num_cases)
    if isinstance(ai_output, dict) and "error" in ai_output:
        return jsonify(ai_output), 500

    parsed_test_cases = parse_test_cases(ai_output)
    if isinstance(parsed_test_cases, dict) and "error" in parsed_test_cases:
        return jsonify(parsed_test_cases), 500

    csv_filepath = save_as_csv(parsed_test_cases, user_filename)
    return jsonify({"message": "Test cases generated successfully from PDF!", "csv_filename": os.path.basename(csv_filepath), "csv_filepath": csv_filepath})


@app.route('/health', methods=['GET'])
def health_check():
    return "OK", 200


@app.route('/download/<filename>')
def download_file(filename):
    file_path = os.path.join(WORKSPACE, filename)
    try:
        return send_file(file_path, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "File not found."}), 404


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
