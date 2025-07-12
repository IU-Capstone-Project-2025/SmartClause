pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Test') {
            parallel {
                stage('Python Service') {
                    steps {
                        dir('analyzer') {
                            sh 'python -m venv venv'
                            sh './venv/bin/pip install -r requirements.txt'
                            sh './venv/bin/pytest tests/'
                        }
                    }
                }
                stage('Java Service') {
                    steps {
                        dir('backend') {
                            sh 'mvn clean package'
                            sh 'mvn test'
                        }
                    }
                }
                stage('Frontend') {
                    steps {
                        sleep(time: 10, unit: 'SECONDS')
                        retry(5) {
                            script {
                                try {
                                    def statusCode = sh(
                                        script: 'curl -s -o /dev/null -w "%{http_code}" http://158.160.190.57:8080',
                                        returnStdout: true
                                    ).trim()
                                    
                                    if (statusCode == "200") {
                                        echo "Frontend successfully started and responds with code: ${statusCode}"
                                    } else {
                                        error "Frontend responded with incorrect status code: ${statusCode}"
                                    }
                                } catch (Exception e) {
                                    error "Failed to connect to frontend: ${e.message}"
                                }
                            }
                            sleep(time: 5, unit: 'SECONDS')
                        }
                    }
                }
            }
        }
        stage('Deploy') {
            steps {
                sh 'docker compose down'
                sh 'docker compose up -d --build'
            }
        }
    }

    post {
        always {
            echo 'Pipeline finished'
        }
        success {
            echo 'All services have been successfully built and tested!'
        }
        failure {
            echo 'Error at one of the stages'
        }
    }
}
