import { FormattedEntry } from "./FormattedEntry.js";
const styles = {
  container: {
    marginLeft: "auto",
    marginRight: "auto",
    padding: "0 2rem",
    maxWidth: "1200px",
  },
  wrapper: {
    position: "relative",
    zIndex: 1000,
  },
  card: {
    backgroundColor: "rgba(255, 255, 255, 0.8)",
    padding: "2rem",
    borderRadius: "1rem",
    maxHeight: "80vh",
    boxShadow:
      "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)",
    ["@media (min-width: 640px)"]: {
      maxWidth: "60vw",
    },
    ["@media (min-width: 768px)"]: {
      maxWidth: "30vw",
    },
  },
  title: {
    fontSize: "1.25rem",
    lineHeight: "1.75rem",
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: "0.025em",
  },
  subtitle: {
    fontSize: "1.125rem",
    lineHeight: "1.75rem",
    fontWeight: 700,
  },
  subtitleCaps: {
    fontSize: "1.125rem",
    lineHeight: "1.75rem",
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: "0.025em",
  },
  sectionHeader: {
    paddingBottom: "0.5rem",
  },
  entriesContainer: {
    maxHeight: "30vh",
    overflowY: "auto",
  },
  entryWrapper: {
    fontSize: "0.875rem",
    lineHeight: "1.25rem",
  },
  divider: {
    margin: "1rem 0.5rem",
    border: 0,
    borderTop: "1px solid #e5e7eb",
  },
};

const desiredFields = new Set([
  "bin",
  "unit",
  "date_entered",
  "inspection_date",
  "complaint_number",
  "complaint_category",
  "community_board",
]);

export function HUD({
  rawData = {},
  descriptionMap,
  descriptionMap2021,
  priorityMap,
}) {
  const data = rawData?.data ? JSON.parse(rawData?.data) : {};
  const status = rawData?.highestPriority ?? null;
  const address = rawData?.address ?? "";

  const mediaQuery = window.matchMedia("(min-width: 768px)");
  const cardStyle = {
    ...styles.card,
    maxWidth: mediaQuery.matches ? "30vw" : "60vw",
  };

  return (
    <div style={styles.container}>
      <div style={styles.wrapper}>
        <div style={cardStyle}>
          <div>
            <h2 style={styles.title}>
              {address.substring(0, address.length - 6).toLowerCase()}
            </h2>
            <h3 style={styles.subtitle}>
              {address.substring(address.length - 6)}
            </h3>
            {status && (
              <h3 style={styles.subtitleCaps}>Highest Priority: {status}</h3>
            )}
            <h3 style={styles.subtitleCaps}>
              Number of Active Complaints: {rawData.count}
            </h3>
          </div>

          <div style={styles.sectionHeader}>
            <h3 style={styles.subtitleCaps}>Database Entries</h3>
          </div>

          <div style={styles.entriesContainer}>
            {Array.isArray(data) &&
              data.map((item, i) => (
                <div key={i}>
                  <div style={styles.entryWrapper}>
                    <p>Entry {i + 1}</p>
                    <FormattedEntry
                      item={item}
                      desiredFields={desiredFields}
                      descriptionMap={descriptionMap}
                      descriptionMap2021={descriptionMap2021}
                      priorityMap={priorityMap}
                    />
                    <p>Details for {item.complaint_number || "N/A"}</p>
                  </div>

                  {i !== data.length - 1 && <hr style={styles.divider} />}
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
}
