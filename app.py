from flask import Flask, request, jsonify, render_template, send_file
import google.generativeai as genai
import json
import re
import csv
import os
import PyPDF2
from datetime import datetime

app = Flask(__name__)

# Configure the Gemini API Key
GEMINI_API_KEY = "AIzaSyCzqoM83e7dcghJ8Ky-nfydKwl4KPANF04"  # Replace with your actual API key
genai.configure(api_key=GEMINI_API_KEY)

# Define Jenkins workspace path
WORKSPACE = os.getenv("WORKSPACE", "/var/lib/jenkins/workspace/Test_Suit")

def extract_text_from_pdf(pdf_path):
    """
    Extract text content from a given PDF file.
    """
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])
        return text
    except Exception as e:
        return {"error": f"Error reading PDF: {str(e)}"}

def generate_test_cases(prompt, num_cases=5):
    """
    Generate detailed test cases using Google Gemini AI, formatted as JSON.
    """
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        detailed_prompt = f"""
        Generate {num_cases} detailed test cases for: {prompt}.
        Each test case should include:
        - "Test Case ID": A unique identifier.
        - "Test Case Name": A descriptive name.
        - "Test Data": The input data.
        - "Expected Result": The expected outcome.
        
        Return ONLY the JSON array, without any code block formatting or additional text.
        """
        response = model.generate_content(detailed_prompt)

        if not response or not response.text:
            return {"error": "No response received from AI."}
        
        return response.text.strip()
    
    except Exception as e:
        return {"error": f"Error generating test cases: {str(e)}"}

def parse_test_cases(ai_output):
    """
    Parses AI output into a structured JSON list.
    """
    try:
        cleaned_output = re.sub(r"```json|```", "", ai_output).strip()
        if cleaned_output.startswith("[") and cleaned_output.endswith("]"):
            return json.loads(cleaned_output)
        else:
            return {"error": "AI response is not a valid JSON array."}
    except (json.JSONDecodeError, ValueError) as e:
        return {"error": f"Error parsing AI output: {str(e)}"}

def save_as_csv(test_cases, user_filename):
    """
    Saves parsed test cases to a CSV file inside the Jenkins workspace.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{user_filename}_{timestamp}.csv"  # Append timestamp to user-provided filename
    filepath = os.path.join(WORKSPACE, filename)

    csv_headers = ["Test Case No", "Test Step", "Test Type", "Test Summary", "Test Data", "Expected Result"]

    try:
        with open(filepath, mode="w", newline="", encoding="utf-8") as file:
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
        return filepath  # Return the full file path
    except Exception as e:
        return {"error": f"Error saving CSV: {str(e)}"}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    if 'file' in request.files:  # Handle PDF input
        file = request.files['file']
        if file.filename.endswith('.pdf'):
            pdf_path = os.path.join(WORKSPACE, file.filename)
            file.save(pdf_path)
            extracted_text = extract_text_from_pdf(pdf_path)
            if isinstance(extracted_text, dict) and "error" in extracted_text:
                return jsonify(extracted_text), 500
            topic = request.form.get("topic", "Extracted PDF Content")
        else:
            return jsonify({"error": "Unsupported file format. Only PDFs are allowed."}), 400
    else:  # Handle text input
        data = request.json
        topic = data.get("topic")
        if not topic:
            return jsonify({"error": "No topic provided. Please provide a topic."}), 400
        extracted_text = topic  # Use text input directly
    
    num_cases = int(request.form.get("num_cases", request.json.get("num_cases", 5)))
    user_filename = request.form.get("filename", request.json.get("filename", "test_cases"))
    
    ai_output = generate_test_cases(extracted_text, num_cases)
    if isinstance(ai_output, dict) and "error" in ai_output:
        return jsonify(ai_output), 500
    
    parsed_test_cases = parse_test_cases(ai_output)
    if isinstance(parsed_test_cases, dict) and "error" in parsed_test_cases:
        return jsonify(parsed_test_cases), 500
    
    csv_filepath = save_as_csv(parsed_test_cases, user_filename)
    if isinstance(csv_filepath, dict) and "error" in csv_filepath:
        return jsonify(csv_filepath), 500
    
    return jsonify({
        "message": "Test cases generated successfully!",
        "csv_filename": os.path.basename(csv_filepath),
        "csv_filepath": csv_filepath
    })

@app.route('/download/<filename>')
def download_file(filename):
    """
    Endpoint to download the generated CSV file.
    """
    file_path = os.path.join(WORKSPACE, filename)
    try:
        return send_file(file_path, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "File not found."}), 404

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
