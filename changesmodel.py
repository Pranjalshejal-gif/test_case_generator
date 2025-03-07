import google.generativeai as genai
from datetime import datetime

# Set up the Gemini API Key
GEMINI_API_KEY = "AIzaSyBMa2DLLM8hXEiCl-VwGnPbnynFC6YGqY0"
genai.configure(api_key=GEMINI_API_KEY)

def generate_test_cases(prompt, num_cases=5):
    """
    Generate test cases using Google Gemini AI.
    """
    try:
        # Use a model from your available list
        model = genai.GenerativeModel("gemini-1.5-pro-latest")  # ✅ Updated model
        response = model.generate_content(f"Generate {num_cases} test cases for: {prompt}")
        
        return response.text if response else "No response received."

    except Exception as e:
        return f"Error generating test cases: {str(e)}"

if __name__ == "__main__":
    user_prompt = input("Enter the topic for test case generation: ")
    num_cases = int(input("Enter the number of test cases: "))

    print("\nGenerating test cases...\n")
    test_cases = generate_test_cases(user_prompt, num_cases)

    if "Error" in test_cases:
        print(test_cases)  # Print error message if any
    else:
        # Generate filename with current date and time
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"test_cases_{timestamp}.txt"

        # Save test cases to a file
        with open(filename, "w") as file:
            file.write(test_cases)

        print(f"\n✅ Test cases generated and saved to '{filename}'!")
