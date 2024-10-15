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
    --set image.tag=v17.3.1 \
    --namespace elektrum-eup-gitlab-agent \
    --set serviceAccount.name=elektrum-eup-gitlab-agent \
    --set config.token=glagent-G6LNN-NZ8k2Vw_5s4-NKLcJYbrhTu9e4mEJGvUn5KvPxfV6y_Q \
    --set config.kasAddress=wss://gitlab.energo.lv/-/kubernetes-agent/
```
