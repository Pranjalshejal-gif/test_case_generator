pipeline {
    agent any

    environment {
        JMETER_PATH = '/home/sarvatra.in/pranjal.shejal/apache-jmeter-5.6.3/apache-jmeter-5.6.3'
        JMX_FILE_PATH = '/home/sarvatra.in/pranjal.shejal/Documents/AI1.jmx'  // Path to the original JMX file
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
                    // Start Flask in the background
                    sh 'nohup python3 app.py > flask_output.log 2>&1 &'
                    sleep 5  // Allow Flask time to start
                    
                    // Request test cases from Flask API
                    def response = sh(
                        script: "curl -X POST http://127.0.0.1:5000/generate -H 'Content-Type: application/json' -d '{\"topic\": \"UPI APP\", \"num_cases\": 5}'",
                        returnStdout: true
                    ).trim()
                    echo "Flask API Response: ${response}"

                    try {
                        // Clean up the response to remove the markdown code block delimiters
                        def cleanedResponse = response.replaceAll(/```json\n|\n```/, '').trim()
                        
                        // Check if the cleaned response is valid JSON
                        if (cleanedResponse) {
                            echo "Cleaned Response: ${cleanedResponse}"
                            
                            // Parse the cleaned response as JSON
                            def jsonResponse = readJSON text: cleanedResponse
                            
                            // Check if the response is an array and extract the test case information
                            if (jsonResponse instanceof List) {
                                def testCaseDescriptions = jsonResponse.collect { testCase ->
                                    return """
                                    Test Case Name: ${testCase."Test Case Name"}
                                    Action: ${testCase.Action}
                                    Test Data: ${testCase."Test Data"}
                                    Expected Result: ${testCase."Expected Result"}
                                    """
                                }.join("\n\n")

                                // Save the test case descriptions for debugging
                                env.JSON_PAYLOAD = testCaseDescriptions
                                writeFile file: 'test_case_payload.json', text: env.JSON_PAYLOAD
                                echo "JSON Payload successfully extracted."
                            } else {
                                error "Error: Expected an array in the response but got ${jsonResponse.getClass().getName()}"
                            }
                        } else {
                            error "Error: The cleaned response is empty or invalid."
                        }
                    } catch (Exception e) {
                        error "Error parsing Flask API response: ${e.getMessage()}"
                    }
                }
            }
        }

        stage('Modify JMX File with JSON Payload') {
            steps {
                script {
                    // Ensure the JSON payload is not empty
                    if (env.JSON_PAYLOAD?.trim()) {
                        // Read the existing JMX file
                        def jmxContent = readFile(env.JMX_FILE_PATH)

                        // Replace request body with the extracted JSON payload
                        def modifiedJmxContent = jmxContent.replaceAll('(?s)<stringProp name="HTTPSampler.postBodyRaw">.*?</stringProp>', 
                            '<stringProp name="HTTPSampler.postBodyRaw">' + env.JSON_PAYLOAD.replaceAll('"', '&quot;') + '</stringProp>')
                        
                        // Get the current timestamp and create a unique JMX file name
                        def timestamp = new Date().format('yyyy-MM-dd_HH-mm-ss')
                        def timestampedJmxFile = "modified_test_case_plan_${timestamp}.jmx"

                        // Write the modified JMX file with the current timestamp in its name
                        writeFile file: "${workspace}/modified_test_case_plan_${timestamp}.jmx", text: modifiedJmxContent
                        echo "JMX file updated with JSON payload and saved as ${timestampedJmxFile}."
                    } else {
                        error "Error: JSON payload is empty. Cannot modify JMX file."
                    }
                }
            }
        }

        stage('Run JMeter Test') {
            steps {
                script {
                    // Get the current timestamp for the modified JMX file
                    def timestamp = new Date().format('yyyy-MM-dd_HH-mm-ss')
                    def timestampedJmxFile = "modified_test_case_plan_${timestamp}.jmx"

                    // Verify the modified JMX file exists
                    if (fileExists("${workspace}/${timestampedJmxFile}")) {
                        // Execute JMeter with the modified test plan using 'java -jar' command
                        echo "Executing JMeter test..."
                        sh "java -jar /home/sarvatra.in/pranjal.shejal/apache-jmeter-5.6.3/bin/ApacheJMeter.jar -n -t \"${workspace}/${timestampedJmxFile}\" -l results.jtl"
                        echo "JMeter test completed. Check results.jtl for details."
                        echo "Displaying JMeter logs..."
                        sh "tail -n 20 jmeter.log"
                    } else {
                        error "Modified JMX file not found!"
                    }
                }
            }
        }

        stage('Save Modified JMX File') {
            steps {
                script {
                    // Get the current timestamp for the modified JMX file
                    def timestamp = new Date().format('yyyy-MM-dd_HH-mm-ss')
                    def timestampedJmxFile = "modified_test_case_plan_${timestamp}.jmx"
                    
                    // Save the modified JMX file as an artifact to the Jenkins workspace
                    archiveArtifacts artifacts: "${workspace}/${timestampedJmxFile}", allowEmptyArchive: true
                    echo "Modified JMX file saved in workspace."
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
            // Optionally, you can display the JMeter log here for further debugging in case of failure
            sh "tail -n 50 jmeter.log"
        }
    }
}
