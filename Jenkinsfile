pipeline {
    agent any

    environment {
        // Define any environment variables needed for your pipeline here
    }

    stages {
        stage('Declarative: Checkout SCM') {
            steps {
                checkout scm
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
                    echo 'Starting Flask server...'
                    sh 'nohup python3 app.py &'
                    sleep 10 // Wait for Flask app to start
                    echo 'Flask app started. Open the browser and interact with the UI.'
                }
            }
        }

        stage('Wait for CSV File') {
            steps {
                script {
                    timeout(time: 10, unit: 'MINUTES') {
                        waitUntil {
                            script {
                                return sh(script: 'ls test_cases_*.csv', returnStatus: true) == 0
                            }
                        }
                    }
                    echo 'CSV file found!'
                }
            }
        }

        stage('Upload to Jira Xray') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'jira-credentials', usernameVariable: 'JIRA_USER', passwordVariable: 'JIRA_PASSWORD')]) {
                    script {
                        // Securely use credentials in curl command
                        def csvFile = sh(script: 'ls test_cases_*.csv', returnStdout: true).trim().split()[0] // Get the latest CSV file
                        sh """
                            curl -u \$JIRA_USER:\$JIRA_PASSWORD -X POST -H 'Content-Type: multipart/form-data' -F file=@\$csvFile https://sarvatrajira.atlassian.net/rest/raven/1.0/import/test
                        """
                    }
                }
            }
        }
    }

    post {
        failure {
            echo 'Pipeline failed! Please check the logs for more details.'
        }
    }
}
