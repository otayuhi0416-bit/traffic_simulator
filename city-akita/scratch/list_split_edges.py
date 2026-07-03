import os
import sumolib

net_file = "network/akita.net.xml"
if not os.path.exists(net_file):
    print("Network not found.")
    exit(1)

net = sumolib.net.readNet(net_file)

print("All edges containing '124579517':")
print("="*60)
for edge in net.getEdges():
    e_id = edge.getID()
    if "124579517" in e_id:
        print(f"Edge ID: {e_id:<25} | From: {edge.getFromNode().getID():<15} | To: {edge.getToNode().getID():<15} | Lanes: {len(edge.getLanes())}")
