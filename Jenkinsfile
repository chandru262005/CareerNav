pipeline {
  agent any
  stages {
    stage('Build') {
      steps {
        sh 'docker-compose build'
      }
    }
    stage('Test') {
      steps {
        // Add your test commands here, e.g.:
        sh 'docker-compose run node-backend npm test'
        // For Python: sh 'docker-compose run python-backend pytest'
      }
    }
    stage('Deploy') {
      steps {
        sh 'docker-compose up -d'
      }
    }
  }
}
