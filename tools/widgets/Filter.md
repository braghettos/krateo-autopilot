# Filters

The filter can filter ANY property of any Widget in a Page

## Props

| Property | Required | Description | Type |
|-|-|-|-|
| prefix | yes | the prefix to share filters values to other widgets | string |
| fields | yes | it defines the filters as fields of a Form | array |
| fields[].label | yes | the label of the field | string |
| fields[].name | yes | the name of the filter field, it must to be identical to the widget prop name to filter or data in dataset | array |
| fields[].description | no | text to show as tooltip | string |
| fields[].type | yes | it's the filter field type, to render input, select, radio buttons, date picker or daterange picker | `string` \| `boolean` \| `number` \| `date` \| `daterange` |
| fields[].options | no | they're the options for select or radio, the type must be 'string' | array |

Examples:
```yaml
apiVersion: widgets.templates.krateo.io/v1beta1
kind: Button
metadata:
  name: blueprints-page-button-drawer-filters
  namespace: krateo-system
spec:
  widgetData:
    icon: fa-filter
    type: primary
    size: small
    clickActionId: blueprints-page-button-drawer-filters
    actions:
      openDrawer:
        - id: blueprints-page-button-drawer-filters
          resourceRefId: blueprints-page-button-drawer-filters
          type: openDrawer
          title: Blueprints Filters
  resourcesRefs:
    items:
      - id: blueprints-page-button-drawer-filters
        apiVersion: widgets.templates.krateo.io/v1beta1
        resource: filters
        name: blueprints-page-button-drawer-filters
        namespace: krateo-system
        verb: GET
---
kind: Filters
apiVersion: widgets.templates.krateo.io/v1beta1
metadata:
  name: blueprints-page-button-drawer-filters
  namespace: krateo-system
spec:
  widgetData:
    prefix: blueprints-datagrid-filters
    fields:
      - label: Name
        name: 
        - title
        type: string
      - label: Status
        name: 
        - headerLeft
        type: string
      - label: Date
        name: 
        - headerRight
        type: daterange
      - label: Tags
        name: 
        - tags
        type: string
---
kind: Page
apiVersion: widgets.templates.krateo.io/v1beta1
metadata:
  name: blueprints-page
  namespace: krateo-system
spec:
  widgetData:
    allowedResources:
      - buttons
      - datagrids
    items:
      - resourceRefId: blueprints-page-button-drawer-filters
      - resourceRefId: blueprints-page-datagrid
  resourcesRefs:
    items:
      - id: blueprints-page-button-drawer-filters
        apiVersion: widgets.templates.krateo.io/v1beta1
        name: blueprints-page-button-drawer-filters
        namespace: krateo-system
        resource: buttons
        verb: GET
      - id: blueprints-page-datagrid
        apiVersion: widgets.templates.krateo.io/v1beta1
        name: blueprints-page-datagrid
        namespace: krateo-system
        resource: datagrids
        verb: GET
        slice:
          page: 1
          perPage: 5
---
kind: DataGrid
apiVersion: widgets.templates.krateo.io/v1beta1
metadata:
  name: compositions-page-datagrid
  namespace: krateo-system
spec:
  apiRef:
    name: compositions-panels
    namespace: krateo-system
  widgetData:
    allowedResources:
      - panels
    prefix: compositions-datagrid-filters
    asGrid: true
    grid:
      column: 1
    items: []
  widgetDataTemplate:
    - forPath: items
      expression: >
        ${ [ .compositionspanels[] | { resourceRefId: .metadata.name } ] }
  resourcesRefs: 
    items: []
  resourcesRefsTemplate:
    - iterator: ${ .compositionspanels }
      template:
        id: ${ .metadata.name }
        apiVersion: ${ .apiVersion }
        resource: panels
        namespace: ${ .metadata.namespace }
        name: ${ .metadata.name }
        verb: GET
```

The first resource (kind: Button) creates a button that opens the filter.
The second resource (kind: Filter) is the definition of the filter.
The third resource (kind: Page) simply shows the filter button and a datagrid
The last resource (kind: DataGrid) is the Datagrid being filtered. Note that it references a RESTAction that finds every Panel widget across the entire cluster that is meant for the "compositions" page, sorts them from newest to oldest, and returns a clean, paginated list ready to be displayed by a frontend widget like a datagrid.