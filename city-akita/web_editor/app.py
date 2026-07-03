import os
import subprocess
import threading
import xml.etree.ElementTree as ET
from flask import Flask, jsonify, request, render_template

app = Flask(__name__, template_folder='templates')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NET_FILE = os.path.join(PROJECT_ROOT, "network", "akita.net.xml")
PATCH_DIR = os.path.join(PROJECT_ROOT, "data", "patch")

# パイプライン実行状態
pipeline_status = {
    "status": "idle",
    "log": "",
    "result": None
}

def get_net_root():
    if not os.path.exists(NET_FILE):
        return None
    try:
        tree = ET.parse(NET_FILE)
        return tree.getroot()
    except Exception as e:
        print(f"Error parsing net file: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get_junctions')
def get_junctions():
    root = get_net_root()
    if root is None:
        return jsonify({"error": "Network file not found. Please build network first."}), 404
    
    junctions = []
    for j in root.findall("junction"):
        j_id = j.get("id")
        j_type = j.get("type")
        # 信号交差点(traffic_light)または優先交差点(priority)のみリスト化
        if j_type in ["traffic_light", "priority"] and not j_id.startswith("cluster"):
            # 流入車線数 (incLanes の個数をカウント)
            inc_str = j.get("incLanes")
            total_lanes = 0
            if inc_str:
                total_lanes = len(inc_str.split(" "))
                
            junctions.append({
                "id": j_id,
                "type": j_type,
                "x": float(j.get("x")),
                "y": float(j.get("y")),
                "totalLanes": total_lanes
            })
    return jsonify(junctions)


# ミニマップデータのグローバルキャッシュ
minimap_data_cache = None

@app.route('/api/get_minimap_data')
def get_minimap_data():
    global minimap_data_cache
    if minimap_data_cache is not None:
        return jsonify(minimap_data_cache)
        
    root = get_net_root()
    if root is None:
        return jsonify({"error": "Network file not found"}), 404
        
    edges = []
    min_x, max_x = float('inf'), float('-inf')
    min_y, max_y = float('inf'), float('-inf')
    
    for edge in root.findall("edge"):
        disallow = edge.get("disallow")
        if disallow and "passenger" in disallow:
            continue
            
        lanes = edge.findall("lane")
        if not lanes:
            continue
            
        shape = lanes[0].get("shape")
        if not shape:
            continue
            
        pts = shape.split(" ")
        p_start = list(map(float, pts[0].split(",")))
        p_end = list(map(float, pts[-1].split(",")))
        
        edges.append({
            "x1": p_start[0],
            "y1": p_start[1],
            "x2": p_end[0],
            "y2": p_end[1]
        })
        
        # 境界ボックスの更新
        for pt in [p_start, p_end]:
            if pt[0] < min_x: min_x = pt[0]
            if pt[0] > max_x: max_x = pt[0]
            if pt[1] < min_y: min_y = pt[1]
            if pt[1] > max_y: max_y = pt[1]
            
    minimap_data_cache = {
        "edges": edges,
        "bbox": {
            "minX": min_x,
            "maxX": max_x,
            "minY": min_y,
            "maxY": max_y
        }
    }
    return jsonify(minimap_data_cache)

@app.route('/api/load_junction')
def load_junction():
    j_id = request.args.get("id")
    if not j_id:
        return jsonify({"error": "Missing junction id"}), 400
    
    root = get_net_root()
    if root is None:
        return jsonify({"error": "Network file not found"}), 404
    
    # 交差点の検索
    j_elem = None
    for j in root.findall("junction"):
        if j.get("id") == j_id:
            j_elem = j
            break
            
    if j_elem is None:
        return jsonify({"error": f"Junction {j_id} not found"}), 404
        
    junction_data = {
        "id": j_id,
        "x": float(j_elem.get("x")),
        "y": float(j_elem.get("y")),
        "type": j_elem.get("type"),
        "incoming": [],
        "outgoing": [],
        "context_edges": [],
        "connections": []
    }
    
    # 接続エッジの収集
    for edge in root.findall("edge"):
        # 歩行者道やサービス道路などは除く
        vclass = edge.get("allow")
        disallow = edge.get("disallow")
        if disallow and "passenger" in disallow:
            continue
            
        edge_id = edge.get("id")
        if edge.get("to") == j_id:
            lanes = edge.findall("lane")
            shape = lanes[0].get("shape") if lanes else ""
            junction_data["incoming"].append({
                "id": edge_id,
                "numLanes": len(lanes),
                "shape": shape
            })
        elif edge.get("from") == j_id:
            lanes = edge.findall("lane")
            shape = lanes[0].get("shape") if lanes else ""
            junction_data["outgoing"].append({
                "id": edge_id,
                "numLanes": len(lanes),
                "shape": shape
            })
            
    # ターゲット交差点の1つ隣のオブジェクト(接続先・接続元交差点に繋がるエッジ)の収集
    incoming_ids = {e["id"] for e in junction_data["incoming"]}
    outgoing_ids = {e["id"] for e in junction_data["outgoing"]}
    neighbor_nodes = set()
    
    for edge in root.findall("edge"):
        edge_id = edge.get("id")
        if edge_id in incoming_ids:
            e_from = edge.get("from")
            if e_from: neighbor_nodes.add(e_from)
        elif edge_id in outgoing_ids:
            e_to = edge.get("to")
            if e_to: neighbor_nodes.add(e_to)
            
    for edge in root.findall("edge"):
        edge_id = edge.get("id")
        if edge_id in incoming_ids or edge_id in outgoing_ids:
            continue
            
        disallow = edge.get("disallow")
        if disallow and "passenger" in disallow:
            continue
            
        e_from = edge.get("from")
        e_to = edge.get("to")
        if e_from in neighbor_nodes or e_to in neighbor_nodes:
            lanes = edge.findall("lane")
            shape = lanes[0].get("shape") if lanes else ""
            if shape:
                junction_data["context_edges"].append({
                    "id": edge_id,
                    "numLanes": len(lanes),
                    "shape": shape
                })
            
    # 接続関係(Connection)の収集
    for conn in root.findall("connection"):
        if conn.get("from") in [e["id"] for e in junction_data["incoming"]] and conn.get("to") in [e["id"] for e in junction_data["outgoing"]]:
            junction_data["connections"].append({
                "from": conn.get("from"),
                "to": conn.get("to"),
                "fromLane": int(conn.get("fromLane")),
                "toLane": int(conn.get("toLane")),
                "dir": conn.get("dir")
            })
            
    return jsonify(junction_data)

@app.route('/api/save_patch', methods=['POST'])
def save_patch():
    data = request.json
    if not data or "junctionId" not in data:
        return jsonify({"error": "Invalid patch data"}), 400
        
    j_id = data["junctionId"]
    settings = data["settings"] # 各流入エッジの設定リスト
    
    # 1. nodes.nod.xml パッチの生成
    nodes_root = ET.Element("nodes")
    nodes_root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    nodes_root.set("xsi:noNamespaceSchemaLocation", "http://sumo.dlr.de/xsd/nodes_file.xsd")
    
    # 2. edges.edg.xml パッチの生成
    edges_root = ET.Element("edges")
    edges_root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    edges_root.set("xsi:noNamespaceSchemaLocation", "http://sumo.dlr.de/xsd/edges_file.xsd")
    
    # 3. connections.con.xml パッチの生成
    conns_root = ET.Element("connections")
    conns_root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    conns_root.set("xsi:noNamespaceSchemaLocation", "http://sumo.dlr.de/xsd/connections_file.xsd")
    
    # 元のネットワークから形状点を取得して正確に内挿するためのヘルパー
    net_root = get_net_root()
    
    for edge_id, config in settings.items():
        # config: {"lanes": 3, "taper": "none" / "taper", "taperLen": 30, "conns": [...]}
        target_lanes = config["lanes"]
        taper_type = config.get("taper", "none")
        taper_len = config.get("taperLen", 30)
        
        # 元のエッジ情報をネットワークファイルから検索
        orig_edge = None
        for e in net_root.findall("edge"):
            if e.get("id") == edge_id:
                orig_edge = e
                break
                
        if orig_edge is None:
            continue
            
        from_node = orig_edge.get("from")
        to_node = orig_edge.get("to")
        
        if taper_type == "taper":
            # 30m手前右折レーン（物理分割テーパー）
            # 中間ノードのIDと座標を計算
            lanes = orig_edge.findall("lane")
            if lanes:
                shape_str = lanes[0].get("shape")
                points = [list(map(float, pt.split(","))) for pt in shape_str.split(" ")]
                
                # 直線上の30m手前座標を計算 (UTM)
                # 終点(交差点側)から指定メートル手前の位置を内挿
                # ※簡易直線補間
                p_start = points[0]
                p_end = points[-1]
                dx = p_end[0] - p_start[0]
                dy = p_end[1] - p_start[1]
                length = (dx**2 + dy**2)**0.5
                
                if length > taper_len:
                    ratio = (length - taper_len) / length
                    nx = p_start[0] + ratio * dx
                    ny = p_start[1] + ratio * dy
                    
                    # UTM座標から緯度経度へ簡易逆変換 (秋田市: UTM Zone 54N)
                    # ※netconvertはproj.utmを指定しているため、UTM座標(x,y)をnodes.nod.xmlに直接記述しても認識されます！
                    taper_node_id = f"node_{j_id}_{edge_id}_taper"
                    
                    # nodesパッチに中間ノード追加 (UTM座標をx, yにそのまま指定)
                    node_elem = ET.SubElement(nodes_root, "node")
                    node_elem.set("id", taper_node_id)
                    node_elem.set("x", f"{nx:.2f}")
                    node_elem.set("y", f"{ny:.2f}")
                    node_elem.set("type", "priority")
                    
                    # edgesパッチに、中間ノードから交差点までの区間を増設して定義
                    # ※日本の左側通行に合わせ、車線が右側(中央線側)に増えるよう spreadType="right" を自動付与！
                    edge_elem = ET.SubElement(edges_root, "edge")
                    edge_elem.set("id", f"edge_{j_id}_{edge_id}_taper_to_junc")
                    edge_elem.set("from", taper_node_id)
                    edge_elem.set("to", to_node)
                    edge_elem.set("numLanes", str(target_lanes))
                    edge_elem.set("spreadType", "right") # これでアライメントのいびつさが消滅します！
                    
                    # connectionsパッチで、この新規エッジからの接続を定義
                    for conn in config.get("conns", []):
                        # conn: {"fromLane": 0, "toLane": 0, "to": "edge_id"}
                        c_elem = ET.SubElement(conns_root, "connection")
                        c_elem.set("from", f"edge_{j_id}_{edge_id}_taper_to_junc")
                        c_elem.set("to", conn["to"])
                        c_elem.set("fromLane", str(conn["fromLane"]))
                        c_elem.set("toLane", str(conn["toLane"]))
                    
                    # 古いエッジ名からの接続の重複を削除
                    d_elem = ET.SubElement(conns_root, "delete")
                    d_elem.set("from", edge_id)
                    d_elem.set("to", to_node)
        else:
            # エッジ全体拡幅またはデフォルト維持
            # ※車線変更アライメントの歪みを防ぐため spreadType="right" を付与
            edge_elem = ET.SubElement(edges_root, "edge")
            edge_elem.set("id", edge_id)
            edge_elem.set("from", from_node)
            edge_elem.set("to", to_node)
            edge_elem.set("numLanes", str(target_lanes))
            edge_elem.set("spreadType", "right")
            
            # connections接続の上書き定義
            for conn in config.get("conns", []):
                c_elem = ET.SubElement(conns_root, "connection")
                c_elem.set("from", edge_id)
                c_elem.set("to", conn["to"])
                c_elem.set("fromLane", str(conn["fromLane"]))
                c_elem.set("toLane", str(conn["toLane"]))
                
    # パッチファイルの書き出し
    os.makedirs(PATCH_DIR, exist_ok=True)
    
    ET.ElementTree(nodes_root).write(os.path.join(PATCH_DIR, "nodes.nod.xml"), encoding="utf-8", xml_declaration=True)
    ET.ElementTree(edges_root).write(os.path.join(PATCH_DIR, "edges.edg.xml"), encoding="utf-8", xml_declaration=True)
    ET.ElementTree(conns_root).write(os.path.join(PATCH_DIR, "connections.con.xml"), encoding="utf-8", xml_declaration=True)
    
    return jsonify({"success": True, "message": "Patches generated and saved successfully!"})

def run_command_in_background(cmds):
    global pipeline_status
    pipeline_status["status"] = "running"
    pipeline_status["log"] = ""
    
    try:
        for name, cmd in cmds:
            pipeline_status["log"] += f"\n>>> Running {name}...\n"
            p = subprocess.Popen(
                cmd,
                shell=True,
                cwd=PROJECT_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            while True:
                line = p.stdout.readline()
                if not line:
                    break
                pipeline_status["log"] += line
            p.wait()
            if p.returncode != 0:
                pipeline_status["status"] = "failed"
                pipeline_status["log"] += f"\nError: {name} failed with exit code {p.returncode}\n"
                return
                
        # 実行成功時の結果解析
        pipeline_status["status"] = "success"
        pipeline_status["log"] += "\n>>> Simulation Pipeline Completed Successfully!\n"
        
        # ボトネックランキングの読み込み
        rank_file = os.path.join(PROJECT_ROOT, "sim", "junction_bottlenecks.txt")
        if os.path.exists(rank_file):
            with open(rank_file, "r", encoding="utf-8") as f:
                pipeline_status["result"] = f.read()
                
    except Exception as e:
        pipeline_status["status"] = "failed"
        pipeline_status["log"] += f"\nException: {str(e)}\n"

@app.route('/api/run_pipeline', methods=['POST'])
def run_pipeline():
    global pipeline_status
    if pipeline_status["status"] == "running":
        return jsonify({"error": "Pipeline is already running"}), 400
        
    cmds = [
        ("Network Rebuild", "python network/build_network.py"),
        ("Demand Generation", "python scripts/process_traffic.py 2026/04/08 8"),
        ("SUMO Simulation Run", "python sim/run_simulation.py 2026/04/08 8 --nogui")
    ]
    
    t = threading.Thread(target=run_command_in_background, args=(cmds,))
    t.start()
    
    return jsonify({"success": True, "message": "Pipeline started in background."})

@app.route('/api/pipeline_status')
def get_pipeline_status():
    return jsonify(pipeline_status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
