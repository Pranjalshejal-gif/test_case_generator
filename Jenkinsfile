pipeline {
    agent any

    environment {
        JIRA_URL = 'https://sarvatrajira.atlassian.net/rest/raven/1.0/import/test'
        JIRA_PROJECT_KEY = 'IMP'
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

        
        stage('Parse JSON and Upload to Jira') {
            steps {
                script {
                    // Get the current date and time in the format required for the filename
                    def currentDateTime = new Date().format('yyyy-MM-dd_HH-mm-ss')
                    def jsonFileName = "test_cases_${currentDateTime}.json"

                    // Construct the path to the file in the Jenkins workspace
                    def filePath = "${env.WORKSPACE}/${jsonFileName}"
                    
                    // Check if the file exists
                    if (fileExists(filePath)) {
                        // Read the JSON file
                        def testCases = readJSON file: filePath

                        // Loop through each test case and create Jira issue
                        testCases.each { testCase ->
                            def testCaseNo = testCase.'Test Case No'
                            def testStep = testCase.'Test Step'
                            def testType = testCase.'Test Type'
                            def testSummary = testCase.'Test Summary'
                            def testData = testCase.'Test Data'
                            def expectedResult = testCase.'Expected Result'

                            // Generate the Jira issue using the provided data
                            withCredentials([usernamePassword(credentialsId: 'testcase', usernameVariable: 'JIRA_USER', passwordVariable: 'JIRA_PASSWORD')]) {
                                def jsonBody = """
                                {
                                    "fields": {
                                        "project": {
                                            "key": "$JIRA_PROJECT_KEY"
                                        },
                                        "summary": "$testSummary",
                                        "description": "Test Case No: $testCaseNo\nTest Step: $testStep\nTest Type: $testType\nTest Data: $testData\nExpected Result: $expectedResult",
                                        "issuetype": {
                                            "name": "Task"
                                        }
                                    }
                                }
                                """

                                // Call Jira REST API to create the issue
                                sh """
                                    curl -u $JIRA_USER:$JIRA_PASSWORD -X POST -H "Content-Type: application/json" \
                                    -d '$jsonBody' \
                                    $JIRA_URL/rest/api/2/issue/
                                """
                            }
                        }
                    } else {
                        error "The file $jsonFileName does not exist in the workspace."
                    }
                }
            }
        }
    }
}

