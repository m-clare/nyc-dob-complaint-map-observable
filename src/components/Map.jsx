import maplibregl from "maplibre-gl";
import { PMTiles, Protocol } from "pmtiles";

export function Card({ title, children } = {}) {
  return (
    <div className="card">
      {title ? <h2>{title}</h2> : null}
      {children}
    </div>
  );
}
