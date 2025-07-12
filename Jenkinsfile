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
                            args '-v ${WORKSPACE}/python-cache:/cache -e TRANSFORMERS_CACHE=/cache/huggingface -e HF_HOME=/cache/huggingface -e XDG_CACHE_HOME=/cache'
                        }
                    }
                    steps {
                        sh 'mkdir -p /cache/huggingface'
                        sh 'chmod -R 777 /cache'
                        
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
                            args '-v ${WORKSPACE}/maven-repo:/root/.m2/repository'
                        }
                    }
                    steps {
                        dir('backend') {
                            sh 'mvn -Dmaven.repo.local=/root/.m2/repository clean package'
                            sh 'mvn -Dmaven.repo.local=/root/.m2/repository test'
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
