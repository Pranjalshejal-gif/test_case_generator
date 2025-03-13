pipeline {
    agent any

    environment {
        GIT_REPO = 'https://github.com/Pranjalshejal-gif/test_case_generator.git'
    }

    parameters {
        string(name: 'TEST_TOPIC', defaultValue: 'CBDC APP', description: 'Enter the test topic')
        string(name: 'NUM_CASES', defaultValue: '5', description: 'Enter the number of test cases')
    }

    stages {
        stage('Clone Repository') {
            steps {
                git branch: 'main', url: "${GIT_REPO}"
            }
        }

        stage('Install Dependencies') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }

        stage('Start Flask Server') {
            steps {
                script {
                    echo "Starting Flask application..."
                    sh 'nohup python3 app.py > flask_output.log 2>&1 &'
                    sleep 5  // Ensure Flask has time to start
                    echo "Flask application started!"
                }
            }
        }

        stage('Generate Test Cases') {
            steps {
                script {
                    echo "Calling Flask API to generate test cases..."
                    
                    // Make API request and get JSON response as a string
                    def jsonResponse = sh(script: """
                        curl -s -X POST http://127.0.0.1:5000/generate \
                        -H "Content-Type: application/json" \
                        -d '{"topic": "${params.TEST_TOPIC}", "num_cases": ${params.NUM_CASES}}'
                    """, returnStdout: true).trim()

                    echo "Flask API Response: ${jsonResponse}"

                    // Use readJSON to parse response safely
                    def parsedResponse = readJSON text: jsonResponse

                    // Extract CSV filename
                    def csvFilename = parsedResponse.csv_filename ?: 'default.csv'

                    if (!csvFilename || csvFilename == "null") {
                        error "Failed to extract CSV filename from API response."
                    }

                    echo "Extracted CSV Filename: ${csvFilename}"

                    // Check if file exists
                    def fileExists = sh(script: "test -f ${csvFilename} && echo 'exists'", returnStdout: true).trim()
                    if (fileExists != "exists") {
                        error "CSV file '${csvFilename}' not found!"
                    }

                    // Move CSV file to Jenkins workspace
                    sh "mv ${csvFilename} ${WORKSPACE}/"
                    echo "CSV file saved in Jenkins workspace: ${WORKSPACE}/${csvFilename}"

                    // Set environment variable for later stages
                    env.GENERATED_CSV = "${WORKSPACE}/${csvFilename}"
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
