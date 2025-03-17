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
            def pdfFilePath = sh(script: "find /tmp -maxdepth 1 -type f -user jenkins -name '*.pdf' 2>/dev/null | head -n 1", returnStdout: true).trim()

            if (!pdfFilePath) {
                error "Uploaded PDF file not found in /tmp!"
            }

            echo "PDF file found at: ${pdfFilePath}"
            env.UPLOADED_PDF = pdfFilePath  // Store the path in an environment variable for later use
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
                    def jsonResponse = ""

                    if (env.UPLOADED_PDF) {
                        echo "Processing PDF file from /tmp: ${env.UPLOADED_PDF}"
                        jsonResponse = sh(script: """
                            curl -s -X POST http://127.0.0.1:5000/generate_pdf \
                            -F "pdf_file=@${env.UPLOADED_PDF}" \
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
                }
            }
        }

        stage('Download Test Cases CSV') {
            steps {
                script {
                    echo "Downloading generated CSV file..."
                    sh "curl -O http://127.0.0.1:5000/download/${params.CSV_FILENAME}_*.csv"
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
