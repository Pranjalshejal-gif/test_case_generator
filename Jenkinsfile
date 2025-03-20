pipeline {
    agent any

    environment {
        GIT_REPO = 'https://github.com/Pranjalshejal-gif/test_case_generator.git'
    }

    parameters {
        string(name: 'TEST_TOPIC', defaultValue: '', description: 'Enter the test topic (optional if using PDF or Image)')
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

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 -m pip install --user --upgrade pip
                    python3 -m pip install --user -r requirements.txt
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
                        echo "✅ PDF file found: ${params.PDF_FILE_PATH}"
                        env.UPLOADED_PDF = params.PDF_FILE_PATH
                    } else {
                        echo "ℹ️ No PDF provided, checking for PlantUML image..."
                    }

                    if (params.PLANTUML_IMAGE_PATH) {
                        if (!fileExists(params.PLANTUML_IMAGE_PATH)) {
                            error "❌ ERROR: PlantUML image file not found at: ${params.PLANTUML_IMAGE_PATH}"
                        }
                        echo "✅ PlantUML image found: ${params.PLANTUML_IMAGE_PATH}"
                        env.UPLOADED_IMAGE = params.PLANTUML_IMAGE_PATH
                    } else {
                        echo "ℹ️ No PlantUML image provided, defaulting to text-based test case generation."
                    }
                }
            }
        }

        stage('Start Flask Server') {
            steps {
                script {
                    echo "🚀 Starting Flask application..."
                    sh '''
                        chmod -R 777 .
                        nohup python3 app.py > flask.log 2>&1 &
                        sleep 5
                    '''

                    def retries = 5
                    def success = false
                    
                    for (int i = 0; i < retries; i++) {
                        def response = sh(script: "curl -s http://127.0.0.1:5000/health || echo 'error'", returnStdout: true).trim()
                        echo "Flask Health Check Response: ${response}"
                        if (response.contains('"status":"up"')) {
                            echo "✅ Flask server is up!"
                            success = true
                            break
                        }
                        echo "Flask is still down, retrying in 3 seconds..."
                        sleep 3
                    }
                    
                    if (!success) {
                        sh 'cat flask.log'  // Show Flask logs to debug
                        error("❌ ERROR: Flask server failed to start!")
                    }
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
                    } else if (env.UPLOADED_IMAGE) {
                        echo "🖼️ Processing PlantUML image file: ${env.UPLOADED_IMAGE}"
                        jsonResponse = sh(script: """
                            curl -s -X POST http://127.0.0.1:5000/generate_image \
                            -F "image_path=${env.UPLOADED_IMAGE}" \
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
            echo '🎉 Pipeline executed successfully!'
        }
        failure {
            echo '❌ Pipeline failed! Check logs for issues.'
            sh 'cat flask.log'  // Show Flask logs on failure
        }
    }
}
