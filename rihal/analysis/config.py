from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Paths:
    workbook: str = r"c:\Users\musafa\OneDrive\Desktop\rihal\MOH_health_units_data.xlsx"
    outputs_dir: str = r"c:\Users\musafa\OneDrive\Desktop\rihal\outputs"
    tables_dir: str = r"c:\Users\musafa\OneDrive\Desktop\rihal\outputs\tables"
    figures_dir: str = r"c:\Users\musafa\OneDrive\Desktop\rihal\outputs\figures"


PATHS = Paths()


SHEETS = {
    "population": "Muscat Population",
    "male_female": "Muscat_male_female",
    "omani_expat": "Muscat_omani_expart",
    "hh_size": "Average_Household_Size",
    "moh_beds_manpower": "muscat_moh_beds_manpower",
    "private_clinics": "muscat_private_clinics",
    "moh_units": "MOH Health Units Data",
    "electricity": "Electricity consumption ",
    "gov_dist": "Oman population distribution",
}

