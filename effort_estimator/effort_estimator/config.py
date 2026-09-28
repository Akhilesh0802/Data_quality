"""
config.py
---------
All estimate data lives here. Each entry in ESTIMATORS becomes one tab in the app.
To add / change a tab, edit only this file - calculator and UI are generic.

Structure of an estimator:
  tab        : tab caption
  title      : title used in summary / CSV
  mode       : optional mode of delivery label (shown on the tab)
  sample_note: optional banner text (e.g. when numbers are placeholders)
  scopes     : volume dropdowns -> multiplier factor
  matrix     : activities -> complexity levels -> base hours
               "scope" says which multiplier applies to that activity
               OR "hours_by_band": hours picked directly from the scope dropdown
               (used with a scope marked "direct": True)
"""

APP_TITLE = "Effort Estimation Calculator"
COMPANY_NAME = "Grant Thornton Bharat LLP"
HOURS_PER_DAY = 8

# Every block of 10 adds 1 to the multiplier
TEN_BANDS = {"Upto 10": 1, "11 - 20": 2, "21 - 30": 3, "31 - 40": 4, "41 - 50": 5}

# Every block of 5 adds 1 to the multiplier
FIVE_BANDS = {"Upto 5": 1, "6 - 10": 2, "11 - 15": 3, "16 - 20": 4}

# Dashboard page count: 1-5 pages all fall in the old "Upto 5" band -> multiplier 1
# for DAX / Visual. Page hours themselves come from hours_by_band.
PAGE_COUNT = {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1}

ESTIMATORS = {
    # ------------------------------------------------------------------ TAB 1
    "data": {
        "tab": "Data & KPIs",
        "title": "Data Processing & KPI Estimate",
        "mode": "CI 1.0",
        "scopes": {
            "files": {"label": "Number of files to be analysed",
                      "subtitle": "Applies to data activities",
                      "unit": "files", "base_qty": 10, "bands": TEN_BANDS},
            "kpis": {"label": "Number of KPIs to be delivered",
                     "subtitle": "Applies to KPI build",
                     "unit": "KPIs", "base_qty": 10, "bands": TEN_BANDS},
        },
        "matrix": {
            "sanity": {"label": "Quality of the Data", "scope": "files",
                       "levels": {"Good": 1, "Average": 2, "Poor": 3}},
            "cleansing": {"label": "Level of Data Cleansing", "scope": "files",
                          "levels": {"Basic": 2, "Intermediate": 3, "Advanced": 4}},
            "ingestion": {"label": "Level of Data Transformation for Ingestion", "scope": "files",
                          "levels": {"Basic": 1, "Intermediate": 2, "Advanced": 5}},
            "kpis": {"label": "Average complexity of KPIs", "scope": "kpis",
                     "levels": {"Basic": 4, "Moderate": 8, "Complex": 12}},
        },
    },

    # ------------------------------------------------------------------ TAB 2
    # Report pages: hours picked directly from page count (1 = 3 h, 2 = 5 h, +2 h per page).
    # Modelling / DAX / Visual hours are SAMPLE values - replace with actual matrix.
    "dashboard": {
        "tab": "Power BI Dashboard",
        "title": "Power BI Dashboard Estimate",
        "scopes": {
            "pages": {"label": "Number of report pages",
                      "subtitle": "Page effort taken directly from count",
                      "unit": "pages", "unit_singular": "page", "base_qty": 5,
                      "direct": True, "bands": PAGE_COUNT},
            "sources": {"label": "Number of data sources",
                        "subtitle": "Applies to data modelling",
                        "unit": "sources", "base_qty": 5, "bands": FIVE_BANDS},
        },
        "matrix": {
            "pages": {"label": "Report Page Development", "scope": "pages",
                      "hours_by_band": {"1": 3, "2": 5, "3": 7, "4": 9, "5": 11}},
            "model": {"label": "Data Modelling & Power Query", "scope": "sources",
                      "levels": {"Basic": 2, "Intermediate": 4, "Advanced": 8}},
            "dax": {"label": "DAX Measures", "scope": "pages",
                    "levels": {"Basic": 2, "Intermediate": 5, "Advanced": 10}},
            "visuals": {"label": "Visual Design & Layout", "scope": "pages",
                        "levels": {"Standard": 2, "Custom": 4, "Advanced": 6}},
        },
    },
}


# ---------------------------------------------------------------- Excel export
CI_RESOURCES = [
    "Anchal Mutneja",
    "Avinash Singh",
    "Dawood Khan",
    "Isha Rawat",
    "Ishita Garg",
    "Kashish Narang",
    "Pallavi Chaudhari",
    "Rahul Tiwary",
    "Swati Awasthi",
    "Akhilesh Kumar",
]
MAX_RESOURCES = 3

DEFAULT_ASSUMPTION = (
    "Assuming the files are provided in the proper format and all required data is "
    "available. Any delay in receiving complete/accurate files may impact the delivery timeline."
)

EXCEL_HEADERS = [
    "Entity Name",
    "Estimated number of hours",
    "Tentative delivery date",
    "Assigned CI resource name",
    "Key assumptions and any data dependencies or risks",
]
