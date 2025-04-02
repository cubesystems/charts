# README

## New chart version release process
 1. Bump version in Chart.yaml  (ex `charts/laravel/Chart.yaml`)
 2. create chart package within `packages` directory  (ex. `cd packages && helm package ../charts/laravel/ && cd ..`)
 3. reindex charts with `helm repo index . --url https://cubesystems.github.io/charts/`
 4. commit and push all changes to GitHub
