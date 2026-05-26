# Cube configuration options: https://cube.dev/docs/config

from cube import config


@config('semantic_layer_sync')
def sls(ctx: dict) -> list:
    return [
    {
      "type": "metabase",
      "name": "Metabase Sync",
      "config": {
        "database": "Cube Cloud: LosCanastos",
        "password": "AC3Qru3lDST1AL",
        "url": "18.205.127.235",
        "user": "fdo@g-tech.io"
      }
    },
    {
      "name": "Preset Sync",
      "type": "preset",
      "config": {
        "api_secret": "b3e648b1f2416c081a4d3249f56bab4be3a74594b83426cf0bf96575e6a03488",
        "api_token": "c6875da9-7971-4452-9444-d102477cfea7",
        "database": "Cube Cloud: Cube-LC",
        "workspace_url": "dd4316c6.us1a.app.preset.io"
      }
    }
]
