pipeline {
    agent any

    triggers {
        cron('0 3 * * *')
    }

    parameters {
        choice(
            name: 'CATEGORY',
            choices: ['all', 'entries', 'jira_sync', 'jira_integration'],
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
        JIRA_TEST_TASK = 'KAN-9'
        TASK_PREFIX = 'KAN'
        JIRA_URL = 'https://iyk040190.atlassian.net'
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
                    def marker = params.CATEGORY == 'all' ? '' : "-m ${params.CATEGORY}"
                    sh ".venv/bin/python -m pytest ${marker} --alluredir=allure-results"
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
            emailext(
                to: "${params.EMAIL}",
                subject: "Тесты упали: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: "Категория: ${params.CATEGORY}\nПодробности: ${env.BUILD_URL}allure"
            )
        }
        success {
            emailext(
                to: "${params.EMAIL}",
                subject: "Тесты прошли: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: "Категория: ${params.CATEGORY}\nВсе тесты прошли успешно.\nОтчёт: ${env.BUILD_URL}allure"
            )
        }
    }
}