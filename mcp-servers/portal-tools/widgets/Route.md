# Route

Route is a configuration to map a path to show in the frontend URL to a resource, it doesn't render anything by itself

## Props

| Property | Required | Description | Type |
|-|-|-|-|
| path | yes | the url path to that loads the resource | string |
| resourceRefId | yes | the id matching the resource in the resourcesRefs array, must of kind page | string |

### Examples

```yaml
apiVersion: widgets.templates.krateo.io/v1beta1
kind: Route
metadata:
  name: demo-system-compositions-route
  namespace: demo-system
spec:
  resourcesRefs:
    items:
    - apiVersion: widgets.templates.krateo.io/v1beta1
      id: demo-system-compositions-page-datagrid
      name: demo-system-compositions-page-datagrid
      namespace: demo-system
      resource: datagrids
      verb: GET
  widgetData:
    path: /compositions/demo-system
    resourceRefId: demo-system-compositions-page-datagrid
```