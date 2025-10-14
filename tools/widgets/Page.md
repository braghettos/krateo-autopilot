### Page

Page is a wrapper component, placed at the top of the component tree, that wraps and renders all nested components.

#### Props

| Property | Required | Description | Type |
|-|-|-|---|
| allowedResources | yes | the list of resources that are allowed to be children of this widget or referenced by it | array |
| items | yes | list of resources to be rendered within the route | array |
| items[].resourceRefId | yes | the identifier of the k8s custom resource that should be rendered, usually a widget | string |
| title | no | title of the page shown in the browser tab | string |

Example:
```yaml
kind: Page
apiVersion: widgets.templates.krateo.io/v1beta1
metadata:
  name: compositions-route
  namespace: test-namespace
spec:
  widgetData:
    allowedResources:
      - barcharts
      - buttons
      - columns
      - datagrids
      - eventlists
      - filters
      - flowcharts
      - forms
      - linecharts
      - markdowns
      - panels
      - paragraphs
      - piecharts
      - rows
      - tables
      - tablists
      - yamlviewers
    items:
      - resourceRefId: composition-test-item
  resourcesRefs:
    items:
      - id: composition-test-item
        apiVersion: widgets.templates.krateo.io/v1beta1
        name: composition-test-item
        namespace: test-namespace
        resource: nav
        verb: GET
```
