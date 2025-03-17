pipeline {
    agent any

    environment {
        GIT_REPO = 'https://github.com/Pranjalshejal-gif/test_case_generator.git'
    }

    parameters {
        string(name: 'TEST_TOPIC', defaultValue: '', description: 'Enter the test topic (optional if using PDF)')
        string(name: 'NUM_CASES', defaultValue: '5', description: 'Enter the number of test cases')
        string(name: 'CSV_FILENAME', defaultValue: 'test_cases', description: 'Enter the CSV filename')
        file(name: 'PDF_FILE', description: 'Upload a PDF file for test case generation (optional)') 
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

        stage('Identify Where Jenkins Stores the Uploaded File') {
            steps {
                script {
                    def tempFilePath = sh(script: "find /tmp -name '${PDF_FILE}' 2>/dev/null | head -n 1", returnStdout: true).trim()
                    if (!tempFilePath) {
                        error "Uploaded file not found in Jenkins temporary directory."
                    }
                    echo "Uploaded PDF file found at: ${tempFilePath}"
                    env.UPLOADED_PDF_PATH = tempFilePath
                }
            }
        }

        stage('Copy File from Temporary Location to Workspace') {
            steps {
                script {
                    def workspaceFilePath = "${WORKSPACE}/uploaded_file.pdf"
                    sh "cp '${env.UPLOADED_PDF_PATH}' '${workspaceFilePath}'"
                    echo "PDF file copied to workspace: ${workspaceFilePath}"
                }
            }
        }

        stage('Verify the File in Jenkins Workspace') {
            steps {
                script {
                    def workspaceFilePath = "${WORKSPACE}/uploaded_file.pdf"
                    def fileExists = sh(script: "test -f '${workspaceFilePath}' && echo 'exists'", returnStdout: true).trim()
                    if (fileExists != "exists") {
                        error "PDF file not found in workspace!"
                    }
                    echo "PDF file verified in workspace: ${workspaceFilePath}"
                }
            }
        }

        stage('Start Flask Server') {
            steps {
                script {
                    echo "Starting Flask application..."
                    sh 'nohup python3 app.py > flask_output.log 2>&1 &'
                    sleep 5  

                    def flaskRunning = sh(script: "curl -s http://127.0.0.1:5000/health || echo 'down'", returnStdout: true).trim()
                    if (flaskRunning == "down") {
                        error "Flask server failed to start!"
                    }

                    echo "Flask application started successfully!"
                }
            }
        }

        stage('Process Uploaded PDF or Generate from Text') {
            steps {
                script {
                    def pdfFilePath = "${WORKSPACE}/uploaded_file.pdf"
                    def jsonResponse = ""

                    if (fileExists(pdfFilePath)) {
                        echo "PDF file detected: ${pdfFilePath}"
                        echo "Extracting test cases from PDF..."

                        jsonResponse = sh(script: """
                            curl -s -X POST http://127.0.0.1:5000/generate_pdf \
                            -F "pdf_file=@${pdfFilePath}" \
                            -F "prompt=${params.TEST_TOPIC}" \
                            -F "num_cases=${params.NUM_CASES}" \
                            -F "filename=${params.CSV_FILENAME}"
                        """, returnStdout: true).trim()

                    } else {
                        echo "No PDF uploaded, generating test cases from text..."
                        
                        jsonResponse = sh(script: """
                            curl -s -X POST http://127.0.0.1:5000/generate \
                            -H "Content-Type: application/json" \
                            -d '{"topic": "${params.TEST_TOPIC}", "num_cases": ${params.NUM_CASES}, "filename": "${params.CSV_FILENAME}"}'
                        """, returnStdout: true).trim()
                    }

                    echo "Flask API Response: ${jsonResponse}"

                    def parsedResponse = readJSON text: jsonResponse
                    def csvFilepath = parsedResponse.csv_filepath ?: ''

                    if (!csvFilepath || csvFilepath == "null") {
                        error "Failed to extract CSV filepath from API response."
                    }

                    echo "CSV file generated: ${csvFilepath}"

                    def fileExists = sh(script: "test -f ${csvFilepath} && echo 'exists'", returnStdout: true).trim()
                    if (fileExists != "exists") {
                        error "CSV file '${csvFilepath}' not found!"
                    }

                    echo "CSV file is successfully stored in Jenkins workspace!"
                }
            }
        }

        stage('Download Test Cases CSV') {
            steps {
                script {
                    if (fileExists("${WORKSPACE}/uploaded_file.pdf")) {
                        echo "Downloading generated CSV file..."
                        sh "curl -O http://127.0.0.1:5000/download/${params.CSV_FILENAME}_*.csv"
                    } else {
                        echo "Skipping CSV download (no PDF uploaded)."
                    }
                }
            }
        }
    }

    post {
        success {
            echo 'Pipeline executed successfully!'
        }
        failure {
            echo 'Pipeline failed! Check logs for issues.'
        }
    }
}
