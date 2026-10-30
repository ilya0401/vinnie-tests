pipeline {
    agent any

    triggers {
        cron('0 3 * * *')
        pollSCM('H/5 * * * *')
    }

    parameters {
        choice(
            name: 'CATEGORY',
            choices: ['all', 'entries', 'jira_sync', 'jira_integration', 'process'],
            description: 'Категория тестов для запуска. all — запустить все тесты'
        )
        string(
            name: 'EMAIL',
            defaultValue: 'iyk040190@gmail.com',
            description: 'Email для отправки отчёта'
        )
    }

    environment {
        VINNY_URL = 'http://vinnie:8000'
        KAFKA_UI_URL = 'http://kafka-ui:8080'
        JIRA_TEST_TASK = 'KAN-1'
        TASK_PREFIX = 'KAN'
        JIRA_URL = 'https://iyk040190-1790711247004.atlassian.net'
        JIRA_EMAIL = 'iyk040190@gmail.com'
        JIRA_API_TOKEN = credentials('jira-api-token')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install dependencies') {
            steps {
                sh '''
                    python3 -m venv .venv
                    .venv/bin/pip install -r requirements.txt
                '''
            }
        }

        stage('Run tests') {
            steps {
                script {
                    // db-тесты рассчитаны на локальный Postgres (DB_HOST=localhost), а не на сеть
                    // Jenkins-контейнера, а chaos-тесты останавливают/пересоздают общие контейнеры
                    // или меняют .env окружения — ломают среду для всех. Оба исключены из 'all',
                    // а не просто пропущены маркером.
                    def marker = params.CATEGORY == 'all' ? 'not db and not chaos' : params.CATEGORY
                    sh ".venv/bin/python -m pytest -m \"${marker}\" --clean-alluredir --alluredir=allure-results"
                }
            }
        }
    }

    post {
        always {
            script {
                if (fileExists('allure-results')) {
                    allure includeProperties: false, jdk: '', results: [[path: 'allure-results']]
                }
            }
        }
        failure {
            withCredentials([string(credentialsId: 'resend-api-key', variable: 'RESEND_API_KEY')]) {
                withEnv([
                    "EMAIL_TO=${params.EMAIL}",
                    "EMAIL_SUBJECT=Тесты упали: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                    "EMAIL_BODY=Категория: ${params.CATEGORY}\nПодробности: ${env.BUILD_URL}allure"
                ]) {
                    sh '.venv/bin/python3 utils/send_email.py'
                }
            }
        }
        success {
            withCredentials([string(credentialsId: 'resend-api-key', variable: 'RESEND_API_KEY')]) {
                withEnv([
                    "EMAIL_TO=${params.EMAIL}",
                    "EMAIL_SUBJECT=Тесты прошли: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                    "EMAIL_BODY=Категория: ${params.CATEGORY}\nВсе тесты прошли успешно.\nОтчёт: ${env.BUILD_URL}allure"
                ]) {
                    sh '.venv/bin/python3 utils/send_email.py'
                }
            }
        }
    }
}