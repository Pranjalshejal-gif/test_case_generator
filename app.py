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

        Return the response strictly as a **JSON array**, without any code block formatting.
        """
        response = model.generate_content(detailed_prompt)

        # Ensure response is valid
        return response.text if response and response.text else "No response received."
    
    except Exception as e:
        return f"Error generating test cases: {str(e)}"

def parse_test_cases(ai_output):
    """
    Parses AI output into a structured JSON list.
    """
    try:
        # Remove unwanted code block markers (```json ... ```)
        cleaned_output = re.sub(r"```json|```", "", ai_output).strip()

        # Validate if response is a proper JSON array
        if cleaned_output.startswith("[") and cleaned_output.endswith("]"):
            return json.loads(cleaned_output)
        else:
            raise ValueError("AI response is not a valid JSON array.")
    
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error parsing AI output: {e}")
        return None

def save_as_csv(test_cases):
    """
    Saves parsed test cases to a CSV file with a timestamped filename.
    """
    # Generate filename with current date and time
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"test_cases_{timestamp}.csv"

    csv_headers = ["Test Case No", "Test Step", "Test Type", "Test Summary", "Test Data", "Expected Result"]

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=csv_headers)
        writer.writeheader()

        for index, case in enumerate(test_cases, start=1):
            writer.writerow({
                "Test Case No": index,
                "Test Step": case.get("Test Case ID", ""),  # Test Step = Test Case ID
                "Test Type": "Manual",  # Always "Manual"
                "Test Summary": case.get("Test Case Name", ""),  # Test Summary = Test Case Name
                "Test Data": json.dumps(case.get("Test Data", {})),  # Convert dictionary to JSON string
                "Expected Result": case.get("Expected Result", "")
            })

    return filename  # Return filename for download

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

    parsed_test_cases = parse_test_cases(ai_output)
    if parsed_test_cases is None:
        return jsonify({"error": "Failed to parse AI response into JSON."}), 500

    # Save test cases as CSV with a dynamic filename
    csv_filename = save_as_csv(parsed_test_cases)

    # Provide JSON response before downloading
    return jsonify({
        "message": "Test cases generated successfully!",
        "csv_filename": csv_filename
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
