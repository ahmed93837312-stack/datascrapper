import sys, os
sys.path.insert(0, '.')
os.environ['GOOGLE_MAPS_MAX_RESULTS'] = '5'
from scrapers.google_maps_scraper import GoogleMapsScraper

scraper = GoogleMapsScraper()
scraper.max_results = 5
results = scraper.run(location='Dubai', niche='gyms')
print(f'--- RESULTS ({len(results)}) ---')
for r in results:
    print(f"  Name:    {r['Business Name']}")
    print(f"  Phone:   {r['Phone Number']}")
    print(f"  Address: {r['Full Address']}")
    print(f"  Rating:  {r['Rating']} ({r['Reviews']} reviews)")
    print(f"  Website: {r['Website URL']}")
    print(f"  Email:   {r['Email']}")
    print()
