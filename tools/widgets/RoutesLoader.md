# RoutesLoader

RoutesLoader loads the Route widgets. It doesn't render anything by itself.

## Props

| Property | Required | Description | Type |
|-|-|-|-|
| allowedResources | yes | the list of resources that are allowed to be children of this widget or referenced by it | array |

## Example

```yaml
apiVersion: widgets.templates.krateo.io/v1beta1
kind: RoutesLoader
metadata:
  name: routes-loader
  namespace: krateo-system
spec:
  apiRef:
    name: all-routes
    namespace: krateo-system
  resourcesRefs:
    items: []
  resourcesRefsTemplate:
  - iterator: ${ .routes }
    template:
      apiVersion: ${ .apiVersion }
      id: ${ .metadata.namespace + "_" + .metadata.name }
      name: ${ .metadata.name }
      namespace: ${ .metadata.namespace }
      resource: routes
      verb: GET
  widgetData:
    allowedResources:
    - routes
```