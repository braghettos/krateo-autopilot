### Table

Table displays structured data with customizable columns and pagination

#### Props

| Property | Required | Description | Type |
|-|-|-|---|
| allowedResources | yes | the list of resources that are allowed to be children of this widget or referenced by it | array |
| columns | yes | configuration of the table's columns | array |
| columns[].color | no | the color of the value (or the icon) to be represented | `blue` \| `darkBlue` \| `orange` \| `gray` \| `red` \| `green` |
| columns[].title | yes | column header label | string |
| columns[].valueKey | yes | key used to extract the value from row data | string |
| data | yes | Array of table rows | array |
| pageSize | no | number of rows displayed per page | integer |
| prefix | no | it's the filters prefix to get right values | string |

Example:
```yaml
kind: Table
apiVersion: widgets.templates.krateo.io/v1beta1
metadata:
  name: my-table
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
    pageSize: 10
    data: 
      - 
        - valueKey: name
          kind: jsonSchemaType
          type: string
          stringValue: Alice
        - valueKey: age
          kind: jsonSchemaType
          type: integer
          numberValue: 30
        - valueKey: icon
          kind: icon
          stringValue: fa-rocket

      - 
        - valueKey: name
          kind: jsonSchemaType
          type: string
          stringValue: Bob
        - valueKey: age
          kind: jsonSchemaType
          type: integer
          numberValue: 45
        - valueKey: icon
          kind: icon
          stringValue: fa-exclamation-circle

    columns:
      - valueKey: name
        title: Name
      - valueKey: age
        title: Age
      - valueKey: icon
        title: Icon
        kind: icon
        color: red
```