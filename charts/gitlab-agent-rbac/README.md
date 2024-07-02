# Gitlab KAS agent creation example

```shell
helm upgrade --install gitlab-agent gitlab/gitlab-agent \
    --namespace MYPROJECT-gitlab-agent \
    --set serviceAccount.name=MYPROJECT-gitlab-agent \
    --create-namespace \
    --set serviceAccount.create=false \
    --set rbac.create=false \
    --set image.tag=v17.1.1 \
    --set config.token=TOKEN \
    --set config.kasAddress=wss://GITLAB/-/kubernetes-agent/ \
   --set replicas=1
```