{{/*
  GenAI environment for every agent deployment.

  Vertex AI (vertexAI.enabled=true): drive the google-genai SDK in Vertex mode via
  Application Default Credentials — the kagent agent pod inherits the GKE node SA
  token from the metadata server (node pool must run as a SA with aiplatform access).
  No API key, no SA-key file.

  Gemini API key (vertexAI.enabled=false): leave Vertex off; the ModelConfig carries
  the apiKeySecret instead.
*/}}
{{- define "krateo-autopilot.genaiEnv" -}}
{{- if .Values.vertexAI.enabled }}
- name: GOOGLE_GENAI_USE_VERTEXAI
  value: "1"
- name: GOOGLE_CLOUD_PROJECT
  value: {{ .Values.vertexAI.projectID | quote }}
- name: GOOGLE_CLOUD_LOCATION
  value: {{ .Values.vertexAI.location | quote }}
{{- else }}
- name: GOOGLE_GENAI_USE_VERTEXAI
  value: "0"
{{- end }}
{{- end -}}
