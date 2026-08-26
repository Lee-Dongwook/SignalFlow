# Jenkins 혼합형 CI/CD 설정

GitHub Actions는 Jenkins 파이프라인을 시작만 하고, Protobuf 검증·Docker 빌드·GHCR 푸시·Flink 매니페스트 갱신은 Jenkins가 수행합니다.

로컬 Jenkins를 사용할 때는 GitHub Actions self-hosted runner를 같은 맥에 등록해야 합니다. 이 워크플로는 `self-hosted` runner에서 실행되므로 Jenkins의 `http://localhost:8080`에 접근할 수 있습니다.

## 1. Jenkins 준비

- 프로젝트 루트에서 다음 명령으로 Jenkins와 전용 Docker 빌드 환경을 실행합니다.

  ```bash
  docker compose -f infra/jenkins/docker-compose.yml up -d --build
  ```

- 초기 관리자 비밀번호는 다음 명령으로 확인하고, `http://localhost:8080`에서 **Install suggested plugins**를 선택해 관리자 계정을 만듭니다.

  ```bash
  docker compose -f infra/jenkins/docker-compose.yml exec jenkins \
    cat /var/jenkins_home/secrets/initialAdminPassword
  ```

- 이 구성은 Jenkins 컨트롤러에 Docker CLI와 Python 3를 포함하고, 별도 Docker-in-Docker 서비스가 이미지 빌드를 담당합니다. 학습·개발 환경에서는 `Jenkinsfile`의 `agent any`가 컨트롤러에서 실행됩니다.
- 저장소를 Pipeline from SCM 방식으로 연결하고, 경로를 `Jenkinsfile`로 지정합니다.
- GitHub 플러그인 또는 GitHub Checks 플러그인을 연결하면 Jenkins 실행 결과를 커밋 상태로 표시할 수 있습니다.

> `docker:dind` 서비스는 privileged 권한이 필요합니다. 현재 구성은 로컬 개발용이며, 운영 환경에서는 전용 Jenkins 에이전트 또는 Kubernetes 기반 에이전트를 사용하세요.

## 2. Jenkins Credentials

Jenkins에 다음 Credential을 등록합니다.

| ID | 유형 | 용도 |
| --- | --- | --- |
| `ghcr-token` | Username with password | GHCR에 이미지 푸시. 비밀번호에는 `write:packages` 권한이 있는 GitHub 토큰을 저장합니다. |
| `github-push-token` | Secret text | Flink 이미지 태그가 바뀐 매니페스트를 `main`에 푸시. `contents:write` 권한이 필요합니다. |

## 3. GitHub Actions Secrets

저장소 Settings → Secrets and variables → Actions에 다음 값을 등록합니다. 실제 토큰은 코드에 기록하지 않습니다.

| Secret | 값 |
| --- | --- |
| `JENKINS_URL` | Jenkins 기본 주소. 예: `https://jenkins.example.com` |
| `JENKINS_USER` | Jenkins API 호출 사용자명 |
| `JENKINS_API_TOKEN` | 해당 사용자의 Jenkins API 토큰 |
| `JENKINS_JOB_PATH` | Jenkins Job 경로. 예: `signalflow-ci`, 폴더 안의 Job은 `platform/signalflow-ci` |

## 4. 확인 방법

`main`에 커밋을 푸시하면 GitHub Actions의 **Trigger Jenkins CI/CD**가 커밋 SHA와 브랜치 정보를 Jenkins Job에 전달합니다. Jenkins에서 각 단계가 성공한 뒤 GHCR에 세 서비스 이미지를 올립니다. 마지막으로 Flink 매니페스트가 새 이미지 태그로 커밋됩니다. 이 자동 커밋에는 `[skip ci]`가 포함되어 다시 Jenkins를 호출하지 않습니다.
