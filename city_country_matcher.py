import sys
from geopy.geocoders import Nominatim

def fetch_cities_and_countries(query):
    """
    Fetches the list of cities and their corresponding countries using Nominatim API.

    Parameters:
        query (str): Query to search for cities.

    Returns:
        list: A list of tuples containing city names and their corresponding countries.
    """
    geolocator = Nominatim(user_agent="your_app_name")
    location = geolocator.geocode(query, exactly_one=False, addressdetails=True)

    cities_and_countries = []
    if location:
        for place in location:
            city = place.raw.get('display_name', 'N/A').split(',')[0].strip()
            country = place.raw.get('address', {}).get('country', 'N/A')
            cities_and_countries.append((city, country))
    return cities_and_countries

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python city_country_matcher.py <query>")
        sys.exit(1)

    query = sys.argv[1]
    cities_and_countries = fetch_cities_and_countries(query)
    for city, country in cities_and_countries:
        print(f"City: {city}, Country: {country}")
