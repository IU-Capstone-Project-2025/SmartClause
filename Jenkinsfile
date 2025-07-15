pipeline {
    agent any

    environment {
        OPENROUTER_API_KEY = credentials('OPENROUTER_API_KEY')
    }

    stages {
        stage('Notify Start') {
            steps {
                script {
                    def sha = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                    githubNotify(
                        context: 'CI',
                        status: 'PENDING',
                        description: 'Jenkins pipeline started',
                        repo: 'SmartClause',
                        account: 'IU-Capstone-Project-2025',
                        credentialsId: 'github_api_token',
                        sha: sha
                    )
                }
            }
        }

        stage('Checkout') {
            steps {
                script {
                    githubNotify(
                        context: 'Checkout',
                        status: 'PENDING',
                        repo: 'SmartClause',
                        account: 'IU-Capstone-Project-2025',
                        credentialsId: 'github_api_token',
                        sha: env.GIT_COMMIT
                    )
                }
                checkout scm
            }
            post {
                success {
                    script {
                        githubNotify(
                            context: 'Checkout',
                            status: 'SUCCESS',
                            repo: 'SmartClause',
                            account: 'IU-Capstone-Project-2025',
                            credentialsId: 'github_api_token',
                            sha: env.GIT_COMMIT
                        )
                    }
                }
                failure {
                    script {
                        githubNotify(
                            context: 'Checkout',
                            status: 'FAILURE',
                            repo: 'SmartClause',
                            account: 'IU-Capstone-Project-2025',
                            credentialsId: 'github_api_token',
                            sha: env.GIT_COMMIT
                        )
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
                            githubNotify(
                                context: 'Python Service',
                                status: 'PENDING',
                                repo: 'SmartClause',
                                account: 'IU-Capstone-Project-2025',
                                credentialsId: 'github_api_token',
                                sha: env.GIT_COMMIT
                            )
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
                                githubNotify(
                                    context: 'Python Service',
                                    status: 'SUCCESS',
                                    repo: 'SmartClause',
                                    account: 'IU-Capstone-Project-2025',
                                    credentialsId: 'github_api_token',
                                    sha: env.GIT_COMMIT
                                )
                            }
                        }
                        failure {
                            script {
                                githubNotify(
                                    context: 'Python Service',
                                    status: 'FAILURE',
                                    repo: 'SmartClause',
                                    account: 'IU-Capstone-Project-2025',
                                    credentialsId: 'github_api_token',
                                    sha: env.GIT_COMMIT
                                )
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
                            githubNotify(
                                context: 'Java Service',
                                status: 'PENDING',
                                repo: 'SmartClause',
                                account: 'IU-Capstone-Project-2025',
                                credentialsId: 'github_api_token',
                                sha: env.GIT_COMMIT
                            )
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
                                githubNotify(
                                    context: 'Java Service',
                                    status: 'SUCCESS',
                                    repo: 'SmartClause',
                                    account: 'IU-Capstone-Project-2025',
                                    credentialsId: 'github_api_token',
                                    sha: env.GIT_COMMIT
                                )
                            }
                        }
                        failure {
                            script {
                                githubNotify(
                                    context: 'Java Service',
                                    status: 'FAILURE',
                                    repo: 'SmartClause',
                                    account: 'IU-Capstone-Project-2025',
                                    credentialsId: 'github_api_token',
                                    sha: env.GIT_COMMIT
                                )
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
                    githubNotify(
                        context: 'Deploy',
                        status: 'PENDING',
                        repo: 'SmartClause',
                        account: 'IU-Capstone-Project-2025',
                        credentialsId: 'github_api_token',
                        sha: env.GIT_COMMIT
                    )
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
                        githubNotify(
                            context: 'Deploy',
                            status: 'SUCCESS',
                            repo: 'SmartClause',
                            account: 'IU-Capstone-Project-2025',
                            credentialsId: 'github_api_token',
                            sha: env.GIT_COMMIT
                        )
                    }
                }
                failure {
                    script {
                        githubNotify(
                            context: 'Deploy',
                            status: 'FAILURE',
                            repo: 'SmartClause',
                            account: 'IU-Capstone-Project-2025',
                            credentialsId: 'github_api_token',
                            sha: env.GIT_COMMIT
                        )
                    }
                }
            }
        }
    }

    post {
        success {
            script {
                githubNotify(
                    context: 'CI',
                    status: 'SUCCESS',
                    description: 'Jenkins build passed',
                    repo: 'SmartClause',
                    account: 'IU-Capstone-Project-2025',
                    credentialsId: 'github_api_token',
                    sha: env.GIT_COMMIT
                )
            }
            echo 'All services have been successfully built, tested, and deployed!'
        }
        failure {
            script {
                githubNotify(
                    context: 'CI',
                    status: 'FAILURE',
                    description: 'Jenkins build failed',
                    repo: 'SmartClause',
                    account: 'IU-Capstone-Project-2025',
                    credentialsId: 'github_api_token',
                    sha: env.GIT_COMMIT
                )
            }
            echo 'Error occurred in one of the CI/CD pipeline stages'
        }
        always {
            echo 'Jenkins pipeline execution completed.'
        }
    }
}
