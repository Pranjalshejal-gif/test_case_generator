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

        stage('Start Flask Server') {
            steps {
                script {
                    echo "Starting Flask application..."
                    sh 'nohup python3 app.py > flask_output.log 2>&1 &'
                    sleep 10  // Ensure Flask has time to fully start
                    echo "Flask application started!"
                }
            }
        }

        stage('Generate Test Cases') {
            steps {
                script {
                   echo "Calling Flask API to generate test cases..."
            
            // Make API request and get JSON response as a string
                    def jsonResponse = sh(script: """
                curl -s -X POST http://127.0.0.1:5000/generate \
                -H "Content-Type: application/json" \
                -d '{"topic": "${params.TEST_TOPIC}", "num_cases": ${params.NUM_CASES}}'
            """, returnStdout: true).trim()

                   echo "Flask API Response: ${jsonResponse}"

            // Parse API response
            def parsedResponse = readJSON text: jsonResponse

            // Extract CSV file path
            def csvFilepath = parsedResponse.csv_filepath ?: ''

            if (!csvFilepath || csvFilepath == "null") {
                error "Failed to extract CSV filepath from API response."
            }

            echo "CSV file generated: ${csvFilepath}"

            // Check if the file exists
            def fileExists = sh(script: "test -f ${csvFilepath} && echo 'exists'", returnStdout: true).trim()
            if (fileExists != "exists") {
                error "CSV file '${csvFilepath}' not found!"
            }

            echo "CSV file is successfully stored in Jenkins workspace!"
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
        }
    }
}
