### BarChart

BarChart express quantities through a bar's length, using a common baseline. Bar charts series should contain a `data` property containing an array of values

#### Props

| Property | Required | Description | Type |
|-|-|-|-|
| data | yes | Array of grouped data entries for the bar chart | array |
| data[].label | no | Label for the group/category | string |
| data[].bars | yes | Bars within the group, each representing a value | array |
| data[].bars[].value | yes | Label or identifier for the bar | string |
| data[].bars[].percentage | yes | Height of the bar as a percentage (0–100) | integer |
| data[].bars[].color | no | Color of the bar | `blue` \| `darkBlue` \| `orange` \| `gray` \| `red` \| `green` |

Example:
```yaml
kind: BarChart
apiVersion: widgets.templates.krateo.io/v1beta1
metadata:
  name: my-bar-chart
  namespace: test-namespace
spec:
  widgetData:
    data:
      - label: CPU usage
        bars:
          - value: "1982"
            percentage: 75
            color: blue
          - value: "75"
            percentage: 12
            color: red
      - label: RAM usage
        bars:
          - value: "72"
            percentage: 12
            color: orange
      - label: Temperature
        bars:
          - value: "63"
            percentage: 85
            color: red
```