import os
import csv
import requests
from bs4 import BeautifulSoup

def scrape_intersections():
    url = "https://www.tmt.or.jp/research/index10_5.html"
    os.makedirs("data/raw", exist_ok=True)
    output_path = "data/raw/intersections.csv"
    
    # フィルタ用の緯度経度範囲
    min_lat, max_lat = 39.70151, 39.72087
    min_lon, max_lon = 140.10277, 140.11950
    
    print(f"Fetching intersections from {url}...")
    try:
        response = requests.get(url, timeout=30)
        # Webページのエンコーディングを自動検出または設定
        response.encoding = 'utf-8'
        html = response.text
    except Exception as e:
        print(f"Network request failed: {e}. Trying to check local environment...")
        return
        
    soup = BeautifulSoup(html, 'html.parser')
    select_elem = soup.find('select', class_='intersection_id')
    
    if not select_elem:
        print("Could not find 'intersection_id' select element in the HTML.")
        return
        
    options = select_elem.find_all('option')
    
    intersections = []
    for opt in options:
        val = opt.get('value')
        lon_str = opt.get('lon')
        lat_str = opt.get('lat')
        num_str = opt.text.strip()
        
        if not val or not lon_str or not lat_str:
            continue
            
        try:
            lon = float(lon_str)
            lat = float(lat_str)
            
            # 対象範囲内か判定
            in_range = (min_lat <= lat <= max_lat) and (min_lon <= lon <= max_lon)
            
            intersections.append({
                'intersection_id': val,
                'intersection_number': num_str,
                'lat': lat,
                'lon': lon,
                'in_range': 1 if in_range else 0
            })
        except ValueError:
            continue
            
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['intersection_id', 'intersection_number', 'lat', 'lon', 'in_range'])
        writer.writeheader()
        writer.writerows(intersections)
        
    in_range_count = sum(1 for item in intersections if item['in_range'] == 1)
    print(f"Scraped {len(intersections)} intersections total. {in_range_count} are in the target range.")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    scrape_intersections()
