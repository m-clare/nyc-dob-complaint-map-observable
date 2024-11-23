---
toc: false
---

<style> 
#observablehq-footer {
   margin-top: 1rem;
   margin-bottom: 1rem;
 }

h1, h2, h3, h4, h5, h6 {
   font-family: "Roboto","Helvetica","Arial",sans-serif
}
</style>

```js
import maplibregl from "npm:maplibre-gl"
import { PMTiles, Protocol } from "npm:pmtiles@3.0.3";
```

```js
const maptiler3dGl = FileAttachment("assets/positron-style.json").json();
const complaintCategory = FileAttachment("assets/dobcomplaints_complaint_category.json").json();
const dobComplaints2021 = FileAttachment("assets/complaint_category.json").json();
const activeComplaints = FileAttachment("complaints.csv").csv()
const disposition = FileAttachment("assets/disposition.csv").csv()
```

```js
const runDate = new Set(activeComplaints.map((complaint) => complaint.dobrundate))
const filteredComplaints = new Set(activeComplaints.map((complaint) => complaint.complaint_category))
```

```js
const dispositionMap = new Map(disposition.map((d) => ([d.code, d.text])))

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

const mergedComplaintDescription = new Map([...descriptionMap2021, descriptionMap])
```

```js
function getBorough(zipCode) {
    const zip = parseInt(zipCode);

    if (isNaN(zip) || zip.toString().length !== 5) {
        throw new Error('Invalid ZIP code format. Please provide a 5-digit ZIP code.');
    }

    // Manhattan
    if (zip >= 10001 && zip <= 10282) {
        return 'Manhattan';
    }

    // Staten Island
    if (zip >= 10301 && zip <= 10314) {
        return 'Staten Island';
    }

    // Bronx
    if (zip >= 10451 && zip <= 10475) {
        return 'Bronx';
    }

    // Queens
    if ((zip >= 11001 && zip <= 11109) || (zip >= 11351 && zip <= 11697)) {
        return 'Queens';
    }

    // Brooklyn
    if (zip >= 11201 && zip <= 11256) {
        return 'Brooklyn';
    }

    // If no match is found
    console.log(zip)
    return 'Invalid NYC Zip Code';
}
```
<link rel="stylesheet" type="text/css" href="npm:maplibre-gl@4.0.2/dist/maplibre-gl.css">

```js
const complaintsByBorough = d3.flatRollup(activeComplaints.map((complaint) => ({...complaint, borough: getBorough(complaint.zip_code)})), v => v.length, d => d.complaint_category, d => d.borough).map((entry) => ({complaintCategory: mergedComplaintDescription.get(entry[0]) ?? entry[0], borough: entry[1], count: entry[2]}))
```
```js
const sortedComplaints = Array.from(d3.rollup(complaintsByBorough, v => ({
total: d3.sum(v, d => d.count), boroughs: v
}), d => d.complaintCategory)).sort((a, b) => b[1].total - a[1].total)
```
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
  "#a4a4a4",
];

const circleRadiusWithLimits = [
  "interpolate",
  ["linear"],
  ["zoom"],
  10, [
    "min",
    ["max", 
      ["*", ["get", "count"], 0.3],  // Base size calculation
      2                              // Minimum size
    ],
    12                               // Maximum size
  ],
  15, [
    "min",
    ["max",
      ["*", ["get", "count"], 0.6],  // Larger base size at higher zoom
      5                              // Larger minimum size
    ],
    30                               // Larger maximum size
  ]
];
```
## [NYC Department of Buildings](https://data.cityofnewyork.us/Housing-Development/DOB-Complaints-Received/eabe-havv/about_data)
### Active Complaints: ${activeComplaints.length}
### Date Run: ${runDate}

```js
Inputs.table(activeComplaints)
```
```js
const complaintsInput = view(Inputs.select(new Map(sortedComplaints.map((entry) => ([`${entry[0]} (${entry[1].total})`, entry[0]]))), {multiple: true, label: "Complaints Category", width: 550}))
```
```js
const selectedValues = complaintsInput.length > 0 ? sortedComplaints.filter((value) => complaintsInput.includes(value[0])).map((complaintCategory) => (complaintCategory[1].boroughs)).flat() : sortedComplaints[0][1].boroughs
```
```js
Plot.plot({
  x: {tickFormat: "s", grid: true},
  y: {axis: null},
  color: {scheme: "Observable10", legend: true, type: "ordinal"},
  marks: [
    Plot.barX(selectedValues, {
      y: "borough",
      x: "count",
      fill: "borough",
      fy: "complaintCategory",
      sort: {y: "y"}
    }),
    Plot.ruleX([0]),
  ],
  width: 1376,
  "marginLeft": 360,
})
```

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
      "circle-radius": circleRadiusWithLimits,
      "circle-stroke-width": 0.5,
      "circle-stroke-color": '#fff'
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
      maxBounds: [[-74.47288248742949, 40.46738321871237], [-73.39760151257211, 41.06502038646664 ]],
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
    <div ref={mapContainerRef} style={{minHeight: "80vh"}}>
      <div ref={mapRef} />
      {hudVisible && <HUD 
        rawData={selectedMarkerData} 
        descriptionMap={descriptionMap} 
        descriptionMap2021={descriptionMap2021} 
        priorityMap={priorityMap}
        dispositionMap={dispositionMap}
      />
      }
    </div>
  </div>
  );
}
```

```tsx
display(<MaplibreMap />);
```
