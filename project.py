import google.generativeai as genai
from datetime import datetime
import os
import csv

# Load API Key from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("API Key not found! Set GEMINI_API_KEY environment variable.")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

def generate_test_cases(prompt, num_cases=5):
    """
    Generate test cases using Google Gemini AI.
    """
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(f"Generate {num_cases} test cases for: {prompt}")
        
        return response.text if response else "No response received."
    
    except Exception as e:
        return f"Error generating test cases: {str(e)}"

def save_test_cases_to_csv(test_cases, filename="test_cases.csv"):
    """
    Save generated test cases to a CSV file.
    """
    # Define header for the CSV file
    header = ["TCID", "Test Summary", "Description", "Test Type", "Test Step", "Test Data", "Expected Result", "Labels", "Priority"]

    # Write to CSV
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(header)  # Write header
        for case in test_cases:
            writer.writerow(case)

if __name__ == "__main__":
    user_prompt = input("Enter the topic for test case generation: ")
    num_cases = int(input("Enter the number of test cases: "))

    print("\nGenerating test cases...\n")
    test_cases = generate_test_cases(user_prompt, num_cases)

    if "Error" in test_cases:
        print(test_cases)  # Print error message if any
    else:
        # Split the response into individual test cases (assuming each test case is separated by newline)
        test_case_list = test_cases.split("\n")

        # Prepare test cases in CSV format (you might need to parse or modify the test cases depending on the response format)
        formatted_test_cases = []
        for i, case in enumerate(test_case_list, 1):
            formatted_test_cases.append([f"TC{i:03}", case, "Description placeholder", "Functional", "Step placeholder", "Data placeholder", "Expected result placeholder", "Labels placeholder", "Priority placeholder"])

        # Generate filename with current date and time
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"test_cases_{timestamp}.csv"

        # Save the test cases to CSV
        save_test_cases_to_csv(formatted_test_cases, filename)

        print(f"\nTest cases generated and saved to '{filename}'!")
