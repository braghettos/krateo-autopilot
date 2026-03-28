### TabList

TabList display a set of tab items for navigation or content grouping

#### Props

| Property | Required | Description | Type |
|-|-|-|---|
| allowedResources | yes | the list of resources that are allowed to be children of this widget or referenced by it | array |
| items | yes | the items of the tab list | array |
| items[].label | no | text displayed on the tab | string |
| items[].resourceRefId | yes | the identifier of the k8s custom resource represented by the tab content | string |

Example:
```yaml
kind: TabList
apiVersion: widgets.templates.krateo.io/v1beta1
metadata:
  name: my-tab-list
  namespace: test-namespace
spec:
  widgetData:
    allowedResources:
      - barcharts
      - buttons
      - filters
      - flowcharts
      - linecharts
      - markdowns
      - paragraphs
      - piecharts
      - yamlviewers
    items:
      - label: first tab
        resourceRefId: first-column
      - label: second tab
        resourceRefId: second-column
  resourcesRefs:
    items:
      - id: first-column
        apiVersion: widgets.templates.krateo.io/v1beta1
        name: first-column
        namespace: test-namespace
        resource: columns
        verb: GET
      - id: second-column
        apiVersion: widgets.templates.krateo.io/v1beta1
        name: second-column
        namespace: test-namespace
        resource: columns
        verb: GET
```