pipeline {
    agent any

    parameters {
        string(name: 'TEST_TOPIC', defaultValue: 'Default Topic', description: 'Enter the test topic')
        string(name: 'NUM_CASES', defaultValue: '5', description: 'Enter the number of test cases')
        string(name: 'CSV_FILENAME', defaultValue: 'test_cases', description: 'Enter the CSV filename')
        file(name: 'PDF_FILE', description: 'Upload a PDF file for test case generation')
    }

    environment {
        WORKSPACE_PATH = "${WORKSPACE}/uploaded_pdfs"  // Define a folder for uploaded PDFs
    }

    stages {
        
        stage('Prepare Workspace') {
            steps {
                script {
                    sh "mkdir -p ${WORKSPACE_PATH}"  // Create a directory for PDFs
                }
            }
        }

        stage('Check for Uploaded PDF') {
            steps {
                script {
                    if (params.PDF_FILE) {
                        echo "PDF file detected: ${params.PDF_FILE}"
                        sh "mv ${params.PDF_FILE} ${WORKSPACE_PATH}/uploaded.pdf"
                    } else {
                        echo "No PDF file uploaded, skipping PDF-related test generation."
                        error("PDF file is required!")
                    }
                }
            }
        }

        stage('Extract Test Cases') {
            steps {
                script {
                    try {
                        def jsonResponse = sh(script: """
                            curl -s -X POST http://127.0.0.1:5000/generate_pdf \
                            -F pdf_file=@${WORKSPACE_PATH}/uploaded.pdf \
                            -F prompt='${params.TEST_TOPIC}' \
                            -F num_cases=${params.NUM_CASES} \
                            -F filename='${params.CSV_FILENAME}.csv'
                        """, returnStdout: true).trim()

                        echo "Response: ${jsonResponse}"

                        // Parse the JSON response safely
                        def parsedJson = readJSON text: jsonResponse
                        echo "Parsed JSON Response: ${parsedJson}"
                        
                    } catch (Exception e) {
                        echo "Error in API call: ${e.getMessage()}"
                        error("Failed to get test case response")
                    }
                }
            }
        }

        stage('Save Test Cases to CSV') {
            steps {
                script {
                    echo "Test cases have been generated and saved as ${params.CSV_FILENAME}.csv"
                }
            }
        }
    }

    post {
        success {
            echo "Pipeline completed successfully!"
        }
        failure {
            echo "Pipeline failed! Check logs for issues."
        }
    }
}
