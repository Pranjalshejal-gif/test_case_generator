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
GEMINI_API_KEY = "AIzaSyAG-EcIMhPiHxiY7JJ9_Hc3ILWRJr0rOSA"  # Replace with actual key
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
 
 
def generate_test_cases(prompt, num_cases=5):
    """Generate test cases using Google Gemini AI."""
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        detailed_prompt = f"""
        Generate {num_cases} detailed test cases for: {prompt}.
        Each test case should be a JSON object with these fields:
        - "Test Case ID"
        - "Test Case Name"
        - "Request"
        - "Response"
        - "Request Headers"
        - "Response Headers"
        - "Expected Message"
        - "Error Code"
        - "Error Message"
        Return ONLY a JSON array.
        """
        response = model.generate_content(detailed_prompt)
        return response.text.strip() if response and response.text else {"error": "No response from AI."}
    except Exception as e:
        return {"error": f"Error generating test cases: {str(e)}"}
 
 
# def parse_test_cases(ai_output):
#     """Parses AI output into JSON format."""
#     try:
#         cleaned_output = re.sub(r"```json|```", "", ai_output).strip()
#         return json.loads(cleaned_output) if cleaned_output.startswith("[") and cleaned_output.endswith("]") else {"error": "Invalid JSON format."}
#     except json.JSONDecodeError as e:
#         return {"error": f"Error parsing AI output: {str(e)}"}
 
def parse_test_cases(ai_output):
    """Parses AI output into JSON format."""
    try:
        # Extract JSON from AI response
        json_match = re.search(r"\[.*\]", ai_output, re.DOTALL)
        if json_match:
            json_text = json_match.group(0)

            # Replace single quotes with double quotes if needed
            json_text = json_text.replace("'", '"')

            # Parse and return JSON
            return json.loads(json_text)
        else:
            return {"error": "No valid JSON found in AI response."}
    except json.JSONDecodeError as e:
        return {"error": f"Error parsing AI output: {str(e)}"} 

    
 
# def save_as_csv(test_cases, user_filename):
#     """Saves parsed test cases to a CSV file."""
#     timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#     filename = f"{user_filename}_{timestamp}.csv"
#     filepath = os.path.join(WORKSPACE, filename)
 
#     # ✅ Added "Test Step" column in headers
#     csv_headers = ["Test Case ID", "Test Summary","Test Step", "Test Type", "Test Data", "Expected Result"]
 
#     try:
#         with open(filepath, "w", newline="", encoding="utf-8") as file:
#             writer = csv.DictWriter(file, fieldnames=csv_headers)
#             writer.writeheader()
 
#             for case in test_cases:
#                 test_case_id = case.get("Test Case ID", "")  # ✅ Defined before use
                
#                 writer.writerow({
#                     "Test Case ID": test_case_id,
#                     "Test Summary": case.get("Test Case Name", ""),
#                     "Test Type": "Manual",
#                      "Test Step": {test_case_id} ,
#                     "Test Data": json.dumps({
#                         "Request": case.get("Request", {}),
#                         "Request Headers": case.get("Request Headers", {}),
#                         "Response": case.get("Response", {}),
#                         "Response Headers": case.get("Response Headers", {})
#                     }),
#                     "Expected Result": json.dumps({
#                         "Expected Message": case.get("Expected Message", ""),
#                         "Error Code": case.get("Error Code", ""),
#                         "Error Message": case.get("Error Message", "")
#                     }),
                    
#                 })
                
#         return filepath
#     except Exception as e:
#         return {"error": f"Error saving CSV: {str(e)}"}
 
def save_as_csv(test_cases, user_filename):
    """Saves parsed test cases to a CSV file in an editable format."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{user_filename}_{timestamp}.csv"
    filepath = os.path.join(WORKSPACE, filename)

    csv_headers = ["Test Case ID", "Test Summary", "Test Step", "Test Type", "Test Data", "Expected Result"]

    try:
        with open(filepath, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=csv_headers)
            writer.writeheader()

            for case in test_cases:
                writer.writerow({
                    "Test Case ID": case.get("Test Case ID", ""),
                    "Test Summary": case.get("Test Case Name", ""),
                    "Test Type": "Manual",
                    "Test Step": case.get("Test Case ID", ""),  # Assigning test case ID as test step
                    "Test Data": json.dumps({
                        "Request": case.get("Request", {}),
                        "Request Headers": case.get("Request Headers", {}),
                        "Response": case.get("Response", {}),
                        "Response Headers": case.get("Response Headers", {})
                    }, indent=4),  # Pretty format for readability
                    "Expected Result": json.dumps({
                        "Expected Message": case.get("Expected Message", ""),
                        "Error Code": case.get("Error Code", ""),
                        "Error Message": case.get("Error Message", "")
                    }, indent=4),  # Pretty format for readability
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
    num_cases = min(int(data.get("num_cases", 5)), 100)  # Limit to 100
 
    user_filename = data.get("filename", "test_cases")
 
    if not topic:
        return jsonify({"error": "No topic provided."}), 400
 
    return generate_and_save_test_cases(topic, num_cases, user_filename)
 
 
# @app.route('/generate_pdf', methods=['POST'])
# def generate_from_pdf():
#     """Generates test cases from a provided PDF file path."""
#     pdf_path = request.form.get("pdf_path")
 
#     if not pdf_path or not os.path.exists(pdf_path):
#         return jsonify({"error": "Invalid or missing PDF file path."}), 400
 
#     extracted_text = extract_text_from_pdf(pdf_path)
#     if not extracted_text:
#         return jsonify({"error": "Could not extract text from the provided PDF file."}), 500
 
#     # num_cases = int(request.form.get("num_cases", 5))
#     num_cases = min(int(request.form.get("num_cases", 5)), 100)  # Limit to 100
 
#     user_prompt = request.form.get("prompt", "Generate test cases based on this document.")
 
#     return generate_and_save_test_cases(f"{user_prompt}\n{extracted_text}", num_cases, os.path.splitext(os.path.basename(pdf_path))[0])
 
@app.route('/generate_pdf', methods=['POST'])
def generate_from_pdf():
    """Generates test cases from a provided PDF file path."""
    
    pdf_path = request.form.get("pdf_path")

    if not pdf_path or not os.path.exists(pdf_path):
        return jsonify({"error": "Invalid or missing PDF file path."}), 400

    extracted_text = extract_text_from_pdf(pdf_path)
    if not extracted_text:
        return jsonify({"error": "Could not extract text from the provided PDF file."}), 500

    num_cases = min(int(request.form.get("num_cases", 5)), 100)  # Limit to 100 test cases
    user_prompt = request.form.get("prompt", "Generate test cases based on this document.")

    print("\n🔹 Extracted PDF Text:\n", extracted_text[:1000])  # Print first 1000 chars for debugging

    ai_output = generate_test_cases(f"{user_prompt}\n{extracted_text}", num_cases)

    print("\n🔹 AI Raw Response:\n", ai_output)  # Debugging: Print raw AI response

    if not ai_output or isinstance(ai_output, dict) and "error" in ai_output:
        return jsonify({"error": "AI failed to generate test cases."}), 500

    parsed_test_cases = parse_test_cases(ai_output)

    print("\n🔹 Parsed Test Cases:\n", parsed_test_cases)  # Debugging: Print parsed test cases

    if isinstance(parsed_test_cases, dict) and "error" in parsed_test_cases:
        return jsonify(parsed_test_cases), 500

    csv_filepath = save_as_csv(parsed_test_cases, os.path.splitext(os.path.basename(pdf_path))[0])

    return jsonify({
        "message": "Test cases generated successfully!",
        "csv_filename": os.path.basename(csv_filepath),
        "csv_filepath": csv_filepath
    })
 
@app.route('/generate_image', methods=['POST'])
def generate_from_image():
    """Generates test cases from a provided PlantUML image."""
    image_path = request.form.get("image_path")
 
    if not image_path or not os.path.exists(image_path):
        return jsonify({"error": "Invalid or missing image file path."}), 400
 
    extracted_text = extract_text_from_image(image_path)
    if not extracted_text:
        return jsonify({"error": "Could not extract text from the provided image."}), 500
 
    # num_cases = int(request.form.get("num_cases", 5))
    num_cases = min(int(request.form.get("num_cases", 5)), 100)  # Limit to 100
 
    user_prompt = request.form.get("prompt", "Generate test cases based on this UML diagram.")
 
    return generate_and_save_test_cases(f"{user_prompt}\n{extracted_text}", num_cases, os.path.splitext(os.path.basename(image_path))[0])
 
@app.route('/generate_pdf_image', methods=['POST'])
def generate_from_pdf_and_image():
    """Generates test cases from both PDF and Image files."""
    
    pdf_path = request.form.get("pdf_path")
    image_path = request.form.get("image_path")
    
    if not pdf_path or not os.path.exists(pdf_path):
        return jsonify({"error": "Invalid or missing PDF file path."}), 400
    
    if not image_path or not os.path.exists(image_path):
        return jsonify({"error": "Invalid or missing image file path."}), 400
    
    # Extract text from both PDF and Image
    pdf_text = extract_text_from_pdf(pdf_path)
    image_text = extract_text_from_image(image_path)
    
    if not pdf_text and not image_text:
        return jsonify({"error": "Could not extract text from the provided files."}), 500
    
    combined_text = f"{pdf_text}\n{image_text}" if pdf_text and image_text else (pdf_text or image_text)
    
    num_cases = min(int(request.form.get("num_cases", 5)), 100)
    user_prompt = request.form.get("prompt", "Generate test cases based on these documents.")
    
    print("\n🔹 Combined Extracted Text:\n", combined_text[:1000])  # Print first 1000 chars for debugging
    
    ai_output = generate_test_cases(f"{user_prompt}\n{combined_text}", num_cases)
    
    print("\n🔹 AI Raw Response:\n", ai_output)  # Debugging: Print raw AI response
    
    if not ai_output or isinstance(ai_output, dict) and "error" in ai_output:
        return jsonify({"error": "AI failed to generate test cases."}), 500
    
    parsed_test_cases = parse_test_cases(ai_output)
    
    print("\n🔹 Parsed Test Cases:\n", parsed_test_cases)  # Debugging: Print parsed test cases
    
    if isinstance(parsed_test_cases, dict) and "error" in parsed_test_cases:
        return jsonify(parsed_test_cases), 500
    
    csv_filename = f"{os.path.splitext(os.path.basename(pdf_path))[0]}_{os.path.splitext(os.path.basename(image_path))[0]}"
    csv_filepath = save_as_csv(parsed_test_cases, csv_filename)
    
    return jsonify({
        "message": "Test cases generated successfully!",
        "csv_filename": os.path.basename(csv_filepath),
        "csv_filepath": csv_filepath
    })

 
def generate_and_save_test_cases(prompt, num_cases, filename):
    ai_output = generate_test_cases(prompt, num_cases)
    if isinstance(ai_output, dict) and "error" in ai_output:
        return jsonify(ai_output), 500
 
    parsed_test_cases = parse_test_cases(ai_output)
    if isinstance(parsed_test_cases, dict) and "error" in parsed_test_cases:
        return jsonify(parsed_test_cases), 500
 
    csv_filepath = save_as_csv(parsed_test_cases, filename)
    return jsonify({"message": "Test cases generated successfully!", "csv_filename": os.path.basename(csv_filepath), "csv_filepath": csv_filepath})
 
 
@app.route('/health', methods=['GET'])
def health_check():
    return "OK", 200
 
 
@app.route('/download/<filename>')
def download_file(filename):
    """Downloads the generated CSV file."""
    file_path = os.path.join(WORKSPACE, filename)
    try:
        return send_file(
            file_path,
            as_attachment=True,
            mimetype="text/csv",  # Explicitly setting MIME type for CSV
            cache_timeout=0  # Prevent caching issues
        )
    except FileNotFoundError:
        return jsonify({"error": "File not found."}), 404

 
 
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)