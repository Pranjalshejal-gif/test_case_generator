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
                    sleep 5 // Give Flask time to start

                    // Call API and capture JSON response
                    def response = sh(
                        script: """curl -s -X POST http://127.0.0.1:5000/generate \
                        -H 'Content-Type: application/json' \
                        -d '{\"topic\": \"${params.TEST_TOPIC}\", \"num_cases\": ${params.NUM_CASES}}'""",
                        returnStdout: true
                    ).trim()

                    echo "Flask API Response: ${response}"

                    // Check if API returned success message
                    if (!response.contains('"message": "Test cases generated successfully!"')) {
                        error "Flask API did not return success message!"
                    }

                    // Extract CSV filename safely
                    def csvFilename = sh(
                        script: "echo '${response}' | grep -oP '(?<=\\\"csv_filename\\\": \\\")([^\\\"]+)'",
                        returnStdout: true
                    ).trim()

                    if (!csvFilename) {
                        error "Failed to extract CSV filename from API response."
                    }

                    env.GENERATED_CSV = csvFilename
                    echo "Generated CSV file: ${csvFilename}"

                    // Ensure file exists before proceeding
                    def fileExistsCheck = sh(script: "test -f ${csvFilename} && echo 'exists'", returnStdout: true).trim()
                    if (fileExistsCheck != "exists") {
                        error "CSV file '${csvFilename}' not found!"
                    }

                    // Move CSV file to Jenkins workspace
                    sh "mv ${csvFilename} ${WORKSPACE}/"

                    echo "CSV file saved in Jenkins workspace: ${WORKSPACE}/${csvFilename}"
                }
            }
        }

        stage('Save Generated CSV File') {
            steps {
                archiveArtifacts artifacts: "${env.GENERATED_CSV}", allowEmptyArchive: false
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
