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
                    agent {
                        docker {
                            image 'python:3.11'
                            args '-v $HOME/.cache/pip:/root/.cache/pip' 
                        }
                    }
                    steps {
                        dir('analyzer') {
                            sh 'python -m venv venv'
                            sh './venv/bin/pip install -r requirements.txt'
                            sh './venv/bin/pytest tests/'
                        }
                    }
                }
                stage('Java Service') {
                    agent {
                        docker {
                            image 'maven:3.9.6-eclipse-temurin-21'
                        }
                    }
                    steps {
                        dir('backend') {
                            sh 'mvn clean package'
                            sh 'mvn test'
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
