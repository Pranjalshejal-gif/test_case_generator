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

        stage('Start Flask and Generate Test Cases') {
            steps {
                script {
                    // Start Flask in the background
                    sh 'nohup python3 app.py > flask_output.log 2>&1 &'
                    sleep 5  // Allow Flask time to start

                    // Use input parameters for dynamic request
                    def response = sh(
                        script: """
                        curl -X POST http://127.0.0.1:5000/generate \
                        -H 'Content-Type: application/json' \
                        -d '{\"topic\": \"${params.TEST_TOPIC}\", \"num_cases\": ${params.NUM_CASES}}'
                        """,
                        returnStdout: true
                    ).trim()
                    echo "Flask API Response: ${response}"

                    // Extract CSV filename from response
                    def csvFilename = response.replaceAll('.*"(test_cases_\\d{4}-\\d{2}-\\d{2}_\\d{2}-\\d{2}-\\d{2}\\.csv)".*', '$1')
                    env.GENERATED_CSV = csvFilename

                    if (!fileExists(csvFilename)) {
                        error "CSV file not found: ${csvFilename}"
                    }
                    echo "Generated CSV file: ${csvFilename}"
                }
            }
        }

        stage('Save Generated CSV File') {
            steps {
                script {
                    archiveArtifacts artifacts: "${env.GENERATED_CSV}", allowEmptyArchive: true
                    echo "Saved CSV file in Jenkins workspace."
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
