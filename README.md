# MET AD 688 Group 2

## Career Evaluation Project

This project examines Data Analytics career opportunities within Computer Systems Design and Related Services.

- **Industry:** Computer Systems Design and Related Services
- **NAICS code:** 5415
- **Career pathway:** Data Analytics
- **Course:** MET AD 688

## Module 2 Dataset

The source is the MET CareerCompass 2026 job-postings dataset provided for the course. It contains 17 Parquet files with 165,386 job postings.

The original project focused on Pharmaceutical and Medicine Manufacturing under NAICS 3254. The team changed the industry scope after finding too few relevant analytics postings for a useful market analysis.

The final Module 2 dataset contains 287 analytics-related postings within NAICS 5415.

## Shared Processed Data

The cleaned dataset is stored at:

`data/processed/career_market_panel.csv`

This file is committed to the repository so team members can render the website and complete later analysis without downloading the full raw dataset.

The related data dictionary is stored at:

`data/processed/career_market_data_dictionary.csv`

## Rebuilding the Dataset

The raw Parquet files are not stored in GitHub because of their size.

To rebuild the cleaned dataset, place the 17 Parquet files in:

`data/MET_CareerCompass_2026/`

Then run:

```bash
python scripts/build_panel.py