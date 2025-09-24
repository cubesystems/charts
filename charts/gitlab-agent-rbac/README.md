# Overview
This is a complimentary chart for creating RBAC with namespace-scoped access prior to installing the actual GitLab agent for Kubernetes Helm chart.

## Minimal config example
```
agents:
  application-a-gitlab-agent:
    namespaces:
      - application-a
      - application-a-demo
  application-b-gitlab-agent:
    namespaces:
      - application-b
```


### Gitlab KAS agent creation example

```shell
TOKEN=foo
NAME=something-gitlab-agent
IMAGE_TAG=v18.4.0
ADDRESS=git.cubesystems.lv

helm upgrade --install gitlab-agent gitlab/gitlab-agent \
    --create-namespace \
    --namespace ${NAME} \
    --set serviceAccount.create=false \
    --set rbac.create=false \
    --set replicas=1 \
    --set image.tag=${IMAGE_TAG} \
    --set serviceAccount.name=${NAME} \
    --set config.token=${TOKEN} \
    --set config.kasAddress=wss://${ADDRESS}/-/kubernetes-agent/
```
