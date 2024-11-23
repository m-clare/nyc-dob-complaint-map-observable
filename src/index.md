---
toc: false
---

```js
import maplibregl from "npm:maplibre-gl"
import { PMTiles, Protocol } from "npm:pmtiles@3.0.3";
```

```js
const maptiler3dGl = FileAttachment("assets/positron-style.json").json();
const complaintCategory = FileAttachment("assets/dobcomplaints_complaint_category.json").json();
const dobComplaints2021 = FileAttachment("assets/complaint_category.json").json();
const activeComplaints = FileAttachment("complaints.csv").csv()
```

```js
const filteredComplaints = new Set(activeComplaints.map((complaint) => complaint.complaint_category))
```


```js

const descriptionMap = new Map(
  complaintCategory.map((d) => [d.CODE, d["COMPLAINT CATEGORY DESCRIPTION"]])
);

const descriptionMap2021 = new Map(
  dobComplaints2021
    .filter((d) => filteredComplaints.has(d["COMPLAINT CATEGORY"]))
    .map((d) => [d["COMPLAINT CATEGORY"], d["COMPLAINT CATEGORY DESCRIPTION"]])
);

const complaintLayersById = [
  ...dobComplaints2021
    .map((d) => `nyc-${d["COMPLAINT CATEGORY"]}`)
    .filter((d) => filteredComplaints.has(d.split("-")[1])),
];

const priorityMap = new Map(complaintCategory.map((d) => [d.CODE, d.PRIORITY]));
```
<link rel="stylesheet" type="text/css" href="npm:maplibre-gl@4.0.2/dist/maplibre-gl.css">


```js
import {useEffect, useRef, useState} from "npm:react";
```

```js
import {HUD} from './components/HUD.js'
```

```js
const nycMap = FileAttachment("data/new-york.pmtiles")
const buildings = FileAttachment("data/nyc-buildings.pmtiles")
```

```ts
const circleColors = [
  "match",
  ["get", "highestPriority"],
  "A",
  "#e31a1c",
  "B",
  "#fd8d3c",
  "C",
  "#fecc5c",
  "D",
  "#ffffb2",
  "#f2f2f2",
];

const circleRadius = ["interpolate", ["linear"], ["zoom"], 10, 2, 15, 5];
```
## NYC Department of Buildings
### Active Complaints: ${activeComplaints.length}
```tsx
function MaplibreMap() {
  const [selectedMarkerData, setSelectedMarkerData] = useState({});
  const [hudVisible, setHudVisible] = useState(false);
  let [layersVisibility, setLayersVisibility] = useState<LayerVisibility[]>([]);
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const mapFile = new PMTiles(nycMap.href)
  const dobFile = new PMTiles(buildings.href)
  
  const getDefaultLayer = (layerId: string) => {
  return {
    id: `${layerId}`,
    type: "circle",
    "source": "dobTiles",
    "source-layer": "nyc-buildings",
    layout: { visibility: "visible" },
    paint: {
      "circle-color": circleColors,
      "circle-opacity": 0.9,
      "circle-radius": circleRadius,
    },
  } as CircleLayerSpecification;
};

  useEffect(() => {
    let protocol = new Protocol();
    maplibregl.addProtocol("pmtiles", protocol.tile);
    protocol.add(mapFile);
    protocol = new Protocol();
    maplibregl.addProtocol("pmtiles", protocol.tile);
    protocol.add(dobFile);

    const map = new maplibregl.Map({
      container: mapContainerRef.current!,
      center: [-73.935242, 40.73061],
      pitch: 20,
      zoom: 10,
      minZoom: 10,
      maxZoom: 19.9,
      maplibreLogo: true,
      logoPosition: "bottom-left",
      style: {
        version: 8,
        sources: {
          openmaptiles: {
            type: "vector",
            tiles: ["pmtiles://" + mapFile.source.getKey() + "/{z}/{x}/{y}"],
            minzoom: 6,
            maxzoom: 14,
          },
          dobTiles: {
            type: "vector",
            tiles: ["pmtiles://" + dobFile.source.getKey() + "/{z}/{x}/{y}"],
            minzoom: 6,
            maxzoom: 14,
          },
        },
        layers: maptiler3dGl.layers as LayerSpecification[],
        glyphs: "https://m-clare.github.io/map-glyphs/fonts/{fontstack}/{range}.pbf",
      },
    });
    mapRef.current = map;
    
    map.on("load", function() {
      map.resize() 
      
      const defaultLayer = getDefaultLayer("nyc-dob")
      map.addLayer(defaultLayer, "highway_name_motorway");
    })
    
    map.on("click", function (e) {
      const features = map.queryRenderedFeatures(e.point)
      const feature = features.filter((feature) =>
      new Set(["nyc-dob", ...complaintLayersById]).has(feature.layer.id)
      )[0] ?? null;
      if (feature) {
        const point = feature.geometry;
        setSelectedMarkerData(feature.properties)
        setHudVisible(true)
      } else {
        setSelectedMarkerData({})
        setHudVisible(false)
        
      }
    })

    map.addControl(
      new maplibregl.AttributionControl({
        compact: true,
        customAttribution: `<a href="https://protomaps.com">Protomaps</a> | <a href="https://openmaptiles.org">© OpenMapTiles</a> | <a href="http://www.openstreetmap.org/copyright"> © OpenStreetMap contributors</a>`,
      }),
      "bottom-left"
    );
    map.addControl(new maplibregl.NavigationControl({}), "bottom-right");

    return () => {
      map.remove();
    };
  }, []);

  return (
  <div>
    <div ref={mapContainerRef} style={{height: "600px"}}>
      <div ref={mapRef} />
      <HUD 
        rawData={selectedMarkerData} 
        descriptionMap={descriptionMap} 
        descriptionMap2021={descriptionMap2021} 
        priorityMap={priorityMap}
      />
    </div>
  </div>
  );
}
```

```tsx
display(<MaplibreMap />);
```
