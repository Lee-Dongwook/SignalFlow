FROM docker:27-cli AS docker-cli

FROM jenkins/jenkins:lts-jdk21

USER root

COPY --from=docker-cli /usr/local/bin/docker /usr/local/bin/docker

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

USER jenkins
