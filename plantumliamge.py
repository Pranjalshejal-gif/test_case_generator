import requests
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re

# 🔹 Replace with your actual Gemini API key
GEMINI_API_KEY = "AIzaSyCzqoM83e7dcghJ8Ky-nfydKwl4KPANF04"

def preprocess_image(image_path):
    """Preprocess the image to improve OCR accuracy."""
    image = Image.open(image_path)

    # Convert to grayscale
    image = image.convert("L")

    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)

    # Apply sharpening filter
    image = image.filter(ImageFilter.SHARPEN)

    return image

def extract_text_from_image(image_path):
    """Extracts text from a UML diagram image using Tesseract OCR."""
    try:
        processed_image = preprocess_image(image_path)
        
        # Use OCR with better configurations
        extracted_text = pytesseract.image_to_string(processed_image, config="--psm 6")

        return extracted_text.strip()
    except Exception as e:
        return f"Error extracting text: {e}"

def clean_extracted_text(ocr_text):
    """Cleans the extracted text by removing unwanted spaces and broken lines."""
    
    # Remove extra spaces and fix line breaks
    cleaned_text = re.sub(r'\s+', ' ', ocr_text)
    
    # Remove unwanted symbols or distorted characters
    cleaned_text = re.sub(r'[_—–“”‘’|]', '', cleaned_text)

    return cleaned_text

def extract_interactions(plantuml_text):
    """Extracts actors, system components, and interactions from the PlantUML diagram text."""
    
    # Clean the extracted UML text
    clean_text = clean_extracted_text(plantuml_text)

    # Extract meaningful interactions
    interactions = re.findall(r'(\w+)\s*->\s*(\w+)\s*:\s*(.+)', clean_text)

    return interactions

def generate_test_cases_from_uml(plantuml_text):
    """Generates test cases from a given PlantUML sequence diagram using Gemini API."""

    interactions = extract_interactions(plantuml_text)
    
    if not interactions:
        return "Error: No valid interactions found in the UML diagram."

    prompt = f"""
    Based on the following PlantUML sequence diagram, generate detailed test cases:

    {plantuml_text}

    The test cases should be structured as follows:
    - **Test Case ID**
    - **Test Summary**
    - **Description**
    - **Preconditions**
    - **Test Steps**
    - **Expected Result**
    - **Priority**

    Cover both **valid and invalid scenarios**.
    """

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800}
    }
    
    api_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    response = requests.post(api_url, headers=headers, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        test_cases = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
        return test_cases if test_cases else "Error: No valid test cases generated."
    else:
        return f"Error: API request failed with status code {response.status_code} - {response.text}"

# 🔹 Provide the UML image file path here
uml_image_path = "plant.png"  # Replace with your actual image file

# Step 1: Extract UML text from the image
uml_text = extract_text_from_image(uml_image_path)

if "Error" not in uml_text:
    cleaned_text = clean_extracted_text(uml_text)
    print("✅ Cleaned UML Diagram Extracted:\n", cleaned_text)

    # Step 2: Generate test cases from the UML text
    test_cases = generate_test_cases_from_uml(cleaned_text)

    # Step 3: Save test cases to a file
    if "Error" not in test_cases:
        with open("generated_test_cases.txt", "w") as file:
            file.write(test_cases)
        print("✅ Test cases saved as 'generated_test_cases.txt'")
    else:
        print("❌", test_cases)
else:
    print("❌", uml_text)
