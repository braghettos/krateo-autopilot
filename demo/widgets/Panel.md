### Panel

Panel is a container to display information

#### Props

| Property | Required | Description | Type |
|-|-|-|-|
| actions | yes | the actions of the widget | object |
| actions.rest | no | rest api call actions triggered by the widget | array |
| actions.rest[].payloadKey | no | key used to nest the payload in the request body | string |
| actions.rest[].headers | no |  | array |
| actions.rest[].id | yes | unique identifier for the action | string |
| actions.rest[].resourceRefId | yes | the identifier of the k8s custom resource that should be represented | string |
| actions.rest[].requireConfirmation | no | whether user confirmation is required before triggering the action | boolean |
| actions.rest[].onSuccessNavigateTo | no | url to navigate to after successful execution | string |
| actions.rest[].errorMessage | no | a message that will be displayed inside a toast in case of error | string |
| actions.rest[].successMessage | no | a message that will be displayed inside a toast in case of success | string |
| actions.rest[].onEventNavigateTo | no | conditional navigation triggered by a specific event | object |
| actions.rest[].onEventNavigateTo.eventReason | yes | identifier of the awaited event reason | string |
| actions.rest[].onEventNavigateTo.url | yes | url to navigate to when the event is received | string |
| actions.rest[].onEventNavigateTo.timeout | no | the timeout in seconds to wait for the event | integer |
| actions.rest[].onEventNavigateTo.reloadRoutes | no |  | boolean |
| actions.rest[].onEventNavigateTo.loadingMessage | no | message to display while waiting for the event | string |
| actions.rest[].type | yes | type of action to execute | `rest` |
| actions.rest[].payload | no | static payload sent with the request | object |
| actions.rest[].payloadToOverride | no | list of payload fields to override dynamically | array |
| actions.rest[].payloadToOverride[].name | yes | name of the field to override | string |
| actions.rest[].payloadToOverride[].value | yes | value to use for overriding the field | string |
| actions.rest[].loading | no |  | object |
| actions.rest[].loading.display | yes |  | boolean |
| actions.navigate | no | client-side navigation actions | array |
| actions.navigate[].id | yes | unique identifier for the action | string |
| actions.navigate[].loading | no |  | object |
| actions.navigate[].loading.display | yes |  | boolean |
| actions.navigate[].path | no | the identifier of the route to navigate to | string |
| actions.navigate[].resourceRefId | no | the identifier of the k8s custom resource that should be represented | string |
| actions.navigate[].requireConfirmation | no | whether user confirmation is required before navigating | boolean |
| actions.navigate[].type | yes | type of navigation action | `navigate` |
| actions.openDrawer | no | actions to open side drawer components | array |
| actions.openDrawer[].id | yes | unique identifier for the drawer action | string |
| actions.openDrawer[].type | yes | type of drawer action | `openDrawer` |
| actions.openDrawer[].resourceRefId | yes | the identifier of the k8s custom resource that should be represented | string |
| actions.openDrawer[].requireConfirmation | no | whether user confirmation is required before opening | boolean |
| actions.openDrawer[].size | no | drawer size to be displayed | `default` \| `large` |
| actions.openDrawer[].title | no | title shown in the drawer header | string |
| actions.openDrawer[].loading | no |  | object |
| actions.openDrawer[].loading.display | yes |  | boolean |
| actions.openModal | no | actions to open modal dialog components | array |
| actions.openModal[].id | yes | unique identifier for the modal action | string |
| actions.openModal[].type | yes | type of modal action | `openModal` |
| actions.openModal[].resourceRefId | yes | the identifier of the k8s custom resource that should be represented | string |
| actions.openModal[].requireConfirmation | no | whether user confirmation is required before opening | boolean |
| actions.openModal[].title | no | title shown in the modal header | string |
| actions.openModal[].loading | no |  | object |
| actions.openModal[].loading.display | yes |  | boolean |
| clickActionId | no | the id of the action to be executed when the panel is clicked | string |
| footer | no | footer section of the panel containing additional items | array |
| footer[].resourceRefId | yes | the identifier of the k8s custom resource that should be represented, usually a widget | string |
| headerLeft | no | optional text to be displayed under the title, on the left side of the Panel | string |
| headerRight | no | optional text to be displayed under the title, on the right side of the Panel | string |
| icon | no | icon displayed in the panel header | object |
| icon.name | yes | name of the icon to display (font awesome icon name eg: `fa-inbox`) | string |
| icon.color | no | color of the icon | string |
| items | yes | list of resource references to display as main content in the panel | array |
| items[].resourceRefId | yes | the identifier of the k8s custom resource that should be represented, usually a widget | string |
| tags | no | list of string tags to be displayed in the footer | array |
| title | no | text to be displayed as the panel title | string |
| tooltip | no | optional tooltip text shown on the top right side of the card to provide additional context | string |

Example:
```yaml
kind: Panel
apiVersion: widgets.templates.krateo.io/v1beta1
metadata:
  name: my-panel
  namespace: test-namespace
spec:
  widgetData:
    actions: {}
    title: My Panel
    items:
      - resourceRefId: my-pie-chart
      - resourceRefId: my-table
    tooltip: this is a tooltip!
    footer:
      - resourceRefId: button-1
      - resourceRefId: button-2
  resourcesRefs:
    items:
      - id: my-table
        apiVersion: widgets.templates.krateo.io/v1beta1
        name: my-table
        namespace: test-namespace
        resource: tables
        verb: GET
      - id: my-pie-chart
        apiVersion: widgets.templates.krateo.io/v1beta1
        name: my-pie-chart
        namespace: test-namespace
        resource: piecharts
        verb: GET
      - id: button-1
        apiVersion: widgets.templates.krateo.io/v1beta1
        name: button-1
        namespace: test-namespace
        resource: buttons
        verb: GET
      - id: button-2
        apiVersion: widgets.templates.krateo.io/v1beta1
        name: button-2
        namespace: test-namespace
        resource: buttons
        verb: GET
```

> NOTE: ALWAYS include `spec.widgets.actions: {}`; it is required.