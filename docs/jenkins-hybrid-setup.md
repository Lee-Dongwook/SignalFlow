# Jenkins 혼합형 CI/CD 설정

GitHub Actions는 Jenkins 파이프라인을 시작만 하고, Protobuf 검증·Docker 빌드·GHCR 푸시·Flink 매니페스트 갱신은 Jenkins가 수행합니다.

## 1. Jenkins 준비

- Docker와 Python 3가 설치되고 Docker 데몬에 접근할 수 있는 Jenkins 에이전트에 `docker` 라벨을 추가합니다.
- 저장소를 Pipeline from SCM 방식으로 연결하고, 경로를 `Jenkinsfile`로 지정합니다.
- GitHub 플러그인 또는 GitHub Checks 플러그인을 연결하면 Jenkins 실행 결과를 커밋 상태로 표시할 수 있습니다.

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

`main`에 커밋을 푸시하면 GitHub Actions의 **Trigger Jenkins CI/CD**가 Jenkins Job을 호출합니다. Jenkins에서 각 단계가 성공한 뒤 GHCR에 세 서비스 이미지가 올라가고, Flink 매니페스트가 새 이미지 태그로 커밋됩니다. 이 자동 커밋에는 `[skip ci]`가 포함되어 다시 Jenkins를 호출하지 않습니다.
