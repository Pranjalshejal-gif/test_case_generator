import google.generativeai as genai

# Configure API key
genai.configure(api_key="AIzaSyBMa2DLLM8hXEiCl-VwGnPbnynFC6YGqY0")

# List available models
models = genai.list_models()

# Print model names
for model in models:
    print(model.name)
