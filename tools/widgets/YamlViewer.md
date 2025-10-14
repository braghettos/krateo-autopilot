### YamlViewer

YamlViewer receives a JSON string as input and renders its equivalent YAML representation for display.

#### Props

| Property | Required | Description | Type |
|-|-|-|---|
| json | yes | json string to be converted and displayed as yaml | string |

Example:
```yaml
kind: YamlViewer
apiVersion: widgets.templates.krateo.io/v1beta1
metadata:
  name: my-yaml-viewer
  namespace: test-namespace
spec:
  widgetData:
    json: '{"type":"object","additionalProperties":false,"properties":{"kind":{"type":"string","default":"YamlViewer"}}}'
```