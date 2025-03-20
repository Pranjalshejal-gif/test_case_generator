from flask import Flask, request, jsonify, render_template, send_file
import google.generativeai as genai
import json
import re
import csv
import os
import fitz  # PyMuPDF for PDF text extraction
import pytesseract  # OCR for image text extraction
from PIL import Image
from datetime import datetime

app = Flask(__name__)

# Configure Gemini AI API
GEMINI_API_KEY = "AIzaSyAU8yxgRk9k2_b7W6tlOotvgyVnNs4_31E"  # Replace with actual key
genai.configure(api_key=GEMINI_API_KEY)

# Jenkins workspace path
WORKSPACE = os.getenv("WORKSPACE", "/var/lib/jenkins/workspace/Test_Suit")
if not os.path.exists(WORKSPACE):
    os.makedirs(WORKSPACE)


def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    try:
        doc = fitz.open(pdf_path)
        text = "\n".join(page.get_text("text") for page in doc).strip()
        return text if text else None
    except Exception:
        return None


def extract_text_from_image(image_path):
    """Extracts text from an image using OCR (for PlantUML)."""
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text.strip() if text else None
    except Exception:
        return None


def generate_test_cases(prompt):
    """Generates test cases dynamically using AI and ensures JSON format."""
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        structured_prompt = f"""
        Generate test cases based on the following requirements:
        {prompt}
        
        Return the response in JSON format as a list of dictionaries. Each dictionary should have the following keys:
        - "Test Case ID"
        - "Test Case Name"
        - "Request"
        - "Request Headers"
        - "Response"
        - "Response Headers"
        - "Expected Message"
        - "Error Code"
        - "Error Message"

        Ensure the JSON output does not include markdown or additional text, just raw JSON.
        """

        response = model.generate_content(structured_prompt)

        if not response or not response.text:
            return {"error": "No response from AI."}

        cleaned_output = re.sub(r"```json|```", "", response.text.strip())  # Remove markdown formatting
        return cleaned_output  # Return cleaned JSON string

    except Exception as e:
        return {"error": f"Error generating test cases: {str(e)}"}


def parse_test_cases(ai_output):
    """Parses AI output into JSON format."""
    try:
        if isinstance(ai_output, dict):  # AI returned an error
            return ai_output

        cleaned_output = ai_output.strip()

        # Validate if it starts and ends with a list structure
        if not (cleaned_output.startswith("[") and cleaned_output.endswith("]")):
            return {"error": "Invalid JSON format: AI response is not a valid list."}

        return json.loads(cleaned_output)  # Convert string to JSON

    except json.JSONDecodeError as e:
        return {"error": f"Error parsing AI output: {str(e)}"}


def save_as_csv(test_cases, user_filename):
    """Saves parsed test cases to a CSV file."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{user_filename}_{timestamp}.csv"
    filepath = os.path.join(WORKSPACE, filename)

    csv_headers = ["Test Case ID", "Test Summary", "Test Step", "Test Type", "Test Data", "Expected Result"]

    try:
        with open(filepath, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=csv_headers)
            writer.writeheader()

            for case in test_cases:
                test_case_id = case.get("Test Case ID", "")

                writer.writerow({
                    "Test Case ID": test_case_id,
                    "Test Summary": case.get("Test Case Name", ""),
                    "Test Type": "Manual",
                    "Test Step": test_case_id,
                    "Test Data": json.dumps({
                        "Request": case.get("Request", {}),
                        "Request Headers": case.get("Request Headers", {}),
                        "Response": case.get("Response", {}),
                        "Response Headers": case.get("Response Headers", {})
                    }),
                    "Expected Result": json.dumps({
                        "Expected Message": case.get("Expected Message", ""),
                        "Error Code": case.get("Error Code", ""),
                        "Error Message": case.get("Error Message", "")
                    }),
                })
                
        return filepath
    except Exception as e:
        return {"error": f"Error saving CSV: {str(e)}"}


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    """Generates test cases from text input based on user prompt."""
    data = request.json or {}  
    topic = data.get("topic")  
    user_filename = data.get("filename", "test_cases")

    if not topic:
        return jsonify({"error": "No topic provided."}), 400

    return generate_and_save_test_cases(topic, user_filename)


@app.route('/generate_pdf', methods=['POST'])
def generate_from_pdf():
    """Generates test cases from a provided PDF file path."""
    pdf_path = request.form.get("pdf_path")

    if not pdf_path or not os.path.exists(pdf_path):
        return jsonify({"error": "Invalid or missing PDF file path."}), 400

    extracted_text = extract_text_from_pdf(pdf_path)
    if not extracted_text:
        return jsonify({"error": "Could not extract text from the provided PDF file."}), 500

    user_prompt = request.form.get("prompt", "Generate test cases based on this document.")

    return generate_and_save_test_cases(f"{user_prompt}\n{extracted_text}", os.path.splitext(os.path.basename(pdf_path))[0])


@app.route('/generate_image', methods=['POST'])
def generate_from_image():
    """Generates test cases from a provided PlantUML image."""
    image_path = request.form.get("image_path")

    if not image_path or not os.path.exists(image_path):
        return jsonify({"error": "Invalid or missing image file path."}), 400

    extracted_text = extract_text_from_image(image_path)
    if not extracted_text:
        return jsonify({"error": "Could not extract text from the provided image."}), 500

    user_prompt = request.form.get("prompt", "Generate test cases based on this UML diagram.")

    return generate_and_save_test_cases(f"{user_prompt}\n{extracted_text}", os.path.splitext(os.path.basename(image_path))[0])

@app.route('/generate_combined', methods=['POST'])
def generate_from_multiple_sources():
    """Generates test cases from a combination of text, PDF, and image input."""
    data = request.json or {}
    topic = data.get("topic", "")
    pdf_path = data.get("pdf_path", "")
    image_path = data.get("image_path", "")
    user_filename = data.get("filename", "test_cases")

    combined_prompt = topic.strip()

    if pdf_path and os.path.exists(pdf_path):
        pdf_text = extract_text_from_pdf(pdf_path)
        if pdf_text:
            combined_prompt += f"\n\n### Extracted from PDF:\n{pdf_text}"

    if image_path and os.path.exists(image_path):
        image_text = extract_text_from_image(image_path)
        if image_text:
            combined_prompt += f"\n\n### Extracted from Image:\n{image_text}"

    if not combined_prompt.strip():
        return jsonify({"error": "No valid input provided."}), 400

    return generate_and_save_test_cases(combined_prompt, user_filename)



def generate_and_save_test_cases(prompt, filename):
    """Generates test cases dynamically based on the user prompt."""
    ai_output = generate_test_cases(prompt)  # AI determines the number of test cases

    if isinstance(ai_output, dict) and "error" in ai_output:
        return jsonify(ai_output), 500

    parsed_test_cases = parse_test_cases(ai_output)
    if isinstance(parsed_test_cases, dict) and "error" in parsed_test_cases:
        return jsonify(parsed_test_cases), 500

    csv_filepath = save_as_csv(parsed_test_cases, filename)
    return jsonify({
        "message": "Test cases generated successfully!",
        "csv_filename": os.path.basename(csv_filepath),
        "csv_filepath": csv_filepath
    })


@app.route('/health', methods=['GET'])
def health_check():
    return "OK", 200


@app.route('/download/<filename>')
def download_file(filename):
    """Downloads the generated CSV file."""
    file_path = os.path.join(WORKSPACE, filename)
    try:
        return send_file(file_path, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "File not found."}), 404


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
