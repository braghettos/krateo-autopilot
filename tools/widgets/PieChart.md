### PieChart

PieChart is a visual component used to display categorical data as segments of a pie chart

#### Props

| Property | Required | Description | Type |
|-|-|-|---|
| title | yes | title displayed above the chart | string |
| description | no | supplementary text displayed below or near the title | string |
| series | no | data to be visualized in the pie chart | object |
| series.total | yes | sum of all data values, used to calculate segment sizes | integer |
| series.data | yes | individual segments of the pie chart | array |
| series.data[].color | yes | color used to represent the segment | `blue` \| `darkBlue` \| `orange` \| `gray` \| `red` \| `green` \| `violet` |
| series.data[].value | yes | numeric value for the segment | integer |
| series.data[].label | yes | label for the segment | string |

Example:
```yaml
kind: PieChart
apiVersion: widgets.templates.krateo.io/v1beta1
metadata:
  name: my-pie-chart
  namespace: test-namespace
spec:
  widgetData:
    title: Pie chart
    description: This is a description
    series:
      total: 100
      data:
        - color: blue
          value: 10
          label: Blue
        - color: darkBlue
          value: 20
          label: Dark Blue
        - color: orange
          value: 30
          label: Orange
```