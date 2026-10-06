# Cricsheet stores player names in short form (e.g. "V Kohli") with no full-name field.
# This lookup maps well-known international players' short forms to their full names,
# for display purposes only — it does not affect stats or database storage.

FULL_NAME_LOOKUP = {
    # India
    "V Kohli": "Virat Kohli",
    "RG Sharma": "Rohit Sharma",
    "S Dhawan": "Shikhar Dhawan",
    "MS Dhoni": "Mahendra Singh Dhoni",
    "KL Rahul": "Kannaur Lokesh Rahul",
    "SC Ganguly": "Sourav Ganguly",
    "SR Tendulkar": "Sachin Tendulkar",
    "R Dravid": "Rahul Dravid",
    "YK Pathan": "Yusuf Pathan",
    "Yuvraj Singh": "Yuvraj Singh",
    "HH Pandya": "Hardik Pandya",
    "RA Jadeja": "Ravindra Jadeja",
    "JJ Bumrah": "Jasprit Bumrah",
    "Mohammed Shami": "Mohammed Shami",
    "R Ashwin": "Ravichandran Ashwin",
    "AB de Villiers": "AB de Villiers",

    # Australia
    "SR Watson": "Shane Watson",
    "RT Ponting": "Ricky Ponting",
    "MJ Clarke": "Michael Clarke",
    "DA Warner": "David Warner",
    "SPD Smith": "Steve Smith",
    "GJ Maxwell": "Glenn Maxwell",
    "AJ Finch": "Aaron Finch",
    "PJ Cummins": "Pat Cummins",
    "MA Starc": "Mitchell Starc",
    "JP Faulkner": "James Faulkner",
    "MEK Hussey": "Mike Hussey",
    "AC Gilchrist": "Adam Gilchrist",

    # England
    "JE Root": "Joe Root",
    "EJG Morgan": "Eoin Morgan",
    "BA Stokes": "Ben Stokes",
    "JC Buttler": "Jos Buttler",
    "AJ Bell": "Ian Bell",
    "KP Pietersen": "Kevin Pietersen",
    "AN Cook": "Alastair Cook",
    "JM Anderson": "James Anderson",
    "MM Ali": "Moeen Ali",
    "JJ Roy": "Jason Roy",

    # Pakistan
    "Babar Azam": "Babar Azam",
    "Mohammad Rizwan": "Mohammad Rizwan",
    "Shaheen Shah Afridi": "Shaheen Shah Afridi",
    "Shahid Afridi": "Shahid Afridi",
    "Younis Khan": "Younis Khan",
    "Misbah-ul-Haq": "Misbah-ul-Haq",
    "Mohammad Hafeez": "Mohammad Hafeez",
    "Wahab Riaz": "Wahab Riaz",
    "Fakhar Zaman": "Fakhar Zaman",

    # South Africa
    "HM Amla": "Hashim Amla",
    "JH Kallis": "Jacques Kallis",
    "F du Plessis": "Faf du Plessis",
    "Q de Kock": "Quinton de Kock",
    "DA Miller": "David Miller",
    "KA Rabada": "Kagiso Rabada",

    # New Zealand
    "KS Williamson": "Kane Williamson",
    "BJ McCullum": "Brendon McCullum",
    "MJ Guptill": "Martin Guptill",
    "TWM Latham": "Tom Latham",
    "TG Southee": "Tim Southee",
    "TA Boult": "Trent Boult",

    # Sri Lanka
    "KC Sangakkara": "Kumar Sangakkara",
    "DPMD Jayawardene": "Mahela Jayawardene",
    "TM Dilshan": "Tillakaratne Dilshan",
    "SL Malinga": "Lasith Malinga",
    "AD Mathews": "Angelo Mathews",
    "WU Tharanga": "Upul Tharanga",

    # West Indies
    "CH Gayle": "Chris Gayle",
    "DM Bravo": "Darren Bravo",
    "DJ Bravo": "Dwayne Bravo",
    "SO Hope": "Shai Hope",
    "N Pooran": "Nicholas Pooran",
    "JO Holder": "Jason Holder",

    # Bangladesh
    "Shakib Al Hasan": "Shakib Al Hasan",
    "Tamim Iqbal": "Tamim Iqbal",
    "Mushfiqur Rahim": "Mushfiqur Rahim",
    "Mahmudullah": "Mahmudullah",
    "Mustafizur Rahman": "Mustafizur Rahman",

    # Afghanistan
    "Rashid Khan": "Rashid Khan",
    "Mohammad Nabi": "Mohammad Nabi",

    # Zimbabwe
    "BRM Taylor": "Brendan Taylor",
    "H Masakadza": "Hamilton Masakadza",
}


def get_display_name(short_name: str) -> str:
    """Return the full name if known, otherwise the original short name."""
    return FULL_NAME_LOOKUP.get(short_name, short_name)
