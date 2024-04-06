{{- define "artisan-process" }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ kebabcase .name }}
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
      tier: {{ kebabcase .name }}
  template:
    metadata:
      name: {{ kebabcase .name }}
      labels:
        app: {{ .Release.Name }}
        tier: {{ kebabcase .name }}
        appVersion: {{ required "appVersion is required" $.Values.appVersion | quote }}
    spec:
{{- if.Values.dnsConfig }}
      dnsConfig: {{- toYaml .Values.dnsConfig | nindent 8 }}
{{- end }}
      initContainers:
        - name: init
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          command: ['./docker/scripts/prepare-laravel']
          env:
            - name: APP_VERSION
              value: {{ $.Values.appVersion | quote }}
          envFrom: {{- toYaml .Values.deploymentsSharedAttributes.initEnvFrom | nindent 12 }}
          volumeMounts: {{- toYaml .Values.deploymentsSharedAttributes.initVolumeMounts | nindent 12 }}
      containers:
        - name: {{ kebabcase .name }}
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          securityContext: {{- toYaml .Values.deploymentsSharedAttributes.securityContext | nindent 12 }}
          volumeMounts: {{- toYaml .Values.deploymentsSharedAttributes.volumeMounts | nindent 12 }}
          {{- toYaml .containerSpec | nindent 10 }}
      volumes: {{- toYaml .Values.deploymentsSharedAttributes.volumes | nindent 8 }}
      imagePullSecrets:
        - name: {{ .Values.image.registrySecretName }}
{{- end }}
