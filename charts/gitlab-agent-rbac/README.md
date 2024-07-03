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
helm upgrade --install gitlab-agent gitlab/gitlab-agent \
    --create-namespace \
    --set serviceAccount.create=false \
    --set rbac.create=false \
    --set replicas=1 \
    --set image.tag=v17.1.1 \
    --namespace AGENT_NAME_HERE \
    --set serviceAccount.name=AGENT_NAME_HERE \
    --set config.token=TOKEN_HERE \
    --set config.kasAddress=wss://GITLAB_INSTANCE_HERE/-/kubernetes-agent
```
