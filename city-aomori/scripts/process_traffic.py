import os
import json
import csv
import sys
from datetime import datetime

# SUMO_HOMEが設定されていない場合のデフォルトを設定
if "SUMO_HOME" not in os.environ:
    os.environ["SUMO_HOME"] = "C:\\Program Files (x86)\\Eclipse\\Sumo"

# sys.path に SUMO の tools を追加（環境変数 SUMO_HOME から）
if "SUMO_HOME" in os.environ:
    sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
try:
    import sumolib
except ImportError:
    pass

def process_traffic(target_date="2026/04/08", start_hour=8, duration_hours=1):
    traffic_csv = "resources/typeB_akita_2026_04/秋田県警_202604.csv"
    match_table_path = "data/match_table.json"
    net_path = "network/akita.net.xml"
    output_rou = "demand/akita.rou.xml"
    
    if not os.path.exists(match_table_path):
        print(f"Error: {match_table_path} not found. Run match_network.py first.")
        sys.exit(1)
        
    # マッピング情報のロード
    with open(match_table_path, 'r', encoding='utf-8') as f:
        match_table = json.load(f)
        
    # SUMO道路網のロード（経路検索用）
    print("Loading net...")
    net = sumolib.net.readNet(net_path)
    
    # ネットワーク内の境界（出口）エッジをリストアップ
    # getOutgoing()が空＝これ以上進めない道路網の端
    boundary_edges = []
    for edge in net.getEdges():
        if not edge.getOutgoing():
            boundary_edges.append(edge)
    print(f"Found {len(boundary_edges)} boundary exit edges in the network.")
    
    # 1. 断面交通量データの集計
    # キー: リンク番号, 値: 車両台数の合計
    link_traffic = {}
    
    # 開始時刻と終了時刻の生成 (例: 2026/04/08 08:00 〜 09:00)
    # csv内の時刻フォーマット: "2026/04/01 00:00"
    start_dt = datetime.strptime(f"{target_date} {start_hour:02d}:00", "%Y/%m/%d %H:%M")
    # 終了時刻
    end_dt = datetime.strptime(f"{target_date} {(start_hour + duration_hours):02d}:00", "%Y/%m/%d %H:%M")
    
    print(f"Filtering traffic data from {start_dt} to {end_dt}...")
    
    with open(traffic_csv, mode='r', encoding='cp932') as f:
        reader = csv.DictReader(f)
        for row in reader:
            time_str = row['時刻'].strip()
            try:
                dt = datetime.strptime(time_str, "%Y/%m/%d %H:%M")
                if start_dt <= dt < end_dt:
                    link_num = row['リンク番号'].strip()
                    traffic_vol = int(row['断面交通量'])
                    
                    link_traffic[link_num] = link_traffic.get(link_num, 0) + traffic_vol
            except ValueError:
                continue
                
    print(f"Found traffic data for {len(link_traffic)} links in the target time frame.")
    
    # 2. SUMOフロー定義の作成
    # flow要素をXML文字列として生成
    flows = []
    
    # シミュレーション時間 (秒)
    begin_sec = 0
    end_sec = duration_hours * 3600
    
    flow_counter = 0
    for intersection_num, data in match_table.items():
        incoming_links = data['incoming_links']
        outgoing_links = data['outgoing_links']
        
        # 各流入リンクに対して交通量を設定
        for link_num, sumo_edge in incoming_links.items():
            if not sumo_edge:
                continue
                
            # このリンクの交通量を取得
            vol = link_traffic.get(link_num, 0)
            if vol == 0:
                continue
                
            # 最適な流出エッジまたはネットワーク境界（出口）へのルートを生成する
            to_edges = [edge for edge in outgoing_links.values() if edge]
            from_edge_obj = net.getEdge(sumo_edge)
            
            # 流入エッジから到達可能なネットワーク境界（出口）までの全ルートを探索
            valid_routes = []
            for b_edge in boundary_edges:
                if b_edge.getID() == sumo_edge:
                    continue
                route, cost = net.getShortestPath(from_edge_obj, b_edge)
                if route and len(route) > 1:
                    valid_routes.append([edge.getID() for edge in route])
            
            flow_id = f"flow_{intersection_num}_{link_num}"
            
            if valid_routes:
                # 複数のルートが存在する場合、ルートディストリビューションを作成して目的地を分散させる
                dist_id = f"dist_{intersection_num}_{link_num}"
                flows.append(f'    <routeDistribution id="{dist_id}">')
                prob = 1.0 / len(valid_routes)
                for r_edges in valid_routes:
                    route_str = " ".join(r_edges)
                    flows.append(f'        <route edges="{route_str}" probability="{prob:.4f}"/>')
                flows.append(f'    </routeDistribution>')
                
                flows.append(f'    <flow id="{flow_id}" route="{dist_id}" type="car" begin="{begin_sec}" end="{end_sec}" number="{vol}" departLane="free" departSpeed="max" />')
            else:
                # 境界へのルートがない場合は、交差点直近の流出エッジへの短いルートでフォールバック
                fallback_route = None
                for to_edge in to_edges:
                    to_edge_obj = net.getEdge(to_edge)
                    route, cost = net.getShortestPath(from_edge_obj, to_edge_obj)
                    if route:
                        fallback_route = [edge.getID() for edge in route]
                        break
                
                if fallback_route:
                    route_id = f"route_{intersection_num}_{link_num}"
                    route_str = " ".join(fallback_route)
                    flows.append(f'    <route id="{route_id}" edges="{route_str}" />')
                    flows.append(f'    <flow id="{flow_id}" route="{route_id}" type="car" begin="{begin_sec}" end="{end_sec}" number="{vol}" departLane="free" departSpeed="max" />')
                else:
                    flows.append(f'    <flow id="{flow_id}" from="{sumo_edge}" type="car" begin="{begin_sec}" end="{end_sec}" number="{vol}" departLane="free" departSpeed="max" />')
                
            flow_counter += 1
            
    # XMLファイルの書き出し
    os.makedirs(os.path.dirname(output_rou), exist_ok=True)
    with open(output_rou, 'w', encoding='utf-8') as f:
        f.write('<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">\n')
        f.write('    <vType id="car" accel="2.6" decel="4.5" sigma="0.5" length="5.0" minGap="2.5" maxSpeed="13.89" guiShape="passenger" lcCooperative="1.0" lcSpeedGain="1.0" lcStrategic="1.0" latAlignment="center" minGapLat="0.6"/>\n\n')
        
        for item in flows:
            f.write(item + "\n")
            
        f.write('</routes>\n')
        
    print(f"Generated {flow_counter} flows in {output_rou}")

if __name__ == "__main__":
    # デフォルト: 2026年4月8日 (水) 08:00 〜 09:00 (1時間)
    target_date = "2026/04/08"
    start_hour = 8
    
    if len(sys.argv) > 2:
        target_date = sys.argv[1]
        start_hour = int(sys.argv[2])
        
    process_traffic(target_date, start_hour)
