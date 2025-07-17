
## Building lichtblick-suite
run:
```bash
make build
```

## Running lichtblick-suite
```bash
make start
```

## Layouts
Unless otherwise specified lichtblick will load the default layout: `Default.json`, this is saved to `../../adore_scenarios/assets/lichtblick_layouts/`.

To specify a layout use the url parameter: `layout=<layout file>.json`
```text
http://localhost:8080/?ds=foxglove-websocket&ds.url=ws://localhost:8765&layout=<layout file>.json
```

Layouts should be saved to `../../adore_scenarios/assets/lichtblick_layouts/`


### Scenario Visualization

> **ℹ️INFO:**
> Visualization requires a chrome based browser (see: https://www.chromium.org/chromium-projects/) 

1. Start `lichtblick suite` aka `foxglove` aka `foxbox`. From the `ADORe` project root run:
```bash
cd tools/lichtblick
make build
make start
```

2. Run a scenario, launch or attach to the `ADORe CLI` from the root of the `ADORe` repo:
```bash
make cli
cd adore_scenarios/simulation_scenarios
ros2 launch simulation_test.py
```

3. Open lichtblick (in another shell):
```bash
chromium http://localhost:8080/\?ds\=foxglove-websocket\&ds.url\=ws://localhost:8765\&layout\=Default.json
```
or with a link:
[http://localhost:8080/?ds=foxglove-websocket&ds.url=ws://localhost:8765&layout=Default.json](http://localhost:8080/?ds=foxglove-websocket&ds.url=ws://localhost:8765&layout=Default.json)


