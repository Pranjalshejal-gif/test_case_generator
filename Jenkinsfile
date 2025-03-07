pipeline {
    agent any

    environment {
        JIRA_URL = 'https://sarvatrajira.atlassian.net/rest/raven/1.0/import/test'
    }

    stages {
        stage('Clone Repository') {
            steps {
                // Clone the repository that contains the Flask app and Jenkinsfile
                git branch: 'main', url: 'https://github.com/Pranjalshejal-gif/test_case_generator.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                // Install dependencies specified in requirements.txt
                sh 'pip install -r requirements.txt'
            }
        }

        stage('Generate Test Cases') {
            steps {
                script {
                    // Run the Flask app to generate test cases (CSV and JSON)
                    sh 'python3 app.py'

                    // Get the current date and time to dynamically generate the CSV file name
                    def currentTime = new Date().format("yyyy-MM-dd_HH-mm-ss")
                    env.CSV_FILE = "test_cases_${currentTime}.csv"
                    echo "Generated CSV file name: ${env.CSV_FILE}"

                    // Ensure the file is created before proceeding
                    if (!fileExists("${env.CSV_FILE}")) {
                        error "CSV file was not created."
                    }
                }
            }
        }

        stage('Upload to Jira Xray') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'testcase', passwordVariable: 'JIRA_PASSWORD', usernameVariable: 'JIRA_USER')]) {
                        // Upload the generated CSV test cases to Jira Xray
                        def response = sh(
                            script: """
                            curl -u ${JIRA_USER}:${JIRA_PASSWORD} -X POST -H "Content-Type: multipart/form-data" \
                            -F "file=@${env.CSV_FILE}" "${JIRA_URL}"
                            """,
                            returnStdout: true
                        ).trim()
                        echo "Response from Jira: ${response}"

                        // Handle response (if needed)
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
