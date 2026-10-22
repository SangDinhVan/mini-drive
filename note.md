kubectl logs deployment/backend-dev --tail=50

kubectl create secret generic backend-secret \
  --from-env-file=./backend/.env
kubectl port-forward svc/frontend-svc 8088:80

kubectl get storageclass

helm upgrade --install traefik traefik/traefik \
  --namespace traefik \
  --create-namespace \
  --wait \
  --timeout 5m


kubectl get pods -n traefik
kubectl get svc -n traefik
kubectl get ingressclass

kubectl port-forward -n traefik svc/traefik 8088:80

kubectl rollout restart deployment/backend-dev
kubectl rollout status deployment/backend-dev
kubectl exec deployment/backend-dev -- printenv model

kubectl get nodes
kubectl get deploy,svc,ingress,pvc

helm install mini-drive . \
  -n default \
  --wait \
  --timeout 5m

helim install: cài đặt chart lên k8s

helm upgrade mini-drive . \
  -n default \
  --wait \
  --timeout 5m

  helm uninstall mini-drive -n default

  helm list -n default	Xem các release
helm status mini-drive -n default	Xem trạng thái release
helm history mini-drive -n default	Xem lịch sử revision
helm get values mini-drive -n default	Xem các giá trị đã truyền khi cài/upgrade
helm get values mini-drive -n default -a	Xem toàn bộ values đang có hiệu lực
helm get manifest mini-drive -n default	Xem Kubernetes YAML mà Helm đã triển khai