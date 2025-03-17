pipeline {
    agent any

    environment {
        GIT_REPO = 'https://github.com/Pranjalshejal-gif/test_case_generator.git'
    }

    parameters {
        string(name: 'TEST_TOPIC', defaultValue: '', description: 'Enter test topic (optional if using PDF)')
        string(name: 'NUM_CASES', defaultValue: '5', description: 'Enter number of test cases')
        file(name: 'PDF_FILE', description: 'Upload PDF file for test case generation (optional)')
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
                }
            }
        }

        stage('Generate Test Cases') {
            steps {
                script {
                    def jsonResponse = fileExists("${PDF_FILE}") ? 
                        sh(script: """curl -s -X POST -F "pdf_file=@${PDF_FILE}" -F "prompt=${params.TEST_TOPIC}" -F "num_cases=${params.NUM_CASES}" http://127.0.0.1:5000/generate_test_cases""", returnStdout: true).trim() :
                        sh(script: """curl -s -X POST -H "Content-Type: application/json" -d '{"prompt": "${params.TEST_TOPIC}", "num_cases": ${params.NUM_CASES}}' http://127.0.0.1:5000/generate_test_cases""", returnStdout: true).trim()

                    echo "Flask API Response: ${jsonResponse}"
                }
            }
        }
    }

    post {
        success { echo 'Pipeline executed successfully!' }
        failure { echo 'Pipeline failed! Check logs for issues.' }
    }
}
