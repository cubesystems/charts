{{/*
Generate modified envFrom from a passed list with resourcePrefix
*/}}
{{- define "chart.modifiedEnvFrom" -}}
{{- $resourcePrefix := .resourcePrefix -}}
envFrom:
{{- range .envFrom }}
  {{- if .configMapRef }}
  - configMapRef:
      name: "{{ $resourcePrefix }}{{ .configMapRef.name }}"
  {{- end }}
  {{- if .secretRef }}
  - secretRef:
      name: "{{ $resourcePrefix }}{{ .secretRef.name }}"
  {{- end }}
{{- end }}
{{- end }}

{{/*
Generate modified volumes from a passed list with resourcePrefix
*/}}
{{- define "chart.modifiedVolumes" -}}
{{- $resourcePrefix := .resourcePrefix -}}
{{- range .volumes }}
  - name: {{ .name }}
    {{- if .configMap }}
    configMap:
      name: "{{ $resourcePrefix }}{{ .configMap.name }}"
    {{- end }}
    {{- if .secret }}
    secret:
      secretName: "{{ $resourcePrefix }}{{ .secret.secretName }}"
    {{- end }}
{{- end }}
{{- end }}
