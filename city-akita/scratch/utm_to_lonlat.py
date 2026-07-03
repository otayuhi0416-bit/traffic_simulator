import pyproj

# UTM Zone 54N (秋田市はZone 54) のプロジェクション設定
# build_network.pyで --proj.utm true を指定すると、
# EPSG:32654 (WGS 84 / UTM Zone 54N) がデフォルトで使用されます。
proj_utm = pyproj.Proj(proj="utm", zone=54, ellps="WGS84", datum="WGS84")

taper_nodes = [
    {"name": "north", "x": 1310.47, "y": 2424.95},
    {"name": "south", "x": 1307.59, "y": 2484.88},
    {"name": "west", "x": 1346.31, "y": 2456.09},
    {"name": "east", "x": 1289.48, "y": 2454.23}
]

# あれ？ 
# 実は、netconvertの --proj.utm true で得られた座標は、
# 通常のUTM座標系の原点（秋田市周辺だと X=400000m付近, Y=4300000m付近）ではなく、
# 「重心位置などを原点 (0,0) としたローカルメートル座標」になっている可能性があります！
# なぜなら、先ほどの get_junction_coords.py の出力で：
# Node Coordinate 1386236878 : X=1309.17, Y=2454.92
# と、千の桁 (1300m付近) になっているからです。
# これは、netconvertが「投影後に、ネットワークの最小(x,y)を基準にオフセット（または投影中心を基準にシフト）」
# しているためです。

# この場合、pyprojで直接逆変換するのではなく、
# 元の akita_center.osm から各上流ノードの「本当の経度・緯度」を取得し、
# 経度・緯度空間上で「30m手前（または10m手前）」の緯度経度を線形補間する方が、
# 100%安全かつ正確に正しい lon/lat を算出できます！

# そこで、OSMノードの本当の緯度経度（lon, lat）を取得し、補間計算を行います。
