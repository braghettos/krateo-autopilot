### LineChart

LineChart displays a customizable line chart based on time series or numerical data. It supports multiple lines with colored coordinates and axis labels, typically used to visualize metrics from Kubernetes resources

#### Props

| Property | Required | Description | Type |
|-|-|-|---|
| prefix | no | it's the filters prefix to get right values | string |
| lines | yes | list of data series to be rendered as individual lines | array |
| lines[].name | no | label of the line displayed in the legend | string |
| lines[].color | no | color used to render the line | `blue` \| `darkBlue` \| `orange` \| `gray` \| `red` \| `green` |
| lines[].coords | no | data points that define the line | array |
| lines[].coords[].xAxis | yes | value on the x axis | string |
| lines[].coords[].yAxis | yes | value on the y axis | string |
| xAxisName | no | label for the x axis | string |
| yAxisName | no | label for the y axis | string |

Example:
```yaml
kind: LineChart
apiVersion: widgets.templates.krateo.io/v1beta1
metadata:
  name: my-line-chart
  namespace: test-namespace
spec:
  widgetData:
    lines:
      - name: blue line
        color: blue
        coords:
          - xAxis: 0
            yAxis: 15
          - xAxis: 1
            yAxis: 52
          - xAxis: 2
            yAxis: 15
          - xAxis: 3
            yAxis: 52
      - name: red line
        color: red
        coords:
          - xAxis: 0
            yAxis: 4
          - xAxis: 1
            yAxis: 8
          - xAxis: 2
            yAxis: 12
          - xAxis: 3
            yAxis: 2
    xAxisName: time
    yAxisName: cost
```