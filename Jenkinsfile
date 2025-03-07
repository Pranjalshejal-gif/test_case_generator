pipeline {
    agent any

    environment {
        JIRA_URL = 'https://sarvatrajira.atlassian.net/rest/raven/1.0/import/test'
    }

    stages {
        stage('Clone Repository') {
            steps {
                git branch: 'main', url: 'https://github.com/Pranjalshejal-gif/test_case_generator.git'
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
                    // Start Flask in the background and redirect output to a log file
                    sh 'nohup python3 app.py > flask_output.log 2>&1 &'
                    sleep 5 // Wait for Flask to start
                    
                    // Send request to Flask API to generate test cases
                    def response = sh(
                        script: "curl -X POST http://127.0.0.1:5000/generate -H 'Content-Type: application/json' -d '{\"topic\": \"Login Functionality\", \"num_cases\": 5}'",
                        returnStdout: true
                    ).trim()
                    echo "Flask API Response: ${response}"
                    
                    // Extract CSV filename from API response
                    def match = (response =~ /"csv_filename": "(.*?)"/)
                    if (match) {
                        env.CSV_FILE = match[0][1]
                        echo "Extracted CSV file: ${env.CSV_FILE}"
                    } else {
                        error "Failed to extract CSV filename from response."
                    }

                    // Stop Flask server
                    sh "pkill -f app.py"
                }
            }
        }

        stage('Upload to Jira Xray') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'testcase', passwordVariable: 'JIRA_PASSWORD', usernameVariable: 'JIRA_USER')]) {
                        def response = sh(
                            script: """
                            curl -u ${JIRA_USER}:${JIRA_PASSWORD} -X POST -H "Content-Type: multipart/form-data" \
                            -F "file=@${env.CSV_FILE}" "${JIRA_URL}"
                            """,
                            returnStdout: true
                        ).trim()
                        echo "Response from Jira: ${response}"

                        if (response.contains("error")) {
                            error "Failed to upload to Jira: ${response}"
                        }
                    }
                }
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed! Please check the logs for more details.'
        }
    }
}
