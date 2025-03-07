import json
import csv
import sys

def convert_json_to_csv(json_filename):
    """
    Convert the provided JSON file into a CSV format.
    """
    try:
        # Load the JSON data from the provided file
        with open(json_filename, 'r', encoding='utf-8') as json_file:
            test_cases = json.load(json_file)

        # Define the CSV filename based on the JSON file name
        csv_filename = json_filename.replace('.json', '.csv')

        # Define the headers for the CSV file
        headers = ["Test Case No", "Test Step", "Test Type", "Test Summary", "Test Data", "Expected Result"]

        # Write the test cases to a CSV file
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=headers)
            writer.writeheader()
            for case in test_cases:
                # Get Test Case ID if available, otherwise use Test Case No
                test_case_id = case.get("Test Case ID", f"TCTC{case['Test Case No'][2:]}")

                # Format Test Data as a string
                test_data = ", ".join([f"{key}: {value}" for key, value in case['Test Data'].items()])
                
                # Format Expected Result as a string
                expected_result = ", ".join([f"{key}: {value}" for key, value in case['Expected Result'].items()])
                
                # Write each test case to CSV
                writer.writerow({
                    "Test Case No": case["Test Case No"],
                    "Test Step": test_case_id,  # Use Test Case ID or default to a generated ID
                    "Test Type": "Manual",  # Assuming Test Type is always Manual
                    "Test Summary": case["Test Scenario"],  # Assuming "Test Scenario" is the test summary
                    "Test Data": test_data,
                    "Expected Result": expected_result
                })

        print(f"Conversion successful! CSV file saved as: {csv_filename}")
        return csv_filename
    except Exception as e:
        print(f"Error converting JSON to CSV: {str(e)}")
        return None


if __name__ == "__main__":
    # Get the JSON filename from the command-line argument
    if len(sys.argv) < 2:
        print("Usage: python convert_json_to_csv.py <json_filename>")
    else:
        json_filename = sys.argv[1]
        convert_json_to_csv(json_filename)
