### NavMenu

NavMenu is a container for NavMenuItem widgets, which are used to setup navigation inside the application

#### Props

| Property | Required | Description | Type |
|----------|----------|-------------|------|
| allowedResources | yes | the list of resources that are allowed to be children of this widget or referenced by it | array |
| items | yes | list of navigation entries each pointing to a k8s custom resource | array |
| items[].resourceRefId | yes | the identifier of the k8s custom resource that should be represented, usually a NavMenuItem | string |

Example:
```yaml
kind: NavMenu
apiVersion: widgets.templates.krateo.io/v1beta1
metadata:
  name: sidebar-nav-menu
  namespace: test-namespace
spec:
  widgetData:
    allowedResources:
      - navmenuitems
    items:
      - resourceRefId: nav-menu-item-templates
  resourcesRefs:
    items:
      - id: nav-menu-item-templates
        apiVersion: widgets.templates.krateo.io/v1beta1
        name: nav-menu-item-templates
        namespace: test-namespace
        resource: navmenuitems
        verb: GET
```