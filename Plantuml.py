import requests

# Replace with your actual Gemini API key
GEMINI_API_KEY = "AIzaSyCzqoM83e7dcghJ8Ky-nfydKwl4KPANF04"

def generate_plantuml_diagram(test_scenario):
    """Generates PlantUML code for a given test scenario using Gemini API."""
    
    prompt = f"""
    Generate a PlantUML sequence diagram based on the following test scenario:

    {test_scenario}

    The diagram should clearly represent system components, user interactions, and expected responses.
    Provide only the PlantUML code inside @startuml and @enduml tags.
    """
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 500}
    }
    
    api_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

    response = requests.post(api_url, headers=headers, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        plantuml_code = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
        
        if "@startuml" in plantuml_code and "@enduml" in plantuml_code:
            return plantuml_code
        else:
            return "Error: Gemini response did not contain valid PlantUML code."
    else:
        return f"Error: API request failed with status code {response.status_code} - {response.text}"

# Example Test Scenario
test_scenario = """


Give the timeout test cases of below plant uml code @startuml
title BANL INWARD TRANSACTION
participant  "Other Bank" as otr#azure
participant  "CBS Middleware" as otr#azure
participant  "NPCI" as NPCI#azure
participant  "C" as NPCI#azure
box "IBK as a Beneficiary BANK "#lightcyan
participant "IMPS SWITCH" as switch #mistyrose
 
participant "IBK CBS" as CBS #mistyrose
end box
autonumber 1
otr ->NPCI :ReqBeneDetails initiated with\n(remitter and beneficiary details) 
NPCI ->switch :ReqBeneDetails initiated with\n( Beneficiary details (Acount & IFSC))
note right :switch validates the request

switch -> CBS :forward the request to Beneficiary Bank
autonumber stop
note right : Identify Acount Name 
autonumber resume
CBS -> switch : Beneficiary account name is \nretrieved from CBS
switch ->NPCI : RespBeneDetails forwarded
@enduml
 
"""

# Generate PlantUML code
plantuml_code = generate_plantuml_diagram(test_scenario)

# Save to a .puml file
if plantuml_code.startswith("@startuml"):
    with open("test_scenario.puml", "w") as file:
        file.write(plantuml_code)
    print("✅ PlantUML diagram saved as 'test_scenario.puml'")
else:
    print("❌", plantuml_code)
