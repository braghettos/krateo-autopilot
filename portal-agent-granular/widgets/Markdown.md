### Markdown

Markdown receives markdown in string format and renders it gracefully

#### Props

| Property | Required | Description | Type |
|-|-|-|---|
| markdown | yes | markdown string to be displayed | string |

Example:
```yaml
kind: Markdown
apiVersion: widgets.templates.krateo.io/v1beta1
metadata:
  name: test-markdown
  namespace: test-namespace
spec:
  widgetData:
    markdown: "# Titolo H1\n## Sottotitolo\nTesto **in grassetto**, _in corsivo_ e `codice inline`.\n\n- Lista 1\n- Lista 2\n\n1. Primo\n2. Secondo\n\n> Questo è un blockquote.\n\n[Link a Google](https://google.com)\n\n```js\nconsole.log('Ciao mondo');\n```"
```

