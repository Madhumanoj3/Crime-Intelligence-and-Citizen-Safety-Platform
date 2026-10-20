"""
Reference coordinates for Tamil Nadu localities used by the SYNTHETIC dataset
generator (generate_datasets.py) and validator (validate_datasets.py).

Coordinates are approximate public map positions of well-known landmarks and
neighbourhoods. They are used only as anchor points for synthetic data.
"""

# Crime-type mixes by kind of place (weights, not percentages).
PROFILES = {
    'transit': {'Theft': 30, 'Chain Snatching': 18, 'Vehicle Theft': 20, 'Robbery': 10,
                'Assault': 8, 'Vandalism': 7, 'Burglary': 2, 'Cyber Crime': 3},
    'market': {'Theft': 35, 'Chain Snatching': 18, 'Robbery': 12, 'Vehicle Theft': 12,
               'Assault': 8, 'Vandalism': 8, 'Burglary': 4, 'Cyber Crime': 3},
    'temple': {'Theft': 32, 'Chain Snatching': 30, 'Vehicle Theft': 12, 'Robbery': 8,
               'Vandalism': 5, 'Assault': 5, 'Burglary': 5, 'Cyber Crime': 3},
    'residential': {'Burglary': 35, 'Vehicle Theft': 15, 'Chain Snatching': 15, 'Theft': 8,
                    'Vandalism': 10, 'Cyber Crime': 10, 'Assault': 5, 'Robbery': 2},
    'it_hub': {'Cyber Crime': 35, 'Vehicle Theft': 15, 'Theft': 15, 'Robbery': 8,
               'Chain Snatching': 8, 'Burglary': 8, 'Assault': 5, 'Vandalism': 6},
    'town': {'Theft': 18, 'Burglary': 18, 'Vehicle Theft': 15, 'Chain Snatching': 12,
             'Assault': 12, 'Vandalism': 10, 'Robbery': 8, 'Cyber Crime': 7},
}

# name, city, lat, lon, profile, hotspot_weight (0 = not a hotspot), spread (deg), max_lon
# max_lon keeps points around coastal Chennai localities on land.
LOCALITIES = [
    # Chennai
    ('T. Nagar', 'Chennai', 13.0418, 80.2341, 'market', 9, 0.0035, None),
    ('Chennai Central', 'Chennai', 13.0827, 80.2757, 'transit', 8, 0.0030, 80.2850),
    ('Koyambedu', 'Chennai', 13.0694, 80.1948, 'transit', 8, 0.0035, None),
    ('Velachery', 'Chennai', 12.9815, 80.2180, 'it_hub', 7, 0.0035, None),
    ('Mylapore', 'Chennai', 13.0339, 80.2619, 'temple', 5, 0.0030, 80.2720),
    ('Tambaram', 'Chennai', 12.9249, 80.1000, 'transit', 5, 0.0035, None),
    ('Guindy', 'Chennai', 13.0067, 80.2206, 'it_hub', 0, 0.0035, None),
    ('Egmore', 'Chennai', 13.0732, 80.2609, 'transit', 0, 0.0030, 80.2720),
    ('Adyar', 'Chennai', 13.0012, 80.2565, 'residential', 0, 0.0030, 80.2650),
    ('Anna Nagar', 'Chennai', 13.0850, 80.2101, 'residential', 0, 0.0035, None),
    ('Vadapalani', 'Chennai', 13.0500, 80.2121, 'temple', 0, 0.0030, None),
    # Madurai (project's home district - densest coverage)
    ('Periyar Bus Stand', 'Madurai', 9.9166, 78.1119, 'transit', 11, 0.0022, None),
    ('Meenakshi Amman Temple', 'Madurai', 9.9195, 78.1193, 'temple', 10, 0.0022, None),
    ('Mattuthavani', 'Madurai', 9.9459, 78.1566, 'transit', 9, 0.0030, None),
    ('Arapalayam', 'Madurai', 9.9331, 78.1017, 'transit', 6, 0.0025, None),
    ('Anna Nagar', 'Madurai', 9.9400, 78.1310, 'residential', 6, 0.0028, None),
    ('Thiruparankundram', 'Madurai', 9.8790, 78.0715, 'temple', 4, 0.0028, None),
    ('Goripalayam', 'Madurai', 9.9295, 78.1270, 'market', 0, 0.0025, None),
    ('K. Pudur', 'Madurai', 9.9530, 78.1420, 'residential', 0, 0.0030, None),
    ('Koodal Nagar', 'Madurai', 9.8810, 78.1010, 'residential', 0, 0.0030, None),
    # Coimbatore
    ('Gandhipuram', 'Coimbatore', 11.0168, 76.9674, 'transit', 8, 0.0035, None),
    ('Ukkadam', 'Coimbatore', 10.9905, 76.9610, 'market', 5, 0.0030, None),
    ('Peelamedu', 'Coimbatore', 11.0254, 77.0028, 'it_hub', 5, 0.0035, None),
    ('R.S. Puram', 'Coimbatore', 11.0080, 76.9500, 'residential', 0, 0.0030, None),
    ('Singanallur', 'Coimbatore', 10.9990, 77.0320, 'transit', 0, 0.0035, None),
    # Tiruchirappalli
    ('Chathiram Bus Stand', 'Tiruchirappalli', 10.8310, 78.6930, 'transit', 6, 0.0030, None),
    ('Srirangam', 'Tiruchirappalli', 10.8627, 78.6897, 'temple', 5, 0.0030, None),
    ('Central Bus Stand', 'Tiruchirappalli', 10.7980, 78.6830, 'transit', 0, 0.0030, None),
    ('Thillai Nagar', 'Tiruchirappalli', 10.8270, 78.6810, 'residential', 0, 0.0025, None),
    # Salem
    ('New Bus Stand', 'Salem', 11.6720, 78.1410, 'transit', 5, 0.0030, None),
    ('Old Bus Stand', 'Salem', 11.6510, 78.1600, 'market', 0, 0.0030, None),
    # Tirunelveli
    ('Tirunelveli Junction', 'Tirunelveli', 8.7270, 77.7080, 'transit', 4, 0.0030, None),
    ('Palayamkottai', 'Tirunelveli', 8.7200, 77.7390, 'residential', 0, 0.0030, None),
    # Other urban centres
    ('Bus Stand', 'Sivakasi', 9.4530, 77.8010, 'market', 4, 0.0025, None),
    ('Katpadi', 'Vellore', 12.9716, 79.1370, 'transit', 3, 0.0030, None),
    ('Vellore Fort', 'Vellore', 12.9202, 79.1290, 'market', 0, 0.0025, None),
    ('Central Bus Stand', 'Erode', 11.3410, 77.7170, 'transit', 4, 0.0030, None),
    ('Old Bus Stand', 'Tiruppur', 11.1085, 77.3411, 'market', 4, 0.0030, None),
    ('Old Bus Stand', 'Thanjavur', 10.7870, 79.1380, 'transit', 0, 0.0030, None),
]

# Smaller towns: sparse, low-density background incidents (not hotspots).
TOWNS = [
    ('Dindigul', 10.3673, 77.9803),
    ('Karur', 10.9601, 78.0766),
    ('Hosur', 12.7409, 77.8253),
    ('Kanchipuram', 12.8342, 79.7036),
    ('Kumbakonam', 10.9617, 79.3881),
    ('Namakkal', 11.2189, 78.1674),
    ('Virudhunagar', 9.5850, 77.9579),
    ('Pollachi', 10.6583, 77.0085),
    ('Krishnagiri', 12.5186, 78.2137),
    ('Villupuram', 11.9401, 79.4861),
]

# Rough bounding box of Tamil Nadu (mainland).
TN_BOUNDS = {'lat_min': 8.0, 'lat_max': 13.6, 'lon_min': 76.2, 'lon_max': 80.35}

HOTSPOT_CRIME_TYPES = ['Theft', 'Robbery', 'Burglary', 'Assault', 'Vehicle Theft',
                       'Chain Snatching', 'Vandalism', 'Cyber Crime']
COMPLAINT_CRIME_TYPES = HOTSPOT_CRIME_TYPES + ['Missing Person']


def location_label(name, city):
    return name if name == city else f"{name}, {city}"


def anchor_lookup():
    """Map 'Name, City' -> (lat, lon) for every locality and town."""
    table = {location_label(n, c): (lat, lon) for n, c, lat, lon, *_ in LOCALITIES}
    table.update({location_label(n, n): (lat, lon) for n, lat, lon in TOWNS})
    return table
