# DataGrid

Layout that allows you to arrange a list of elements within a page as a grid, where you can specify the number of elements per row.

## Props

| Property | Required | Description | Type |
|-|-|-|-|
| allowedResources | yes | the list of resources that are allowed to be children of this widget or referenced by it | array |
| asGrid | no | to show children as list or grid | boolean |
| grid | no | The grid type of list. You can set grid to something like {gutter: 16, column: 4} or specify the integer for columns based on their size, e.g. sm, md, etc. to make it responsive. | object |
| grid.gutter | no | The spacing between grid | integer |
| grid.column | no | The column of grid | integer |
| grid.xs | no | <576px column of grid | integer |
| grid.sm | no | ≥576px column of grid | integer |
| grid.md | no | ≥768px column of grid | integer |
| grid.lg | no | ≥992px column of grid | integer |
| grid.xl | no | ≥1200px column of grid | integer |
| grid.xxl | no | ≥1600px column of grid | integer |
| items | yes |  | array |
| items[].resourceRefId | yes |  | string |
| prefix | no | it's the filters prefix to get right values | string |

### Examples

```yaml
apiVersion: widgets.templates.krateo.io/v1beta1
kind: DataGrid
metadata:
  name: compositions-page-datagrid
  namespace: krateo-system
spec:
  apiRef:
    name: compositions-panels
    namespace: krateo-system
  resourcesRefs:
    items: []
  resourcesRefsTemplate:
  - iterator: ${ .compositionspanels }
    template:
      apiVersion: ${ .apiVersion }
      id: ${ .metadata.name }
      name: ${ .metadata.name }
      namespace: ${ .metadata.namespace }
      resource: panels
      verb: GET
  widgetData:
    allowedResources:
    - panels
    asGrid: true
    grid:
      column: 1
    items: []
    prefix: compositions-datagrid-filters
  widgetDataTemplate:
  - expression: |
      ${ [ .compositionspanels[] | { resourceRefId: .metadata.name } ] }
    forPath: items
```

This datagrid shows Panels in a grid format, where the list of panels is fetched with the RESTAction `compositions-panels`.