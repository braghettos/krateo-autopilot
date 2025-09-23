### Form

A classic form that collects user input through fields like text boxes and checkboxes

#### Props

| Property | Required | Description | Type |
|-|-|-|-|
| actions | yes | the actions of the widget | object |
| actions.rest | no | rest api call actions triggered by the widget | array |
| actions.rest[].payloadKey | no | key used to nest the payload in the request body | string |
| actions.rest[].headers | yes |  | array |
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
| buttonConfig | no | custom labels and icons for form buttons | object |
| buttonConfig.primary | no | primary button configuration | object |
| buttonConfig.primary.label | no | text label for primary button | string |
| buttonConfig.primary.icon | no | icon name for primary button | string |
| buttonConfig.secondary | no | secondary button configuration | object |
| buttonConfig.secondary.label | no | text label for secondary button | string |
| buttonConfig.secondary.icon | no | icon name for secondary button | string |
| schema | no | the schema of the form as an object | object |
| stringSchema | no | the schema of the form as a string | string |
| submitActionId | yes | the id of the action to be called when the form is submitted | string |
| fieldDescription | no |  | `tooltip` \| `inline` |
| autocomplete | no | autocomplete configuration for the form fields | array |
| autocomplete[].path | yes | the path of the field to apply autocomplete | string |
| autocomplete[].fetch | yes | remote data source configuration for autocomplete | object |
| autocomplete[].fetch.url | yes | the URL to fetch autocomplete options from | string |
| autocomplete[].fetch.verb | yes | HTTP method to use for fetching options | `GET` \| `POST` |
| dependencies | no | list of dependencies for the form fields | array |
| dependencies[].path | yes | the path of the field | string |
| dependencies[].dependsField | yes |  | object |
| dependencies[].dependsField.field | no | the field that this field depends on | string |
| dependencies[].fetch | yes |  | object |
| dependencies[].fetch.url | yes | the URL to fetch options | string |
| dependencies[].fetch.verb | yes | HTTP method to use for fetching options | `GET` \| `POST` |
| objectFields | no | configuration for object fields in the form | array |
| objectFields[].path | yes | the path of the object field | string |
| objectFields[].displayField | yes | the field to display in the objects list | string |

Example:
```yaml
kind: Form
apiVersion: widgets.templates.krateo.io/v1beta1
metadata:
  name: form-example
  namespace: test-namespace
spec:
  widgetData:
    submitActionId: firework-submit-action
    stringSchema: |
      {
        "type": "object",
        "properties": {
          "name": {
            "type": "string",
            "title": "Application Name",
            "description": "The name of your fireworks app"
          },
          "image": {
            "type": "string",
            "title": "Container Image",
            "description": "Full image path (e.g., ghcr.io/org/image:tag)"
          },
          "replicas": {
            "type": "integer",
            "title": "Number of Replicas",
            "default": 1
          },
          "enableMetrics": {
            "type": "boolean",
            "title": "Enable Metrics",
            "default": false
          }
        },
        "required": ["name", "image"]
      }
    autocomplete:
      - path: name
        fetch:
          url: https://loremipsum.io/api/1
          method: GET
    actions:
      rest:
        - id: firework-submit-action
          headers:  
            - 'Content-Type: application/json'
          resourceRefId: resource-ref-1
          type: rest
          onSuccessNavigateTo: /dashboard
          payloadToOverride:
            - name: metadata.name
              value: ${ git.toRepo.name } # git.toRepo.name is NOT a state variable or artifact. DO NOT try to access it
  resourcesRefs:
    items:
      - id: resource-ref-1
        apiVersion: composition.krateo.io/v2-0-0
        name: new-app
        namespace: test-namespace
        resource: fireworksapps
        verb: POST
```

> NOTE: ALWAYS include actions.rest[].headers as shown in the example above.
> NOTE: in the `value` of the `payloadToOverride` ALWAYS access variables using `x.y.z`, NOT with a leading dot as in `.x.y.z`  
  Example: 
  - if the variable is named `name`, use `name`, not `.name`
  - if the variable is named `metadata.namespace`, use `metadata.namespace`, not `.metadata.namespace`! 
