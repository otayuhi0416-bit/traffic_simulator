import os
import csv
import json
import math
import sys

# SUMO_HOMEが設定されていない場合のデフォルトを設定
if "SUMO_HOME" not in os.environ:
    os.environ["SUMO_HOME"] = "C:\\Program Files (x86)\\Eclipse\\Sumo"

# sys.path に SUMO の tools を追加（環境変数 SUMO_HOME から）
if "SUMO_HOME" in os.environ:
    sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
try:
    import sumolib
except ImportError:
    print("Warning: sumolib not found in SUMO_HOME/tools. Trying standard import...")
    try:
        import sumolib
    except ImportError:
        print("Error: sumolib is required. Please install sumolib via pip or set SUMO_HOME.")
        sys.exit(1)

def distance_latlon(lat1, lon1, lat2, lon2):
    # 簡易的な2点間距離計算 (メートル)
    R = 6371000  # 地球の半径
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def parse_definition_csv(csv_path):
    # 定義CSVから交差点番号と流入・流出リンクのマッピングをパース
    # 形式: [日付, 情報源コード, 交差点番号, 流入方向数, 流出方向数, 流入1_メッシュ, 流入1_区分, 流入1_リンク, ...]
    mapping = {}
    if not os.path.exists(csv_path):
        print(f"Definition CSV not found: {csv_path}")
        return mapping
        
    print(f"Parsing definition CSV: {csv_path}...")
    with open(csv_path, mode='r', encoding='cp932') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or len(row) < 5:
                continue
            try:
                intersection_num = row[2].strip()
                num_in = int(row[3])
                num_out = int(row[4])
                
                incoming_links = []
                outgoing_links = []
                
                # 流入リンクのパース (最大8個。5列目から3列ずつ)
                for i in range(min(num_in, 8)):
                    idx = 5 + i * 3
                    if idx + 2 < len(row) and row[idx+2]:
                        link_num = row[idx+2].strip()
                        incoming_links.append(link_num)
                        
                # 流出リンクのパース (流入リンクの後のカラム、30列目から3列ずつ)
                for i in range(min(num_out, 8)):
                    idx = 29 + i * 3
                    if idx + 2 < len(row) and row[idx+2]:
                        link_num = row[idx+2].strip()
                        outgoing_links.append(link_num)
                        
                mapping[intersection_num] = {
                    'incoming': incoming_links,
                    'outgoing': outgoing_links
                }
            except Exception as e:
                # パースエラーはスキップ
                continue
    print(f"Parsed {len(mapping)} intersections from definition CSV.")
    return mapping

def match_network():
    net_path = "network/akita.net.xml"
    intersections_csv = "data/raw/intersections.csv"
    definition_csv = "resources/typeC_akita_2026_04/秋田県警_定義_202604.csv"
    output_mapping = "data/match_table.json"
    
    if not os.path.exists(net_path):
        print(f"Error: Network file {net_path} does not exist. Run build_network.py first.")
        sys.exit(1)
    if not os.path.exists(intersections_csv):
        print(f"Error: Intersections CSV {intersections_csv} does not exist. Run scrape_intersections.py first.")
        sys.exit(1)
        
    # 1. 道路網のロード
    print(f"Loading SUMO network: {net_path}...")
    net = sumolib.net.readNet(net_path)
    
    # 2. 交差点位置情報のロード
    intersections_data = []
    with open(intersections_csv, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['in_range'] == '1':
                intersections_data.append({
                    'id': row['intersection_id'],
                    'number': row['intersection_number'],
                    'lat': float(row['lat']),
                    'lon': float(row['lon'])
                })
    print(f"Loaded {len(intersections_data)} target intersections in target range.")
    
    # 3. 信号定義CSVのロード
    def_mapping = parse_definition_csv(definition_csv)
    
    # 4. SUMOの信号付き交差点(Junction)とオープンデータの交差点のマッチング
    matched_data = {}
    sumo_tls_nodes = [node for node in net.getNodes() if node.getType() == "traffic_light"]
    print(f"Found {len(sumo_tls_nodes)} traffic light junctions in SUMO network.")
    
    for intersection in intersections_data:
        num = intersection['number']
        lat = intersection['lat']
        lon = intersection['lon']
        
        # 最も近いSUMOノードを探す
        best_node = None
        best_dist = float('inf')
        
        for node in sumo_tls_nodes:
            # SUMOのXY座標から緯度経度に変換
            x, y = node.getCoord()
            node_lon, node_lat = net.convertXY2LonLat(x, y)
            
            dist = distance_latlon(lat, lon, node_lat, node_lon)
            if dist < best_dist:
                best_dist = dist
                best_node = node
                
        # 距離が近い（例: 70メートル以内）場合のみマッチング
        if best_node and best_dist < 70:
            print(f"Matched Intersection #{num} to SUMO Junction '{best_node.getID()}' (dist: {best_dist:.1f}m)")
            
            # 交差点に接続するエッジの取得
            incoming_edges = [edge.getID() for edge in best_node.getIncoming()]
            outgoing_edges = [edge.getID() for edge in best_node.getOutgoing()]
            
            # 流入・流出リンクの定義（存在すれば）
            links = def_mapping.get(num, {'incoming': [], 'outgoing': []})
            
            # 流入・流出エッジとリンクのマッピングを初期推測（基本的には方角やインデックスで紐付け可能だが、
            # 初期値として単純にリストを紐付けるか、手動修正用のプレースホルダーを作成）
            incoming_map = {}
            for i, link in enumerate(links['incoming']):
                # エッジの数が足りていれば順に割り当てる（簡易推測）、足りなければ空
                incoming_map[link] = incoming_edges[i] if i < len(incoming_edges) else ""
                
            outgoing_map = {}
            for i, link in enumerate(links['outgoing']):
                outgoing_map[link] = outgoing_edges[i] if i < len(outgoing_edges) else ""
                
            matched_data[num] = {
                'sumo_junction_id': best_node.getID(),
                'lat': lat,
                'lon': lon,
                'incoming_links': incoming_map,
                'outgoing_links': outgoing_map,
                'all_sumo_incoming': incoming_edges,
                'all_sumo_outgoing': outgoing_edges
            }
        else:
            print(f"Warning: Could not match Intersection #{num} (lat: {lat}, lon: {lon}) to any SUMO junction within 50m. Best dist: {best_dist if best_node else 'N/A'}")
            
    # マッピングテーブルの書き出し
    os.makedirs(os.path.dirname(output_mapping), exist_ok=True)
    with open(output_mapping, 'w', encoding='utf-8') as f:
        json.dump(matched_data, f, indent=4, ensure_ascii=False)
        
    print(f"Successfully generated mapping table: {output_mapping}")
    print(f"Total matched junctions: {len(matched_data)}")

if __name__ == "__main__":
    match_network()
