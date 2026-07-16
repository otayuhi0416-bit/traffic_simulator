import os
import sumolib

net_file = "network/akita.net.xml"
if not os.path.exists(net_file):
    print("Network not found.")
    exit(1)

net = sumolib.net.readNet(net_file)

node_ids = ["8425745665", "10915541257"]

print("Upstream Nodes Coordinates:")
print("="*60)
for n_id in node_ids:
    node = net.getNode(n_id)
    if node is not None:
        coords = node.getCoord()
        print(f"Node ID: {n_id:<15} | UTM X: {coords[0]:.2f} | UTM Y: {coords[1]:.2f}")
