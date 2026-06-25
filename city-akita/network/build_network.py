import os
import subprocess
import sys

# SUMO_HOMEが設定されていない場合のデフォルトを設定
if "SUMO_HOME" not in os.environ:
    os.environ["SUMO_HOME"] = "C:\\Program Files (x86)\\Eclipse\\Sumo"

def build_network():
    osm_file = "data/raw/akita_center.osm"
    output_net = "network/akita.net.xml"
    
    # 必要なディレクトリの作成
    os.makedirs("network", exist_ok=True)
    
    if not os.path.exists(osm_file):
        print(f"Error: {osm_file} does not exist. Run download_osm.py first.")
        sys.exit(1)
        
    print(f"Building SUMO network from {osm_file}...")
    
    # netconvertの基本引数
    # OSMのインポートと、日本（左側通行）の設定を指定
    cmd = [
        "netconvert",
        "--osm-files", osm_file,
        "-o", output_net,
        "--lefthand", # 日本は左側通行
        "--geometry.junction-mismatch-threshold", "20",
        "--tls.discard-simple", "true",
        "--tls.join", "true",
        "--no-turnarounds",
        "--junctions.join",
        "--keep-edges.by-vclass", "passenger",
    ]
    
    # パッチファイルの有無を確認して引数に追加
    patch_dir = "data/patch"
    if os.path.exists(patch_dir):
        # connections
        con_patch = os.path.join(patch_dir, "connections.con.xml")
        if os.path.exists(con_patch):
            cmd.extend(["--connection-files", con_patch])
            print(f"Applying connection patch: {con_patch}")
            
        # nodes
        nod_patch = os.path.join(patch_dir, "nodes.nod.xml")
        if os.path.exists(nod_patch):
            cmd.extend(["--node-files", nod_patch])
            print(f"Applying node patch: {nod_patch}")
            
        # edges
        edg_patch = os.path.join(patch_dir, "edges.edg.xml")
        if os.path.exists(edg_patch):
            cmd.extend(["--edge-files", edg_patch])
            print(f"Applying edge patch: {edg_patch}")
            
        # traffic lights
        tfl_patch = os.path.join(patch_dir, "traffic_lights.tfl.xml")
        if os.path.exists(tfl_patch):
            cmd.extend(["--tfl-files", tfl_patch])
            print(f"Applying traffic light patch: {tfl_patch}")
            
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        # SUMOのパス解決のため、環境変数にSUMO_HOMEが定義されているかも確認
        env = os.environ.copy()
        if "SUMO_HOME" in env:
            # netconvertのフルパスを試みる
            netconvert_path = os.path.join(env["SUMO_HOME"], "bin", "netconvert")
            if os.path.exists(netconvert_path) or os.path.exists(netconvert_path + ".exe"):
                cmd[0] = netconvert_path
                
        result = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        print("Network build succeeded!")
        print(result.stdout[:1000])
    except FileNotFoundError:
        print("Error: 'netconvert' command not found. Please ensure SUMO is installed and added to your PATH or SUMO_HOME is set.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print("Error: netconvert failed!")
        print(e.stderr)
        sys.exit(1)

if __name__ == "__main__":
    build_network()
