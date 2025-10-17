# InlineGroup

widget di layout che permette di disporre widget figli in riga specificando l’allineamento (prop alignment) rispetto alla pagina (sinistra, centro, destra) e la spaziatura tra elementi (prop gap). In questo modo è possibile ad esempio inserire due bottoni allineati a destra della pagina senza fare magheggi con le Row.

> NOTE: not in the set of available widgets at the moment

## Props

| Property | Required | Description | Type |
|-|-|-|-|
| alignment | no | the alignment of the element inside the InlineGroup. Default is 'left' | `center` \| `left` \| `right` |
| allowedResources | yes | the list of resources that are allowed to be children of this widget or referenced by it | array |
| gap | no | the spacing between the items of the InlineGroup. Default is 'small' | `extra-small` \| `small` \| `medium` \| `large` |
| items | yes | the items of the InlineGroup | array |
| items[].resourceRefId | yes |  | string |

<details>
<summary>Example</summary>

```yaml
kind: InlineGroup
apiVersion: widgets.templates.krateo.io/v1beta1
metadata:
  name: test-inline-group
  namespace: test-namespace
spec:
  widgetData:
    alignment: center
    allowedResources:
      - barcharts
      - buttons
      - eventlists
      - filters
      - flowcharts
      - forms
      - linecharts
      - markdowns
      - panels
      - paragraphs
      - piecharts
      - tables
      - tablists
      - yamlviewers
    gap: medium
    items:
      - resourceRefId: button-1
      - resourceRefId: button-2
  resourcesRefs:
    items:
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