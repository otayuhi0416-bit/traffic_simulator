import os
import requests

def download_osm():
    # 緯度経度のバウンディングボックス (min_lon, min_lat, max_lon, max_lat)
    # ユーザー指定範囲: (39.70151, 140.10277) から (39.72087, 140.11950)
    bbox = "140.10277,39.70151,140.11950,39.72087"
    url = f"https://overpass-api.de/api/map?bbox={bbox}"
    
    # 保存先ディレクトリの作成
    os.makedirs("data/raw", exist_ok=True)
    output_path = "data/raw/akita_center.osm"
    
    print(f"Downloading OSM data for bbox {bbox}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=60)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"OSM data successfully downloaded to {output_path}")
        else:
            print(f"Failed to download OSM data. Status code: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"An error occurred during download: {e}")

if __name__ == "__main__":
    download_osm()
