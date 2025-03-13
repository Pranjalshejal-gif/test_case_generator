from flask import Flask, request, jsonify, render_template, send_file
import google.generativeai as genai
import json
import re
import csv
import os
from datetime import datetime

app = Flask(__name__)

# Set up the Gemini API Key (Replace with your actual API key)
genai.configure(api_key="AIzaSyCzqoM83e7dcghJ8Ky-nfydKwl4KPANF04")

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
        # Remove unwanted code block markers if they exist
        cleaned_output = re.sub(r"```json|```", "", ai_output).strip()

        # Validate if response is a proper JSON array
        if cleaned_output.startswith("[") and cleaned_output.endswith("]"):
            return json.loads(cleaned_output)
        else:
            return {"error": "AI response is not a valid JSON array."}
    
    except (json.JSONDecodeError, ValueError) as e:
        return {"error": f"Error parsing AI output: {str(e)}"}

def save_as_csv(test_cases):
    """
    Saves parsed test cases to a CSV file with a timestamped filename.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"test_cases_{timestamp}.csv"

    csv_headers = ["Test Case No", "Test Step", "Test Type", "Test Summary", "Test Data", "Expected Result"]

    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
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

        return filename  # Return filename for download
    
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

    if not topic:
        return jsonify({"error": "No topic provided. Please provide a topic."}), 400

    ai_output = generate_test_cases(topic, num_cases)

    if isinstance(ai_output, dict) and "error" in ai_output:
        return jsonify(ai_output), 500

    parsed_test_cases = parse_test_cases(ai_output)
    
    if isinstance(parsed_test_cases, dict) and "error" in parsed_test_cases:
        return jsonify(parsed_test_cases), 500

    csv_filename = save_as_csv(parsed_test_cases)
    
    if isinstance(csv_filename, dict) and "error" in csv_filename:
        return jsonify(csv_filename), 500

    return jsonify({
        "message": "Test cases generated successfully!",
        "csv_filename": csv_filename,
        "test_cases": parsed_test_cases
    })

@app.route('/download/<filename>')
def download_file(filename):
    """
    Endpoint to download the generated CSV file.
    """
    try:
        return send_file(filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "File not found."}), 404

if __name__ == "__main__":
    app.run(debug=True)
