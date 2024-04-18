{{- define "artisan-process" }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Values.resourcePrefix }}{{ kebabcase .name }}
spec:
  replicas: 1
  minReadySeconds: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: {{ .Release.Name }}
      tier: {{ .Values.resourcePrefix }}{{ kebabcase .name }}
  template:
    metadata:
      name: {{ kebabcase .name }}
      labels:
        app: {{ .Release.Name }}
        tier: {{ .Values.resourcePrefix }}{{ kebabcase .name }}
        appVersion: {{ required "appVersion is required" $.Values.appVersion | quote }}
    spec:
{{- if.Values.dnsConfig }}
      dnsConfig: {{- toYaml .Values.dnsConfig | nindent 8 }}
{{- end }}
      initContainers:
{{- if.Values.phpDeployment.initContainer.enabled }}
        - name: init
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          command: {{- toYaml $.Values.phpDeployment.initContainer.command | nindent 12 }}
          env:
            - name: APP_VERSION
              value: {{ $.Values.appVersion | quote }}
          {{- $args := dict "envFrom" .Values.phpDeployment.initContainer.envFrom "resourcePrefix" .Values.resourcePrefix }}
          {{- include "chart.modifiedEnvFrom" $args | nindent 10 }}
          volumeMounts: {{- toYaml .Values.phpDeployment.initContainer.volumeMounts | nindent 12 }}
{{- end }}
      containers:
        - name: {{ kebabcase .name }}
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          securityContext: {{- toYaml .Values.phpDeployment.container.securityContext | nindent 12 }}
          volumeMounts: {{- toYaml .Values.phpDeployment.container.volumeMounts | nindent 12 }}
          {{- toYaml .containerSpec | nindent 10 }}
      volumes: {{- toYaml .Values.phpDeployment.volumes | nindent 8 }}
      imagePullSecrets:
        - name: {{ .Values.resourcePrefix }}{{ .Values.image.registrySecretName }}
{{- end }}
