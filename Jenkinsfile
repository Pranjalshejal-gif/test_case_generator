pipeline {
    agent any

    environment {
        GIT_REPO = 'https://github.com/Pranjalshejal-gif/test_case_generator.git'
    }

    parameters {
        string(name: 'TEST_TOPIC', defaultValue: '', description: 'Enter the test topic (optional if using PDF)')
        string(name: 'NUM_CASES', defaultValue: '5', description: 'Enter the number of test cases')
        string(name: 'CSV_FILENAME', defaultValue: 'test_cases', description: 'Enter the CSV filename')
        string(name: 'PDF_FILE_PATH', defaultValue: '', description: 'Enter the absolute path of the PDF file (optional)')
    }

    stages {
        stage('Clone Repository') {
            steps {
                git branch: 'main', url: "${GIT_REPO}"
            }
        }

        stage('Install Dependencies') {
            steps {
                sh 'pip install --user -r requirements.txt'
                sh 'pip install --user pymupdf'
            }
        }

        stage('Check PDF File') {
            steps {
                script {
                    if (params.PDF_FILE_PATH) {
                        if (!fileExists(params.PDF_FILE_PATH)) {
                            error "❌ ERROR: PDF file not found at: ${params.PDF_FILE_PATH}"
                        }
                        echo "✅ PDF file found at: ${params.PDF_FILE_PATH}"
                        env.UPLOADED_PDF = params.PDF_FILE_PATH
                    } else {
                        echo "⚠️ No PDF file provided, proceeding with text-based test case generation."
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

                    def flaskRunning = ""
                    for (int i = 0; i < 3; i++) {
                        flaskRunning = sh(script: "curl -s http://127.0.0.1:5000/health || echo 'down'", returnStdout: true).trim()
                        if (flaskRunning != "down") {
                            break
                        }
                        sleep 3
                    }

                    if (flaskRunning == "down") {
                        error "❌ ERROR: Flask server failed to start!"
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

                    } else {
                        echo "📝 Generating test cases from text input..."
                        jsonResponse = sh(script: """
                            curl -s -X POST http://127.0.0.1:5000/generate \
                            -H "Content-Type: application/json" \
                            -d '{"topic": "${params.TEST_TOPIC}", "num_cases": ${params.NUM_CASES}, "filename": "${params.CSV_FILENAME}"}'
                        """, returnStdout: true).trim()
                    }

                    echo "🔹 Flask API Response: ${jsonResponse}"

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
                    echo "📥 Downloading generated CSV file..."
                    sh "curl -o ${env.GENERATED_CSV} http://127.0.0.1:5000/download/${env.GENERATED_CSV}"
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
