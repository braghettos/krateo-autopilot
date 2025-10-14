### NavMenuItem

NavMenuItem represents a single item in the navigation menu and links to a specific resource and route in the application

#### Props

| Property | Required | Description | Type |
|-|-|-|---|
| allowedResources | yes | the list of resources that are allowed to be children of this widget or referenced by it | array |
| icon | yes | name of the icon to display alongside the label (font awesome icon name eg: `fa-inbox`) | string |
| label | yes | text displayed as the menu item's label | string |
| order | no | a weight to be used to sort the items in the menu | integer |
| path | yes | route path to navigate to when the menu item is clicked | string |
| resourceRefId | yes | the identifier of the k8s custom resource that should be represented, usually a widget | string |

Example:
```yaml
kind: NavMenuItem
apiVersion: widgets.templates.krateo.io/v1beta1
metadata:
  name: nav-menu-item-templates
  namespace: test-namespace
spec:
  widgetData:
    allowedResources:
      - pages
    resourceRefId: templates-page
    label: Templates
    icon: fa-rectangle-list
    path: /templates
    order: 20

  resourcesRefs:
    items:
      - id: templates-page
        apiVersion: widgets.templates.krateo.io/v1beta1
        name: templates-page
        namespace: test-namespace
        resource: pages
        verb: GET
```