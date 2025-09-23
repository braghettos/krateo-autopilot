### FlowChart

FlowChart represents a Kubernetes composition as a directed graph. Each node represents a resource, and edges indicate parent-child relationships

#### Props

| Property | Required | Description | Type |
|-|-|-|-|
| data | no | list of kubernetes resources and their relationships to render as nodes in the flow chart | array |
| data[].date | yes | optional date value to be shown in the node, formatted as ISO 8601 string | string |
| data[].icon | no | custom icon displayed for the resource node | object |
| data[].icon.name | no | FontAwesome icon class name (e.g. 'fa-check') | string |
| data[].icon.color | no | CSS color value for the icon background | `blue` \| `darkBlue` \| `orange` \| `gray` \| `red` \| `green` \| `violet` |
| data[].icon.message | no | optional tooltip message displayed on hover | string |
| data[].statusIcon | no | custom status icon displayed alongside resource info | object |
| data[].statusIcon.name | no | FontAwesome icon class name representing status | string |
| data[].statusIcon.color | no | CSS color value for the status icon background | `blue` \| `darkBlue` \| `orange` \| `gray` \| `red` \| `green` \| `violet` |
| data[].statusIcon.message | no | optional tooltip message describing the status | string |
| data[].kind | yes | kubernetes resource type (e.g. Deployment, Service) | string |
| data[].name | yes | name of the resource | string |
| data[].namespace | yes | namespace in which the resource is defined | string |
| data[].parentRefs | no | list of parent resources used to define graph relationships | array |
| data[].parentRefs[].date | no | optional date value to be shown in the node, formatted as ISO 8601 string | string |
| data[].parentRefs[].icon | no | custom icon for the parent resource | object |
| data[].parentRefs[].icon.name | no | FontAwesome icon class name | string |
| data[].parentRefs[].icon.color | no | CSS color value for the icon background | `blue` \| `darkBlue` \| `orange` \| `gray` \| `red` \| `green` \| `violet` |
| data[].parentRefs[].icon.message | no | optional tooltip message | string |
| data[].parentRefs[].statusIcon | no | custom status icon for the parent resource | object |
| data[].parentRefs[].statusIcon.name | no | FontAwesome icon class name | string |
| data[].parentRefs[].statusIcon.color | no | CSS color value for the status icon background | `blue` \| `darkBlue` \| `orange` \| `gray` \| `red` \| `green` \| `violet` |
| data[].parentRefs[].statusIcon.message | no | optional tooltip message | string |
| data[].parentRefs[].kind | no | resource type of the parent | string |
| data[].parentRefs[].name | no | name of the parent resource | string |
| data[].parentRefs[].namespace | no | namespace of the parent resource | string |
| data[].parentRefs[].parentRefs | no | nested parent references for recursive relationships | array |
| data[].parentRefs[].resourceVersion | no | internal version string of the parent resource | string |
| data[].parentRefs[].uid | no | unique identifier of the parent resource | string |
| data[].parentRefs[].version | no | api version of the parent resource | string |
| data[].resourceVersion | yes | internal version string of the resource | string |
| data[].uid | yes | unique identifier of the resource | string |
| data[].version | yes | api version of the resource | string |

Example:
```yaml
kind: FlowChart
apiVersion: widgets.templates.krateo.io/v1beta1
metadata:
  name: my-flow-chart
  namespace: test-namespace
spec:
  widgetData:
    data:
      - date: "2025-07-24T15:30:36Z"
        icon:
          name: "fa-cubes"
          color: "blue"
        statusIcon:
          name: "fa-check"
          color: "green"
          message: "Available"
        kind: "FrontendGithubScaffolding"
        name: "test2"
        namespace: "demo-system"
        parentRefs:
          - {}
        resourceVersion: ""
        uid: "1eed3c65-90d2-4823-a85c-3430d4e41944"
        version: "composition.krateo.io/v0-0-1"

      - date: "2024-07-31T15:30:39Z"
        icon:
          name: "fa-file-alt"
          color: "orange"
        statusIcon:
          name: "fa-ellipsis"
          color: "blue"
          message: "Progressing"
        kind: "ConfigMap"
        name: "test2-replace-values"
        namespace: "demo-system"
        parentRefs:
          - kind: "FrontendGithubScaffolding"
            name: "test2"
            namespace: "demo-system"
            parentRefs: [{}]
            uid: "1eed3c65-90d2-4823-a85c-3430d4e41944"
            version: "composition.krateo.io/v0-0-1"
        resourceVersion: "77493"
        uid: "e99a3efe-7461-4ffe-b956-55cb3882f0c5"
        version: "v1"

      - date: "2025-07-31T15:30:39Z"
        icon:
          name: "fa-cogs"
          color: "gray"
        statusIcon:
          name: "fa-pause"
          color: "orange"
          message: "Suspended"
        kind: "Application"
        name: "test2"
        namespace: "krateo-system"
        parentRefs:
          - kind: "FrontendGithubScaffolding"
            name: "test2"
            namespace: "demo-system"
            parentRefs: [{}]
            uid: "1eed3c65-90d2-4823-a85c-3430d4e41944"
            version: "composition.krateo.io/v0-0-1"
        resourceVersion: "2769771"
        uid: "10c62b82-8096-4f40-a991-8f1a420a7c42"
        version: "argoproj.io/v1alpha1"

      - date: "2025-07-31T15:30:39Z"
        icon:
          name: "fa-database"
          color: "violet"
        statusIcon:
          name: "fa-xmark"
          color: "red"
          message: "Degraded"
        kind: "Repo"
        name: "test2-repo"
        namespace: "demo-system"
        parentRefs:
          - kind: "FrontendGithubScaffolding"
            name: "test2"
            namespace: "demo-system"
            parentRefs: [{}]
            uid: "1eed3c65-90d2-4823-a85c-3430d4e41944"
            version: "composition.krateo.io/v0-0-1"
        resourceVersion: "2771491"
        uid: "36177476-08c3-42dd-a148-48d0b94bbf13"
        version: "git.krateo.io/v1alpha1"

      - date: "2025-07-31T15:30:39Z"
        icon:
          name: "fa-book"
          color: "red"
        statusIcon:
          name: "fa-question"
          color: "gray"
          message: "Unknown"
        kind: "Repo"
        name: "test2-repo"
        namespace: "demo-system"
        parentRefs:
          - kind: "FrontendGithubScaffolding"
            name: "test2"
            namespace: "demo-system"
            parentRefs: [{}]
            uid: "1eed3c65-90d2-4823-a85c-3430d4e41944"
            version: "composition.krateo.io/v0-0-1"
        resourceVersion: "77512"
        uid: "cc1fb868-3ae9-435a-a748-aa54dcd1b26b"
        version: "github.kog.krateo.io/v1alpha1"
```