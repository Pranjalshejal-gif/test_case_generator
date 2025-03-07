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
                script {
                    sh 'pip install --upgrade pip'
                    sh 'pip install -r requirements.txt'
                }
            }
        }

        stage('Start Flask Server') {
            steps {
                script {
                    echo "Starting Flask server..."
                    sh 'nohup python3 app.py > flask_output.log 2>&1 &'
                    sleep 10 // Wait for Flask to start
                    echo "Flask app started. Open the browser and interact with the UI."
                }
            }
        }

        stage('Wait for CSV File') {
            steps {
                script {
                    def csvFile
                    timeout(time: 10, unit: 'MINUTES') {
                        waitUntil {
                            csvFile = sh(
                                script: "ls *.csv 2>/dev/null || echo ''",
                                returnStdout: true
                            ).trim()
                            return csvFile != ''
                        }
                    }
                    echo "Found CSV file: ${csvFile}"
                    env.CSV_FILE = csvFile
                }
            }
        }

        stage('Upload to Jira Xray') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'testcase', passwordVariable: 'Shaikh@2609', usernameVariable: 'teheseen.shaikh@sarvatra.in')]) {
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
