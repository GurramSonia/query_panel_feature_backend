pipeline {
    agent any

    environment {
        VENV_DIR = "venv"  // You can change this if needed
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Set up Python Environment') {
            steps {
                sh '''
                    python -m venv ${VENV_DIR}
                    source ${VENV_DIR}/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install safety
                '''
            }
        }

        stage('Run Safety Scan') {
            steps {
                sh '''
                    source ${VENV_DIR}/bin/activate
                    safety check --file=requirements.txt --full-report --json > safety-report.json
                '''
            }
        }

        stage('Fail on Vulnerabilities') {
            steps {
                script {
                    def output = readJSON file: 'safety-report.json'
                    if (output.issues && output.issues.size() > 0) {
                        error "❌ Vulnerabilities found! See safety-report.json"
                    } else {
                        echo "✅ No known vulnerabilities found."
                    }
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'safety-report.json', onlyIfSuccessful: false
        }
    }
}
