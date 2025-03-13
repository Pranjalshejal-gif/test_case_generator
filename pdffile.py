import fitz  # PyMuPDF for PDF reading
import requests
import json
import os
from datetime import datetime

# Replace with your actual Gemini API Key
GEMINI_API_KEY = "AIzaSyCzqoM83e7dcghJ8Ky-nfydKwl4KPANF04"

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    try:
        doc = fitz.open(pdf_path)
        text = "\n".join([page.get_text() for page in doc])
        return text.strip()
    except Exception as e:
        return f"Error reading PDF: {e}"

def generate_test_cases(pdf_text, custom_prompt):
    """Sends extracted text and custom prompt to Gemini API for test case generation."""
    prompt = f"""
    Based on the following extracted content from a PDF:

    {pdf_text[:2000]}  # Limiting to 2000 chars for API efficiency

    {custom_prompt}

    Generate test cases in the following JSON format:

    {{
        "fields": {{
            "project": {{ "key": "ABC" }},
            "summary": "<test case title>",
            "description": "<test case description>",
            "issuetype": {{ "name": "Test" }},
            "customfield_10200": {{ "value": "Manual" }},
            "customfield_10004": {{
                "steps": [
                    {{
                        "index": 1,
                        "fields": {{
                            "action": "<Step 1 Action>",
                            "data": "<Step 1 Input Data>",
                            "expected result": "<Step 1 Expected Result>"
                        }}
                    }},
                    {{
                        "index": 2,
                        "fields": {{
                            "action": "<Step 2 Action>",
                            "data": "<Step 2 Input Data>",
                            "expected result": "<Step 2 Expected Result>"
                        }}
                    }},
                    ...
                    {{
                        "index": N,
                        "fields": {{
                            "action": "<Step N Action>",
                            "data": "<Step N Input Data>",
                            "expected result": "<Step N Expected Result>"
                        }}
                    }}
                ]
            }}
        }}
    }}

    Ensure that the number of steps is appropriate for the test case complexity. **Do NOT limit it to just two steps.** 
    Generate **as many steps as needed** for a complete test case.
    Provide the JSON output **strictly in this format**, with no explanations, just the JSON response.
    """

    api_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2000}  # Increased limit
    }

    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        
        try:
            response_text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()

            # Print AI Response for Debugging
            print("🔍 AI Response:\n", response_text)

            # Validate JSON format
            if response_text.startswith("{") and response_text.endswith("}"):
                return response_text
            else:
                return "❌ Error: AI response is not in JSON format. Try modifying the prompt."
        except Exception as e:
            return f"❌ Error: Unexpected API response format - {str(e)}"
    else:
        return f"❌ Error: API request failed with status code {response.status_code} - {response.text}"

def save_test_cases_to_json(test_cases_text):
    """Saves test cases in JSON format with a timestamped filename."""
    try:
        test_cases = json.loads(test_cases_text)  # Convert AI output to Python dictionary

        # Create 'data' directory if it doesn't exist
        output_dir = os.path.join(os.getcwd(), "data")
        os.makedirs(output_dir, exist_ok=True)

        # Generate a timestamped filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_filename = f"test_cases_{timestamp}.json"

        # Define output file path
        output_path = os.path.join(output_dir, output_filename)

        # Debugging print
        print(f"📝 Saving JSON to: {output_path}")

        # Write to JSON file
        with open(output_path, "w") as json_file:
            json.dump(test_cases, json_file, indent=4)

        print(f"✅ Test cases saved successfully at: {output_path}")

    except json.JSONDecodeError:
        print("❌ Error: Could not parse JSON test cases from AI response")

# Main Execution
pdf_path = input("Enter the PDF file path: ")  # User inputs PDF file path
pdf_text = extract_text_from_pdf(pdf_path)

if pdf_text and not pdf_text.startswith("Error"):
    print("✅ PDF Text Extracted Successfully!")
    custom_prompt = input("Enter your prompt (e.g., 'Generate test cases for TypeScript'): ")
    
    test_cases = generate_test_cases(pdf_text, custom_prompt)

    if not test_cases.startswith("❌ Error"):
        save_test_cases_to_json(test_cases)
    else:
        print(test_cases)  # Display API error message
else:
    print("❌ Error: No text found in the PDF.")
