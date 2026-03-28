### Paragraph

Paragraph is a simple component used to display a block of text

#### Props

| Property | Required | Description | Type |
|-|-|-|---|
| text | yes | the content of the paragraph to be displayed | string |

Example:
```yaml
kind: Paragraph
apiVersion: widgets.templates.krateo.io/v1beta1
metadata:
  name: my-paragraph
  namespace: test-namespace
spec:
  widgetData:
    text: "This is a paragraph"
```
