from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import json
import re

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
        "Test Case Name", "Test Data", "Expected Result", "Test Case ID", "Action".
        """
        response = model.generate_content(detailed_prompt)
        return response.text if response and response.text else "No response received."
    except Exception as e:
        return f"Error generating test cases: {str(e)}"

def parse_test_cases(ai_output):
    """
    Cleans AI output and parses it as JSON in the required format for Jira Xray.
    """
    try:
        # Remove Markdown-style code blocks if present
        cleaned_output = re.sub(r"```json|```", "", ai_output).strip()

        # Ensure it's valid JSON before parsing
        if cleaned_output.startswith("[") and cleaned_output.endswith("]"):
            json_data = json.loads(cleaned_output)
            issue_updates = []

            for case in json_data:
                # Create test case fields according to the desired format
                test_case = {
                    "fields": {
                        "project": { "key": "IMP" },
                        "summary": f"Test Case: {case['Test Case Name']}",
                        "description": f"Test Case ID: {case['Test Case ID']}\nTest Data: {json.dumps(case['Test Data'], indent=2)}\nAction: {case['Action']}\nExpected Result: {case['Expected Result']}",
                        "issuetype": { "name": "Test" }
                    }
                }
                issue_updates.append(test_case)

            # Return the structured JSON response
            return {"issueUpdates": issue_updates}
        else:
            raise ValueError("AI response is not a valid JSON array.")

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        print(f"Error parsing AI output: {e}")
        return {"error": str(e)}

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
    if "error" in parsed_test_cases:
        return jsonify({"error": parsed_test_cases["error"]}), 500

    # Save the final JSON body in a variable
    json_payload = json.dumps(parsed_test_cases, indent=4)
    
    # Log the generated JSON payload (for debugging purposes)
    print("JSONPayload:\n", json_payload)

    return jsonify({
        "message": "Test cases generated and saved.",
        "json_payload": json_payload
    })

if __name__ == "__main__":
    app.run(debug=True)
