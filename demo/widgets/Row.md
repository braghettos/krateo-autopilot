### Row

#### Props

| Property | Required | Description | Type |
|-|-|-|---|
| allowedResources | yes | the list of resources that are allowed to be children of this widget or referenced by it | array |
| items | yes | the items of the row | array |
| items[].resourceRefId | yes |  | string |
| items[].size | no | the number of cells that the item will occupy, from 0 (not displayed) to 24 (occupies all space) | integer |

Example:
```yaml
kind: Row
apiVersion: widgets.templates.krateo.io/v1beta1
metadata:
  name: composition-test-row
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
      - resourceRefId: composition-test-panel
  resourcesRefs:
    items:
      - id: composition-test-panel
        apiVersion: widgets.templates.krateo.io/v1beta1
        name: composition-test-panel
        namespace: test-namespace
        resource: panels
        verb: GET
```