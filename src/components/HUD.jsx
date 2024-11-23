import { FormattedEntry } from "./FormattedEntry.js";
const styles = {
  container: {
    margin: "1rem",
    padding: "0 1rem",
    maxWidth: "1200px",
    position: "absolute",
    zIndex: 1000,
    pointerEvents: "none",
  },
  wrapper: {
    position: "relative",
    width: "fit-content",
  },
  card: {
    backgroundColor: "rgba(255, 255, 255, 0.8)",
    padding: "1rem",
    borderRadius: "1rem",
    maxHeight: "80vh",
    boxShadow:
      "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)",
    display: "flex",
    flexDirection: "column",
    pointerEvents: "auto", // Enable interactions for the card
    overflow: "hidden", // Prevent content from spilling out
  },
  contentWrapper: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
  },
  entriesContainer: {
    maxHeight: "30vh",
    overflowY: "auto",
    flex: "1 1 auto",
    marginTop: "1rem",
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
  entryWrapper: {
    fontSize: "0.875rem",
    lineHeight: "1.25rem",
  },
  divider: {
    border: 0,
    padding: 0,
    marginY: "0.5rem",
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
  "disposition_date",
  "disposition_code",
]);

export function HUD({
  rawData = {},
  descriptionMap,
  descriptionMap2021,
  priorityMap,
  dispositionMap,
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
          <div style={styles.contentWrapper}>
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
                      <FormattedEntry
                        item={item}
                        desiredFields={desiredFields}
                        descriptionMap={descriptionMap}
                        descriptionMap2021={descriptionMap2021}
                        priorityMap={priorityMap}
                        dispositionMap={dispositionMap}
                      />
                    </div>
                    {i !== data.length - 1 && <hr style={styles.divider} />}
                  </div>
                ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
