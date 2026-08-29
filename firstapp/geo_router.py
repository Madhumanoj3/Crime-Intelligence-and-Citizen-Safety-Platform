"""
Geographic & Jurisdiction Routing Service.
Routes a complaint to the most appropriate Police Station based on
latitude/longitude distance, pincode, or city/district matching.
"""

import math


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees) in kilometers.
    """
    R = 6371.0  # Earth radius in kilometers
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def find_jurisdiction_station(complaint_lat: str = None, complaint_lon: str = None,
                              city: str = '', pincode: str = '', address: str = '',
                              stations: list = None) -> tuple:
    """
    Finds the best matching Police Station.
    Returns: (station_obj, distance_km or None, match_reason)
    """
    if not stations:
        return (None, None, "No stations registered")

    # Try Coordinate-based Matching
    try:
        if complaint_lat and complaint_lon:
            c_lat = float(str(complaint_lat).strip())
            c_lon = float(str(complaint_lon).strip())

            best_station = None
            min_dist = float('inf')

            for st in stations:
                st_lat_raw = getattr(st, 'latitude', None) or (st.get('latitude') if isinstance(st, dict) else None)
                st_lon_raw = getattr(st, 'longitude', None) or (st.get('longitude') if isinstance(st, dict) else None)

                if st_lat_raw and st_lon_raw:
                    try:
                        s_lat = float(str(st_lat_raw).strip())
                        s_lon = float(str(st_lon_raw).strip())
                        dist = _haversine_distance(c_lat, c_lon, s_lat, s_lon)
                        if dist < min_dist:
                            min_dist = dist
                            best_station = st
                    except (ValueError, TypeError):
                        continue

            if best_station and min_dist < float('inf'):
                return (best_station, round(min_dist, 2), f"Nearest Station ({round(min_dist, 2)} km away)")
    except (ValueError, TypeError):
        pass

    # Try City/District text matching
    query_text = f"{city} {address} {pincode}".lower()
    for st in stations:
        st_name = (getattr(st, 'name', '') or (st.get('name', '') if isinstance(st, dict) else '')).lower()
        st_addr = (getattr(st, 'address', '') or (st.get('address', '') if isinstance(st, dict) else '')).lower()
        st_dist = (getattr(st, 'district', '') or (st.get('district', '') if isinstance(st, dict) else '')).lower()

        if (city and city.lower() in st_name) or (city and city.lower() in st_addr) or (city and city.lower() in st_dist):
            return (st, None, "Matched by City/District Jurisdiction")
        if any(word in query_text for word in st_name.split() if len(word) > 4):
            return (st, None, "Matched by Area / Station Name")

    # Default to first station if no exact match
    return (stations[0], None, "Assigned to Primary District Headquarters")
