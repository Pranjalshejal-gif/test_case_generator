pipeline {
    agent any

    environment {
        JIRA_URL = 'https://sarvatrajira.atlassian.net/rest/api/2/issue/bulk'  // Jira Xray URL for bulk test case upload
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
                    
                    // Assuming the response contains test case summaries and descriptions
                    def testCasesJson = []
                    def testCaseData = response.split("\n")  // Split response into lines
                    
                    // Create JSON payload based on test case data
                    testCaseData.eachWithIndex { line, index ->
                        if (index > 0 && line.trim()) {  // Skip header and empty lines
                            def columns = line.split(",")
                            def summary = columns[0].trim()
                            def description = columns[1].trim()
                            
                            def testCase = [
                                "fields": [
                                    "project": [ "key": "IMP" ],  // Adjust project key if needed
                                    "summary": summary,
                                    "description": description,
                                    "issuetype": [ "name": "Test" ]
                                ]
                            ]
                            testCasesJson.add(testCase)
                        }
                    }

                    // Create the final JSON structure
                    def jsonPayload = [
                        "issueUpdates": testCasesJson
                    ]
                    
                    // Store the JSON payload in an environment variable
                    env.JSON_PAYLOAD = groovy.json.JsonOutput.toJson(jsonPayload)
                    echo "<strong>BULK TESTCASE:</strong>\n${env.JSON_PAYLOAD}"

                    // Save the JSON payload to a file for debugging
                    writeFile file: 'test_case_payload.json', text: env.JSON_PAYLOAD
                }
            }
        }

        stage('Upload to Jira Xray') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'testcase', passwordVariable: 'JIRA_PASSWORD', usernameVariable: 'JIRA_USER')]) {
                        def response = sh(
                            script: """
                            curl -u ${JIRA_USER}:${JIRA_PASSWORD} -X POST -H "Content-Type: application/json" \
                            -d '${env.JSON_PAYLOAD}' "${JIRA_URL}"
                            """,
                            returnStdout: true
                        ).trim()
                        echo "Response from Jira: ${response}"

                        // Check if the response indicates success or failure
                        if (response.contains("error")) {
                            echo "Failed to upload to Jira Xray: ${response}"
                        } else {
                            echo "Test cases successfully uploaded to Jira Xray."
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
