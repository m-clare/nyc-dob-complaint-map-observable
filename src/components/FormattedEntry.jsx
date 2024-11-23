const styles = {
  keyStyle: {
    display: "inline",
    fontWeight: 700,
    textTransform: "uppercase",
    fontSize: "0.875rem",
    letterSpacing: "0.02857em",
    fontFamily: '"Roboto","Helvetica","Arial",sans-serif',
  },
  valueStyle: {
    display: "inline",
    fontSize: "0.875rem",
    fontFamily: '"Roboto","Helvetica","Arial",sans-serif',
  },
  entryContainer: {
    marginBottom: "0.5rem",
  },
};

export const FormattedEntry = ({
  item,
  desiredFields,
  descriptionMap,
  descriptionMap2021,
  priorityMap,
}) => {
  return (
    <>
      {Object.entries(item).map(([key, value], i) => {
        const formattedKey = key.split("_").join(" ");

        if (desiredFields.has(key) && key === "complaint_category") {
          return (
            <div key={key} style={styles.entryContainer}>
              <div>
                <span style={styles.keyStyle}>{formattedKey}:</span>
                <span> </span>
                <span style={styles.valueStyle}>
                  {descriptionMap.has(value)
                    ? descriptionMap.get(value)
                    : descriptionMap2021.has(value)
                    ? descriptionMap2021.get(value)
                    : value}
                </span>
              </div>
              <div>
                <span style={styles.keyStyle}>Priority:</span>
                <span> </span>
                <span style={styles.valueStyle}>
                  {priorityMap.get(value) ??
                    "Unknown Priority (category post-2021)"}
                </span>
              </div>
            </div>
          );
        } else if (desiredFields.has(key)) {
          return (
            <div key={key} style={styles.entryContainer}>
              <div>
                <span style={styles.keyStyle}>{formattedKey}:</span>
                <span> </span>
                <span style={styles.valueStyle}>{value}</span>
              </div>
            </div>
          );
        }
        return null; // Skip fields not in desiredFields
      })}
    </>
  );
};

export default FormattedEntry;
