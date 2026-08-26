pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        timestamps()
        disableConcurrentBuilds()
    }

    parameters {
        string(name: 'GIT_SHA', defaultValue: '', description: 'Commit SHA supplied by GitHub Actions')
        string(name: 'GIT_REF', defaultValue: 'refs/heads/main', description: 'Git ref supplied by GitHub Actions')
    }

    environment {
        IMAGE_REPOSITORY = 'ghcr.io/lee-dongwook/signalflow'
    }

    stages {
        stage('Checkout requested commit') {
            steps {
                checkout scm
                script {
                    if (params.GIT_SHA?.trim()) {
                        sh "git checkout --detach ${params.GIT_SHA}"
                    }

                    env.IMAGE_TAG = sh(
                        script: 'git rev-parse --short=7 HEAD',
                        returnStdout: true
                    ).trim()
                    env.DASHBOARD_IMAGE = "${env.IMAGE_REPOSITORY}/dashboard:${env.IMAGE_TAG}"
                    env.BACKEND_IMAGE = "${env.IMAGE_REPOSITORY}/backend-api:${env.IMAGE_TAG}"
                    env.FLINK_IMAGE = "${env.IMAGE_REPOSITORY}/flink-jobs:${env.IMAGE_TAG}"
                }
            }
        }

        stage('Validate Protobuf schemas') {
            steps {
                sh '''
                    python3 -m pip install --user "grpcio-tools>=1.60.0,<1.63.0"
                    python3 -m grpc_tools.protoc -I. --python_out=. schemas/event_schema_v1.proto
                '''
            }
        }

        stage('Build service images') {
            steps {
                sh '''
                    docker build -t "$DASHBOARD_IMAGE" -f apps/dashboard/Dockerfile .
                    docker build -t "$BACKEND_IMAGE" -f apps/backend_api/Dockerfile .
                    docker build -t "$FLINK_IMAGE" -f apps/flink_jobs/Dockerfile apps/flink_jobs
                '''
            }
        }

        stage('Push service images') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'ghcr-token',
                    usernameVariable: 'GHCR_USER',
                    passwordVariable: 'GHCR_TOKEN'
                )]) {
                    sh '''
                        printf '%s' "$GHCR_TOKEN" | docker login ghcr.io --username "$GHCR_USER" --password-stdin
                        docker push "$DASHBOARD_IMAGE"
                        docker push "$BACKEND_IMAGE"
                        docker push "$FLINK_IMAGE"
                        docker logout ghcr.io
                    '''
                }
            }
        }

        stage('Update Flink manifest') {
            steps {
                withCredentials([string(credentialsId: 'github-push-token', variable: 'GITHUB_TOKEN')]) {
                    sh '''
                        sed -i "s|image: ghcr.io/.*:.*|image: ${FLINK_IMAGE}|g" k8s/manifests/flink-jobmanager.yml
                        git diff --quiet -- k8s/manifests/flink-jobmanager.yml && exit 0

                        git config user.name "jenkins[bot]"
                        git config user.email "jenkins[bot]@users.noreply.github.com"
                        git add k8s/manifests/flink-jobmanager.yml
                        git commit -m "chore(deploy): update flink image to ${IMAGE_TAG} [skip ci]"
                        git remote set-url origin "https://x-access-token:${GITHUB_TOKEN}@github.com/Lee-Dongwook/SignalFlow.git"
                        git push origin HEAD:main
                    '''
                }
            }
        }
    }
}
