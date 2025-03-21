pipeline {
    agent any

    environment {
        GIT_REPO = 'https://github.com/Pranjalshejal-gif/test_case_generator.git'
        PYTHON_BIN = '/usr/bin/python3' // Update this path if necessary
    }

    parameters {
        string(name: 'TEST_TOPIC', defaultValue: '', description: 'Enter the test topic')
        string(name: 'CSV_FILENAME', defaultValue: 'test_cases', description: 'Enter CSV filename')
        string(name: 'PDF_FILE_PATH', defaultValue: '', description: 'Path to PDF file')
        string(name: 'PLANTUML_IMAGE_PATH', defaultValue: '', description: 'Path to PlantUML image')
    }

    stages {
        stage('Clone Repository') {
            steps {
                git branch: 'main', url: "${GIT_REPO}"
            }
        }

        stage('Install Python Dependencies') {
            steps {
                sh '''
                    echo "Installing Python dependencies..."
                    pip3 install --user --no-cache-dir --force-reinstall pillow
                    pip3 install --no-cache-dir -r requirements.txt
                    echo "Dependencies installed"
                '''
            }
        }

        stage('Start Flask Server') {
            steps {
                script {
                    echo "🚀 Starting Flask application..."
                    sh '''
                        nohup python3 app.py > flask_output.log 2>&1 &
                    '''
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
                        error "ERROR: Flask server failed to start! Check flask_output.log"
                    }

                    echo "Flask application started successfully!"
                }
            }
        }

        stage('Generate Test Cases') {
            steps {
                script {
                    def jsonResponse = ""

                    if (params.TEST_TOPIC && params.PDF_FILE_PATH && params.PLANTUML_IMAGE_PATH) {
                        echo "Processing all inputs: Text, PDF, and Image..."
                        jsonResponse = sh(script: """
                            curl -s -X POST http://127.0.0.1:5000/generate_combined \
                            -H "Content-Type: application/json" \
                            -d '{"topic": "${params.TEST_TOPIC}", "pdf_path": "${params.PDF_FILE_PATH}", "image_path": "${params.PLANTUML_IMAGE_PATH}", "filename": "${params.CSV_FILENAME}"}'
                        """, returnStdout: true).trim()
                    } else if (params.PDF_FILE_PATH) {
                        echo "Processing PDF file: ${params.PDF_FILE_PATH}"
                        jsonResponse = sh(script: """
                            curl -s -X POST http://127.0.0.1:5000/generate_pdf \
                            -F "pdf_path=${params.PDF_FILE_PATH}"
                        """, returnStdout: true).trim()
                    } else if (params.PLANTUML_IMAGE_PATH) {
                        echo "Processing Image file: ${params.PLANTUML_IMAGE_PATH}"
                        jsonResponse = sh(script: """
                            curl -s -X POST http://127.0.0.1:5000/generate_image \
                            -F "image_path=${params.PLANTUML_IMAGE_PATH}"
                        """, returnStdout: true).trim()
                    } else if (params.TEST_TOPIC) {
                        echo "Processing topic: ${params.TEST_TOPIC}"
                        jsonResponse = sh(script: """
                            curl -s -X POST http://127.0.0.1:5000/generate \
                            -H "Content-Type: application/json" \
                            -d '{"topic": "${params.TEST_TOPIC}", "filename": "${params.CSV_FILENAME}"}'
                        """, returnStdout: true).trim()
                    } else {
                        error "No valid input provided for test case generation."
                    }

                    echo "Response: ${jsonResponse}"
                }
            }
        }

        stage('Download Test Cases CSV') {
            steps {
                script {
                    echo "Downloading generated test cases CSV..."
                    sh "curl -s -o ${params.CSV_FILENAME}.csv http://127.0.0.1:5000/download/${params.CSV_FILENAME}.csv"
                    archiveArtifacts artifacts: "${params.CSV_FILENAME}.csv", fingerprint: true
                }
            }
        }
    }
}
