# METAD688_Group2
MET AD 688 Group 2 - Group Project

## Step 2 Data Setup

The Step 2 analysis uses the MET CareerCompass 2026 job-postings dataset provided for the course.

The raw dataset contains 17 Parquet files and should **not** be committed to GitHub. The files can be downloaded from the course-provided [Google Drive folder](https://drive.google.com/drive/folders/11uTPfwHiRohl2ljSYeFuo0KKBUP_1vk4?usp=sharing).

Each team member who needs to reproduce the analysis should download the 17 Parquet files and place them in:

`data/MET_CareerCompass_2026/`

The Step 2 analysis script is `mariam_step2_analysis.py`. It filters the Pharmaceutical and Medicine Manufacturing industry (NAICS 3254) and identifies analytics-related postings for the market-baseline analysis.
