from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import json
import re

app = Flask(__name__)

# Hardcoded Gemini API Key (Replace with your actual key)
GEMINI_API_KEY = "AIzaSyCzqoM83e7dcghJ8Ky-nfydKwl4KPANF04"

genai.configure(api_key=GEMINI_API_KEY)

def generate_test_cases(prompt, num_cases=5):
    """
    Generate detailed test cases using Google Gemini AI, formatted as JSON.
    """
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        detailed_prompt = f"""
        Generate {num_cases} detailed test cases for: {prompt}.
        Each test case should include:
        - A concise Test Scenario.
        - Specific Test Data to be used.
        - The Expected Result of the test.
        - The test case number.

        Format the response as a JSON array of test cases, where each test case is a JSON object with keys:
        "Test Case Name", "Test Data", "Expected Result", "Test Case ID", "Action".
        """
        response = model.generate_content(detailed_prompt)

        if response and response.text:
            return response.text
        else:
            return None  # Return None if no response is received

    except Exception as e:
        return f"Error generating test cases: {str(e)}"

def parse_test_cases(ai_output):
    """
    Cleans AI output and parses it as JSON in the required format for Jira Xray.
    """
    try:
        if not ai_output:
            raise ValueError("AI response is empty.")

        # Remove Markdown-style code blocks if present
        cleaned_output = re.sub(r"```json|```", "", ai_output).strip()

        # Ensure it's valid JSON before parsing
        json_data = json.loads(cleaned_output)

        if not isinstance(json_data, list):
            raise ValueError("AI response is not a valid JSON array.")

        issue_updates = []
        for case in json_data:
            # Create test case fields according to the desired format
            test_case = {
                "fields": {
                    "project": { "key": "IMP" },
                    "summary": f"Test Case: {case.get('Test Case Name', 'Unnamed Test Case')}",
                    "description": f"Test Case ID: {case.get('Test Case ID', 'N/A')}\n"
                                   f"Test Data: {json.dumps(case.get('Test Data', {}), indent=2)}\n"
                                   f"Action: {case.get('Action', 'N/A')}\n"
                                   f"Expected Result: {case.get('Expected Result', 'N/A')}",
                    "issuetype": { "name": "Test" }
                }
            }
            issue_updates.append(test_case)

        return {"issueUpdates": issue_updates}

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        return {"error": f"Error parsing AI output: {e}"}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        topic = data.get("topic")
        num_cases = int(data.get("num_cases", 5))

        if not topic:
            return jsonify({"error": "No topic provided. Please provide a topic."}), 400

        ai_output = generate_test_cases(topic, num_cases)
        if ai_output is None or "Error" in ai_output:
            return jsonify({"error": ai_output or "AI did not return any test cases."}), 500

        parsed_test_cases = parse_test_cases(ai_output)
        if "error" in parsed_test_cases:
            return jsonify(parsed_test_cases), 500

        # Save the final JSON body in a variable
        json_payload = json.dumps(parsed_test_cases, indent=4)

        # Log the generated JSON payload (for debugging purposes)
        print("Generated JSON Payload:\n", json_payload)

        return jsonify({
            "message": "Test cases generated successfully.",
            "json_payload": parsed_test_cases
        })

    except Exception as e:
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
