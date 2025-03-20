pipeline {
    agent any

    environment {
        GIT_REPO = 'https://github.com/Pranjalshejal-gif/test_case_generator.git'
    }

    parameters {
        string(name: 'TEST_TOPIC', defaultValue: '', description: 'Enter the test topic (optional if using PDF or PlantUML)')
        string(name: 'NUM_CASES', defaultValue: '5', description: 'Enter the number of test cases')
        string(name: 'CSV_FILENAME', defaultValue: 'test_cases', description: 'Enter the CSV filename')
        string(name: 'PDF_FILE_PATH', defaultValue: '', description: 'Enter the absolute path of the PDF file (optional)')
        string(name: 'PLANTUML_IMAGE_PATH', defaultValue: '', description: 'Enter the absolute path of the PlantUML image file (optional)')
    }

    stages {
        stage('Clone Repository') {
            steps {
                git branch: 'main', url: "${GIT_REPO}"
            }
        }

        stage('Install System Dependencies') {
            steps {
                sh '''
                    echo "📌 Installing Tesseract OCR and required libraries..."
                    sudo apt-get update
                    sudo apt-get install -y tesseract-ocr libtesseract-dev \
                        libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev \
                        tcl8.6-dev tk8.6-dev python3-tk
                '''
            }
        }

        stage('Install Python Dependencies') {
            steps {
                sh '''
                    echo "📌 Installing Python dependencies..."
                    pip install --user --no-cache-dir --force-reinstall \
                        -r requirements.txt \
                        pytesseract pillow flask requests plantuml
                '''
            }
        }

        stage('Check PDF and PlantUML Image') {
            steps {
                script {
                    if (params.PDF_FILE_PATH) {
                        if (!fileExists(params.PDF_FILE_PATH)) {
                            error "❌ ERROR: PDF file not found at: ${params.PDF_FILE_PATH}"
                        }
                        echo "📄 PDF file found: ${params.PDF_FILE_PATH}"
                        env.UPLOADED_PDF = params.PDF_FILE_PATH
                    } else if (params.PLANTUML_IMAGE_PATH) {
                        if (!fileExists(params.PLANTUML_IMAGE_PATH)) {
                            error "❌ ERROR: PlantUML image file not found at: ${params.PLANTUML_IMAGE_PATH}"
                        }
                        echo "🖼️ PlantUML image file found: ${params.PLANTUML_IMAGE_PATH}"
                        env.UPLOADED_PLANTUML = params.PLANTUML_IMAGE_PATH
                    } else {
                        echo "ℹ️ No PDF or PlantUML image provided, defaulting to text-based test case generation."
                    }
                }
            }
        }

        stage('Start Flask Server') {
            steps {
                script {
                    echo "🚀 Starting Flask application..."
                    sh 'nohup python3 app.py > flask_output.log 2>&1 &'
                    sleep 5  

                    def max_retries = 5
                    def flaskRunning = "down"

                    for (int i = 0; i < max_retries; i++) {
                        flaskRunning = sh(script: "curl -s http://127.0.0.1:5000/health || echo 'down'", returnStdout: true).trim()
                        if (flaskRunning != "down") {
                            break
                        }
                        sleep 3
                    }

                    if (flaskRunning == "down") {
                        error "❌ ERROR: Flask server failed to start! Check flask_output.log"
                    }

                    echo "✅ Flask application started successfully!"
                }
            }
        }

        stage('Generate Test Cases') {
            steps {
                script {
                    def jsonResponse = ""

                    if (env.UPLOADED_PDF) {
                        echo "📄 Processing PDF file: ${env.UPLOADED_PDF}"
                        jsonResponse = sh(script: """
                            curl -s -X POST http://127.0.0.1:5000/generate_pdf \
                            -F "pdf_path=${env.UPLOADED_PDF}" \
                            -F "prompt=${params.TEST_TOPIC}" \
                            -F "num_cases=${params.NUM_CASES}" \
                            -F "filename=${params.CSV_FILENAME}"
                        """, returnStdout: true).trim()
                    } else if (env.UPLOADED_PLANTUML) {
                        echo "🖼️ Processing PlantUML image: ${env.UPLOADED_PLANTUML}"
                        jsonResponse = sh(script: """
                            curl -s -X POST http://127.0.0.1:5000/generate_plantuml \
                            -F "plantuml_path=${env.UPLOADED_PLANTUML}" \
                            -F "prompt=${params.TEST_TOPIC}" \
                            -F "num_cases=${params.NUM_CASES}" \
                            -F "filename=${params.CSV_FILENAME}"
                        """, returnStdout: true).trim()
                    } else {
                        echo "📝 Generating test cases from text..."
                        jsonResponse = sh(script: """
                            curl -s -X POST http://127.0.0.1:5000/generate \
                            -H "Content-Type: application/json" \
                            -d '{"topic": "${params.TEST_TOPIC}", "num_cases": ${params.NUM_CASES}, "filename": "${params.CSV_FILENAME}"}'
                        """, returnStdout: true).trim()
                    }

                    echo "🔹 API Response: ${jsonResponse}"

                    if (!jsonResponse || jsonResponse.contains("404 Not Found") || jsonResponse.contains("500 Internal Server Error")) {
                        error "❌ ERROR: API request failed. Check Flask logs."
                    }

                    def parsedResponse = readJSON text: jsonResponse
                    def csvFilepath = parsedResponse.csv_filepath ?: ''

                    if (!csvFilepath || csvFilepath == "null") {
                        error "❌ ERROR: Failed to extract CSV filepath from API response."
                    }

                    echo "✅ CSV file generated: ${csvFilepath}"
                    env.GENERATED_CSV = csvFilepath
                }
            }
        }

        stage('Download Test Cases CSV') {
            steps {
                script {
                    echo "⬇️ Downloading generated CSV file..."
                    def downloadResponse = sh(script: "curl -s -o ${params.CSV_FILENAME}.csv http://127.0.0.1:5000/download/${env.GENERATED_CSV} || echo 'error'", returnStdout: true).trim()

                    if (downloadResponse == "error") {
                        error "❌ ERROR: Failed to download CSV file. Check Flask logs."
                    }

                    echo "✅ CSV file downloaded successfully!"
                }
            }
        }
    }

    post {
        success {
            echo '✅ Pipeline executed successfully!'
        }
        failure {
            echo '❌ Pipeline failed! Check logs for issues.'
        }
    }
}
