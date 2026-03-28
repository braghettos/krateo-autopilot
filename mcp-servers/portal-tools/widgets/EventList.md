### EventList

EventList renders data coming from a Kubernetes cluster or Server Sent Events associated to a specific endpoint and topic

#### Props

| Property | Required | Description | Type |
|-|-|-|-|
| events | yes | list of events received from a k8s cluster or server sent event | array |
| events[].icon | no | name of the icon associated with the event (font awesome icon name eg: `fa-inbox`) | string |
| events[].reason | yes | reason or cause of the event | string |
| events[].message | yes | descriptive message of the event | string |
| events[].type | yes | type of the event, e.g., normal or warning | `Normal` \| `Warning` |
| events[].count | no | number of times the event has occurred | integer |
| events[].action | no | action associated with the event, if any | string |
| events[].reportingComponent | no | component that reported the event | string |
| events[].reportingInstance | no | instance of the component that reported the event | string |
| events[].firstTimestamp | no | timestamp of the first occurrence of the event | string |
| events[].lastTimestamp | no | timestamp of the last occurrence of the event | string |
| events[].eventTime | no | specific timestamp of the event | string |
| events[].metadata | yes | metadata of the event such as name, namespace, and uid | object |
| events[].metadata.name | yes | unique name of the event | string |
| events[].metadata.namespace | yes | namespace the event belongs to | string |
| events[].metadata.uid | yes | unique identifier of the event | string |
| events[].metadata.creationTimestamp | yes | creation date and time of the event | string |
| events[].involvedObject | yes | object involved in the event with key details | object |
| events[].involvedObject.apiVersion | no | api version of the involved object | string |
| events[].involvedObject.kind | yes | resource type involved | string |
| events[].involvedObject.name | yes | name of the involved object | string |
| events[].involvedObject.namespace | yes | namespace of the involved object | string |
| events[].involvedObject.uid | yes | unique identifier of the involved object | string |
| events[].source | yes | information about the source generating the event | object |
| events[].source.component | no | component source of the event | string |
| events[].source.host | no | host where the event originated | string |
| prefix | no | filter prefix used to filter data | string |
| sseEndpoint | no | endpoint url for server sent events connection | string |
| sseTopic | no | subscription topic for server sent events | string |

Example:
```yaml
kind: EventList
apiVersion: widgets.templates.krateo.io/v1beta1
metadata:
  name: my-event-list
  namespace: test-namespace
spec:
  widgetData:
    events:
      - icon: "fa-exclamation-circle"
        reason: "FailedScheduling"
        message: "0/1 nodes are available: 1 Insufficient memory."
        type: "Warning"
        count: 3
        firstTimestamp: "2024-04-20T12:34:56Z"
        lastTimestamp: "2024-04-20T12:45:00Z"
        metadata:
          name: "my-pod.17d90d9c8ab2b1e1"
          namespace: "default"
          uid: "d1234567-89ab-4def-8123-abcdef012345"
          creationTimestamp: "2024-04-20T12:34:56Z"
        involvedObject:
          apiVersion: "v1"
          kind: "Pod"
          name: "my-pod"
          namespace: "default"
          uid: "abcd-1234"
        source:
          component: "scheduler"
      - icon: "fa-rocket"
        reason: "Started"
        message: "Started container nginx"
        type: "Normal"
        metadata:
          name: "nginx-pod.17d90d9c8ab2b1e2"
          namespace: "default"
          uid: "f1234567-89ab-4def-8123-abcdef012346"
          creationTimestamp: "2024-04-21T08:20:00Z"
        involvedObject:
          apiVersion: "v1"
          kind: "Pod"
          name: "nginx-pod"
          namespace: "default"
          uid: "defg-5678"
        source:
          component: "kubelet"
          host: "worker-node-1"
    sseEndpoint: "/events/stream"
    sseTopic: "k8s-event"
```