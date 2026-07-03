import xml.etree.ElementTree as ET
import math

osm_file = "data/raw/akita_center.osm"
tree = ET.parse(osm_file)
root = tree.getroot()

# ノード座標ディクショナリを構築
node_coords = {}
for node in root.findall("node"):
    n_id = node.get("id")
    node_coords[n_id] = (float(node.get("lon")), float(node.get("lat")))

# ターゲットノードの座標取得
def get_coord(n_id):
    if n_id in node_coords:
        return node_coords[n_id]
    print(f"Error: Node {n_id} not found in OSM.")
    return None

# 交差点
junc = get_coord("1386236878")
# 北上流
north_up = get_coord("8425745667")
# 南上流
south_up = get_coord("1386278487")

# 西側（交差点側下流端: 7296384874, 上流端: 8425745665）
west_down = get_coord("7296384874")
west_up = get_coord("8425745665")

# 東側（交差点側下流端: 7296384881, 上流端: 10915541257）
east_down = get_coord("7296384881")
east_up = get_coord("10915541257")

# 地球パラメータ (秋田市付近: 北緯39.7度)
lat_degree_m = 111100.0  # 1度あたり約111.1km
lon_degree_m = 111100.0 * math.cos(math.radians(39.715)) # 1度あたり約85.4km

def interpolate_lonlat(start, end, target_dist_m):
    """start(交差点側)からend(上流側)に向かってtarget_dist_mメートル進んだ位置のlon, latを計算"""
    d_lon = end[0] - start[0]
    d_lat = end[1] - start[1]
    
    # メートル単位での距離
    dx = d_lon * lon_degree_m
    dy = d_lat * lat_degree_m
    total_len = math.sqrt(dx*dx + dy*dy)
    
    ratio = target_dist_m / total_len
    if ratio > 1.0:
        ratio = 0.9 # エッジ長より長い場合は90%位置にする
        
    target_lon = start[0] + ratio * d_lon
    target_lat = start[1] + ratio * d_lat
    return target_lon, target_lat

# 各方向の中間ノード緯度経度を算出
# 北本線 (交差点から30m手前)
n_lon, n_lat = interpolate_lonlat(junc, north_up, 30.0)
# 南本線 (交差点から30m手前)
s_lon, s_lat = interpolate_lonlat(junc, south_up, 30.0)
# 西支線 (西下流端から30m手前)
w_lon, w_lat = interpolate_lonlat(west_down, west_up, 30.0)
# 東支線 (東下流端から10m手前)
e_lon, e_lat = interpolate_lonlat(east_down, east_up, 10.0)

print("Calculated lon, lat for taper nodes:")
print("="*60)
print(f"North taper: x=\"{n_lon:.7f}\" y=\"{n_lat:.7f}\"")
print(f"South taper: x=\"{s_lon:.7f}\" y=\"{s_lat:.7f}\"")
print(f"West taper:  x=\"{w_lon:.7f}\" y=\"{w_lat:.7f}\"")
print(f"East taper:  x=\"{e_lon:.7f}\" y=\"{e_lat:.7f}\"")
