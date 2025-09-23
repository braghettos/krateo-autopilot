### Column

Column is a layout component that arranges its children in a vertical stack, aligning them one above the other with spacing between them

#### Props

| Property | Required | Description | Type |
|-|-|-|-|
| allowedResources | yes | the list of resources that are allowed to be children of this widget or referenced by it | array |
| items | yes | the items of the column | array |
| items[].resourceRefId | yes | the identifier of the k8s Custom Resource that should be represented, usually a widget | string |
| size | no | the number of cells that the column will occupy, from 0 (not displayed) to 24 (occupies all space) | integer |

Example:
```yaml
kind: Column
apiVersion: widgets.templates.krateo.io/v1beta1
metadata:
  name: test-column
  namespace: test-namespace
spec:
  widgetData:
    allowedResources:
      - barcharts
      - buttons
      - columns
      - datagrids
      - eventlists
    items:
      - resourceRefId: table-of-pods
      - resourceRefId: pie-chart-inside-column
  resourcesRefs:
    items:
      - id: table-of-pods
        apiVersion: widgets.templates.krateo.io/v1beta1
        name: table-of-pods
        namespace: test-namespace
        resource: tables
        verb: GET
      - id: pie-chart-inside-column
        apiVersion: widgets.templates.krateo.io/v1beta1
        name: pie-chart-inside-column
        namespace: test-namespace
        resource: piecharts
        verb: GET
```