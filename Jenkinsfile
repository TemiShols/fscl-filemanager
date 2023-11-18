pipeline {
    agent any

    environment {
        KUBE_NAMESPACE = 'your-namespace'
        KUBE_DEPLOYMENT_NAME = 'FSCL'
        DJANGO_APP_NAME = 'FSCL Portal'
    }

    stages {
        stage('Checkout') {
            steps {
                // Checkout your source code from version control (e.g., Git)
                checkout scm
            }
        }

        stage('Unit Test') {
            steps {
                script {
                    // Install dependencies and run Python unit tests
                    sh 'pip install -r requirements.txt'
                    sh 'python -m unittest discover -s your_tests_directory'
                }
            }
        }

        stage('Build and Deploy') {
            steps {
                script {
                    // Build your Django app and deploy to Kubernetes
                    sh 'docker build -t your-docker-image .'
                    sh 'docker push your-docker-image'
                    sh "kubectl apply -f kubernetes/deployment.yaml -n ${KUBE_NAMESPACE}"
                }
            }
        }

        stage('Security Scan') {
            steps {
                script {
                    // Perform security scanning using Snyk.io
                    sh 'snyk test'
                }
            }
        }
    }

    post {
        failure {
            echo 'Pipeline failed!'
            // You can add additional actions to perform on failure
        }

        success {
            echo 'Pipeline succeeded!'
            // You can add additional actions to perform on success
        }
    }
}
