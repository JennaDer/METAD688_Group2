# MET AD 688 Group 2

## Career Evaluation Project

This project examines Data Analytics career opportunities within Computer Systems Design and Related Services.

- **Industry:** Computer Systems Design and Related Services
- **NAICS code:** 5415
- **Career pathway:** Data Analytics
- **Course:** MET AD 688

## Dataset

The source is the MET CareerCompass 2026 v2 job-postings extract provided for the course. It contains 21 Parquet files with 504,208 job postings and 124 variables.

The analytical panel keeps the analytics-related postings in NAICS 5415 from the most recent 12 months. The counts at each filtering step are recorded in `data/processed/panel_build_stats.json`.

### Changes to the data

- The project originally focused on Pharmaceutical and Medicine Manufacturing under NAICS 3254. The team changed the industry scope after finding too few relevant analytics postings for a useful market analysis.
- Module 2 used the original extract of 17 Parquet files and 165,386 postings. In Module 3 the panel was rebuilt on the corrected v2 extract, which restores skill names the original had cut off and adds experience data.

## Shared Processed Data

The cleaned dataset is stored at:

`data/processed/career_market_panel.csv`

This file is committed to the repository so team members can render the website and complete later analysis without downloading the full raw dataset.

The counts recorded while building it are stored at:

`data/processed/panel_build_stats.json`

The related data dictionary is stored at:

`data/processed/career_market_data_dictionary.csv`

## Rebuilding the Dataset

The raw Parquet files are not stored in GitHub because of their size.

To rebuild the cleaned dataset, place the 21 Parquet files of the v2 extract in:

`data/MET_CareerCompass_2026_v2/`

This folder is listed in `.gitignore`, so the raw files cannot be committed by accident.

Then run:

```bash
python scripts/build_panel.py
```

The script writes the panel and the stats file. Every number on the Data Preparation page is read from those two files.
