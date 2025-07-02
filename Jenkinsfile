pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Build & Test') {
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
                                        echo "Фронтенд успешно запущен и отвечает с кодом: ${statusCode}"
                                    } else {
                                        error "Фронтенд ответил с неверным статус-кодом: ${statusCode}"
                                    }
                                } catch (Exception e) {
                                    error "Не удалось подключиться к фронтенду: ${e.message}"
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
            echo 'Пайплайн завершён'
        }
        success {
            echo 'Все сервисы успешно собраны и протестированы!'
        }
        failure {
            echo 'Ошибка на одном из этапов'
        }
    }
}
