#!/usr/bin/env python3
import requests
import os
import json
from dotenv import load_dotenv
import pandas as pd
import re
from io import StringIO
import aiohttp
import asyncio
import math
import numpy as np
from datetime import datetime
import sys

load_dotenv()

__author__ = "Maryanne Wachter"
__contact__ = "mwachter@utsv.net"
__version__ = "0.0.1"

# Download the raw data - only open complaints

app_token = os.getenv("APP_TOKEN")


def clean_string(x):
    if isinstance(x, str):
        return re.sub(r"\s+", " ", x.strip())
    return x


def get_raw_active_results(app_token=None):

    url = "https://data.cityofnewyork.us/resource/eabe-havv.json?status=ACTIVE&$limit=1000000"

    headers = {"X-App-Token": app_token}

    response = requests.request("GET", url, headers=headers)

    if response.status_code == 200:
        try:
            results = response.json()
            complaint_df = pd.DataFrame(results)
            complaint_df = complaint_df.replace({np.nan: None})
            complaint_df["address_string"] = complaint_df.apply(
                lambda x: f'{x["house_number"]} {x["house_street"]}, , New York, {x["zip_code"]}',
                axis=1,
            )
            return complaint_df
        except Exception as e:
            print(f"Error loading complaint results into data frame: {str(e)}")
            raise
    else:
        print(f"Error in API request: Status code {response.status_code}")
        return None


def find_missing_entries(source_df, reference_df, column_name="address_string"):
    """
    Find values from source DataFrame that don't appear in reference DataFrame.

    Parameters:
    source_df (pandas.DataFrame): DataFrame containing values to check
    reference_df (pandas.DataFrame): DataFrame to search in
    column_name (str): Name of the column containing values

    Returns:
    list: Values from source_df that don't appear in reference_df
    """

    source_df["address_string"] = source_df["address_string"].apply(clean_string)
    reference_df["address_string"] = reference_df["address_string"].apply(clean_string)
    source_addresses = source_df[column_name].str.lower()
    reference_addresses = reference_df[column_name].str.lower()

    missing_mask = ~source_addresses.isin(reference_addresses)
    missing_addresses = source_df.loc[missing_mask, column_name].tolist()

    return missing_addresses


def parse_with_pandas(response_content):
    # Decode bytes to string
    csv_string = response_content.decode("utf-8")

    # Read CSV string into DataFrame
    df = pd.read_csv(
        StringIO(csv_string),
        header=None,
        names=GEOCODER_COLUMNS,
        converters={col: clean_string for col in GEOCODER_COLUMNS},
    )
    return df


async def process_chunk(chunk, session, chunk_index):
    # Prepare the chunk data
    numbered_strings = [
        f"{i + (chunk_index * 8000)},{value}" for i, value in enumerate(chunk)
    ]
    data_string = "\n".join(numbered_strings)

    # Prepare the form data
    data = aiohttp.FormData()
    data.add_field(
        "addressFile",
        StringIO(data_string),
        filename="chunk_{}.csv".format(chunk_index),
        content_type="text/csv",
    )
    data.add_field("benchmark", "2020")

    try:
        async with session.post(
            "https://geocoding.geo.census.gov/geocoder/locations/addressbatch",
            data=data,
        ) as response:
            if response.status == 200:
                return await response.read(), chunk_index
            else:
                print(f"Error with chunk {chunk_index}: Status {response.status}")
                return None, chunk_index
    except Exception as e:
        print(f"Exception processing chunk {chunk_index}: {str(e)}")
        return None, chunk_index


async def process_all_chunks(missing_strings):
    max_chunk_size = 10000
    total_items = len(missing_strings)

    # Calculate optimal number of chunks while respecting max size
    num_chunks = max(1, (total_items + max_chunk_size - 1) // max_chunk_size)
    base_chunk_size = total_items // num_chunks
    remainder = total_items % num_chunks

    chunks = []
    start = 0

    for i in range(num_chunks):
        current_chunk_size = base_chunk_size + (1 if i < remainder else 0)
        end = start + current_chunk_size
        chunks.append(missing_strings[start:end])
        start = end

    # Create TCP connector with limits
    connector = aiohttp.TCPConnector(limit=10)  # Limit concurrent connections

    async with aiohttp.ClientSession(connector=connector) as session:
        # Create tasks for each chunk
        tasks = [process_chunk(chunk, session, i) for i, chunk in enumerate(chunks)]

        # Process chunks with progress tracking
        results = []
        for completed in asyncio.as_completed(tasks):
            result, chunk_index = await completed
            if result is not None:
                results.append((result, chunk_index))

    # Sort results by chunk index to maintain order
    results.sort(key=lambda x: x[1])
    return [r[0] for r in results]


def process_dob_complaints(csv_path, complaints_categories_path):
    """
    Process DOB complaints data from CSV, grouping by ID and calculating priorities

    Args:
        csv_path: Path to the main DOB complaints CSV file
        complaints_categories_path: Path to the complaints categories JSON file

    Expected CSV columns:
    - id: Unique identifier for each complaint
    - address_string: Location address
    - coordinates: Lat/Long as splittable string
    - complaint_category: Category code of the complaint

    Returns:
        DataFrame containing processed and grouped complaints data
    """
    PRIORITY_ORDER = {
        "A": 0,
        "B": 1,
        "C": 2,
        "D": 3,
    }

    # Read the CSV file
    df = pd.read_csv(csv_path).replace({pd.NA: None, pd.NaT: None, np.nan: None})
    date = csv_path.split("_")[0]

    # Read the complaints categories JSON
    with open(complaints_categories_path, "r") as f:
        complaint_categories = json.load(f)

    # Create priority mapping dictionary
    priority_map = {d["CODE"]: d["PRIORITY"] for d in complaint_categories}

    # Create geometry for each row
    df["geometry"] = df.apply(
        lambda row: {
            "type": "Point",
            "coordinates": [
                float(row["coordinates"].split(",")[0]),
                float(row["coordinates"].split(",")[1]),
            ],
        },
        axis=1,
    )

    # Add priority based on complaint category
    df["priority"] = df["complaint_category"].map(priority_map)

    # Identify columns that will go into properties
    # Exclude columns that are used for geojson
    excluded_cols = ["id", "geometry", "coordinates", ""]
    property_cols = [col for col in df.columns if col not in excluded_cols]

    # Create a DataFrame with the counts
    counts = df.groupby("bin").size().to_dict()

    def convert_to_dict_records(df_subset):
        records = df_subset.replace({pd.NA: None, pd.NaT: None, np.nan: None}).to_dict(
            "records"
        )
        return [
            {k: (None if pd.isna(v) else v) for k, v in record.items()}
            for record in records
        ]

    # Group and aggregate other fields
    grouped_data = {}
    for bin_id, group in df.groupby("bin"):
        grouped_data[bin_id] = {
            "type": "Feature",
            "geometry": group["geometry"].iloc[0],
            "properties": {
                "count": counts[bin_id],
                "address": group["geocoder_matched_address_string"].iloc[0],
                "complaintCategories": list({*group["complaint_category"].tolist()}),
                "highestPriority": (
                    sorted(
                        [x for x in group["priority"].tolist() if pd.notna(x)],
                        key=lambda p: PRIORITY_ORDER.get(p, 999),
                    )[0]
                    if any(pd.notna(x) for x in group["priority"])
                    else None
                ),
                "data": convert_to_dict_records(group[property_cols]),
            },
        }

    # Convert to list and sort by count
    result = list(grouped_data.values())
    result.sort(key=lambda x: x["properties"]["count"], reverse=True)

    # Save to JSON file
    with open(f"{date}_nycdob_rollup.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)

    return pd.DataFrame(result)


# Process all chunks
async def get_results(original_address_df, complaint_df):
    GEOCODER_COLUMNS = [
        "ID",
        "address_string",
        "match_status",
        "match_type",
        "geocoder_matched_address_string",
        "coordinates",
        "parcel_number",
        "side",
    ]

    missing_addresses = find_missing_entries(
        complaint_df, original_address_df, column_name="address_string"
    )
    address_set = list({*missing_addresses})
    results = await process_all_chunks(address_set)

    all_df = pd.DataFrame()
    for result in results:
        # Parse each chunk's CSV content
        chunk_df = pd.read_csv(
            StringIO(result.decode("utf-8")),
            header=None,
            names=GEOCODER_COLUMNS,
            converters={col: clean_string for col in GEOCODER_COLUMNS},
        )
        # Append to main DataFrame
        all_df = pd.concat([all_df, chunk_df], ignore_index=True)

    # filter results to only matches
    matched_df = all_df[all_df.match_status.isin(["Match"])]
    reduced_df = matched_df.drop(columns=["ID", "match_status", "match_type", "side"])
    address_df = pd.concat([original_address_df, reduced_df])
    address_df_unique = address_df.drop_duplicates(subset="address_string")

    # rewrite address_df_unique to csv to add new entries
    address_df_unique.to_csv("geocode_address.csv", index=False)

    complaints_matched = complaint_df.merge(
        address_df_unique, how="inner", on="address_string"
    )

    complaints_merged = complaint_df.merge(
        address_df_unique, how="left", on="address_string"
    )

    return [complaints_merged, complaints_matched]


df = pd.read_csv("geocode_address.csv")
complaint_df = get_raw_active_results(app_token)
[all_complaints_df, geomatched_df] = asyncio.run(get_results(df, complaint_df))


if __name__ == "__main__":
    app_token = os.getenv("APP_TOKEN")
    if not app_token:
        print("Error: APP_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    try:
        df = pd.read_csv("geocode_address.csv")
        # Get the complaints data
        complaint_df = get_raw_active_results(app_token)
        [all_complaints, geomatched_df] = asyncio.run(get_results(df, complaint_df))
        current_date = datetime.now().strftime("%Y-%m-%d")
        # output matched complaints for record
        output_name = f"{current_date}_matched-complaints.csv"
        geomatched_df.to_csv(output_name, index=False)

        # output required json for tippecanoe
        process_dob_complaints(
            output_name, "../assets/dobcomplaints_complaint_category.json"
        )

        # output for data loader
        if complaint_df is not None:
            # Output to stdout as CSV
            complaint_df.to_csv(sys.stdout, index=False)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
