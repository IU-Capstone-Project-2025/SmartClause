pipeline {
    agent any

    environment {
        OPENROUTER_API_KEY = credentials('OPENROUTER_API_KEY')
    }

    

    stages {
        stage('Notify Start') {
            steps {
                script {
                    githubNotify context: 'CI', status: 'PENDING', description: 'Jenkins pipeline started'
                }
            }
        }
        stage('Checkout') {
            steps {
                script {
                    githubNotify context: 'Checkout', status: 'PENDING'
                }
                checkout scm
            }
            post {
                success {
                    script {
                        githubNotify context: 'Checkout', status: 'SUCCESS'
                    }
                }
                failure {
                    script {
                        githubNotify context: 'Checkout', status: 'FAILURE'
                    }
                }
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
                        script {
                            githubNotify context: 'Python Service', status: 'PENDING'
                        }
                        
                        sh 'mkdir -p /cache/huggingface'
                        sh 'chmod -R 777 /cache'
                        
                        dir('analyzer') {
                            sh 'python -m venv venv'
                            sh './venv/bin/pip install -r requirements.txt'
                            sh './venv/bin/pytest tests/'
                        }
                    }
                    post {
                        success {
                            script {
                                githubNotify context: 'Python Service', status: 'SUCCESS'
                            }
                        }
                        failure {
                            script {
                                githubNotify context: 'Python Service', status: 'FAILURE'
                            }
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
                        script {
                            githubNotify context: 'Java Service', status: 'PENDING'
                        }

                        sh 'mkdir -p /root/.m2/repository'
                        sh 'chmod -R 777 /root/.m2/repository'
                        
                        dir('backend') {
                            sh 'mvn -Dmaven.repo.local=/root/.m2/repository clean package'
                            sh 'mvn -Dmaven.repo.local=/root/.m2/repository test'
                        }
                    }
                    post {
                        success {
                            script {
                                githubNotify context: 'Java Service', status: 'SUCCESS'
                            }
                        }
                        failure {
                            script {
                                githubNotify context: 'Java Service', status: 'FAILURE'
                            }
                        }
                    }
                }
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                script {
                    githubNotify context: 'Deploy', status: 'PENDING'
                }

                echo "Starting deployment stage on Jenkins side"
                sshagent(['deploy-key-id']) {
                    sh '''
                        ssh -o StrictHostKeyChecking=no deploy@158.160.190.57 '
                            echo "=== Starting deployment ===" &&
                            cd SmartClause &&
                            git pull &&
                            ./docker/build_frontend.sh &&
                            docker compose down &&
                            docker compose up -d --build &&
                            echo "=== Deploy completed successfully ==="
                        '
                    '''
                }
                echo "Deploy stage finished successfully on Jenkins side"
            }
            post {
                success {
                    script {
                        githubNotify context: 'Deploy', status: 'SUCCESS'
                    }
                }
                failure {
                    script {
                        githubNotify context: 'Deploy', status: 'FAILURE'
                    }
                }
            }
        }
    }

    post {
        success {
            script {
                githubNotify context: 'CI', status: 'SUCCESS', description: 'Jenkins build passed'
            }
            echo 'All services have been successfully built, tested, and deployed!'
        }
        failure {
            script {
                githubNotify context: 'CI', status: 'FAILURE', description: 'Jenkins build failed'
            }
            echo 'Error occurred in one of the CI/CD pipeline stages'
        }
        always {
            echo 'Jenkins pipeline execution completed.'
        }
    }
}
