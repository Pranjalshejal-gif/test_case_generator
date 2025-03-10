pipeline {
    agent any

    environment {
        JIRA_URL = 'https://sarvatrajira.atlassian.net/rest/api/2/issue/bulk'  // Bulk issue creation URL
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
                        script: "curl -X POST http://127.0.0.1:5000/generate -H 'Content-Type: application/json' -d '{\"topic\": \"CBDC APP\", \"num_cases\": 5}'",
                        returnStdout: true
                    ).trim()
                    echo "Flask API Response: ${response}"
                    
                    // Check if the response contains a CSV filename
                    def match = (response =~ /"csv_filename": "(.*?)"/)
                    if (match) {
                        env.CSV_FILE = match[0][1]
                        echo "CSV file generated: ${env.CSV_FILE}"
                    } else {
                        // If no CSV file is found, save response to a text file
                        echo "No CSV file found. Saving response as a text file..."
                        def responseFile = "${env.WORKSPACE}/flask_response.txt"
                        writeFile file: responseFile, text: response
                        env.CSV_FILE = responseFile
                    }

                    // Stop Flask server
                    // sh "pkill -f app.py"
                }
            }
        }

        stage('Upload to Jira (Bulk Issue Creation)') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'testcase', passwordVariable: 'JIRA_PASSWORD', usernameVariable: 'JIRA_USER')]) {
                        // Prepare the bulk create issues JSON payload
                        def jsonPayload = """
                        {
                          "issueUpdates": [
                            {
                              "fields": {
                                "project": { "key": "YOUR_PROJECT_KEY" },
                                "summary": "Test case summary from CSV",
                                "description": "Test case description from CSV",
                                "issuetype": { "name": "Task" }
                              }
                            }
                          ]
                        }
                        """
                        def response = sh(
                            script: """
                            curl -u ${JIRA_USER}:${JIRA_PASSWORD} -X POST -H "Content-Type: application/json" \
                            -d '${jsonPayload}' "${JIRA_URL}"
                            """,
                            returnStdout: true
                        ).trim()
                        echo "Response from Jira: ${response}"

                        // Log the response but do not fail the pipeline
                        if (response.contains("error")) {
                            echo "Failed to create issues in Jira: ${response}"
                        } else {
                            echo "Issues successfully created in Jira."
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
