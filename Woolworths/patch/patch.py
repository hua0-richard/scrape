import pandas as pd
addresses = [
    ['50', "shop 1248/Cnr Park street &, George St, Sydney NSW 2000, Australia"],
    ['51', "Pakington Strand, 95/113 Pakington St, Geelong West VIC 3218, Australia"],
    ['52', "Macarthur Central 259 Queen Street, Brisbane QLD 4000"],
    ['53', "166 Murray St, Perth WA 6000, Australia"]
]

def extract_city_region(address):
    known_locations = {
        "Sydney": "NSW",
        "Geelong West": "VIC",
        "Brisbane": "QLD",
        "Perth": "WA"
    }
    for city, region in known_locations.items():
        if city in address:
            return [city, region]

    return [None, None]

def patch_images():
    None

def patch_notes():
    None
