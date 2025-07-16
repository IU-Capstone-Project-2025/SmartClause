pipeline {
    agent any

    environment {
        OPENROUTER_API_KEY = credentials('OPENROUTER_API_KEY')
    }

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
                            args '-v ${WORKSPACE}/python-cache:/cache -e TRANSFORMERS_CACHE=/cache/huggingface -e HF_HOME=/cache/huggingface -e XDG_CACHE_HOME=/cache -u root'
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
                            args '-v ${WORKSPACE}/maven-repo:/root/.m2/repository -u root'
                        }
                    }
                    steps {
                        sh 'mkdir -p /root/.m2/repository'
                        sh 'chmod -R 777 /root/.m2/repository'
                        
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
                script {
                    def branchName = env.GIT_BRANCH ?: env.BRANCH_NAME ?: sh(
                        returnStdout: true,
                        script: 'git symbolic-ref --short HEAD || git name-rev --name-only HEAD'
                    ).trim()
                    
                    if (branchName == 'main' || branchName == 'origin/main') {
                        echo "Starting deployment stage on Jenkins side (branch: ${branchName})"
                        
                        sshagent(['deploy-key-id']) {
                            sh '''
                                ssh -o StrictHostKeyChecking=no deploy@158.160.190.57 '
                                    echo "=== Starting deployment ===" &&
                                    cd SmartClause &&
                                    git fetch origin &&
                                    git reset --hard origin/main &&
                                    chmod +x ./docker/build_frontend.sh
                                    ./docker/build_frontend.sh &&
                                    docker compose down &&
                                    docker compose up -d --build &&
                                    echo "=== Deploy completed successfully ==="
                                '
                            '''
                        }
                        
                        echo "Deploy stage finished successfully on Jenkins side"
                    } else {
                        echo "Skipping deployment: current branch is '${branchName}', not 'main'"
                    }
                }
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