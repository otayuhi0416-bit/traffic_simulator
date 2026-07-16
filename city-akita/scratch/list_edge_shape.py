import os
import sumolib

net_file = "network/akita.net.xml"
if not os.path.exists(net_file):
    print("Network not found.")
    exit(1)

net = sumolib.net.readNet(net_file)

targets = ["-461237392#5", "461237392#4", "-124585729#1", "-124579517#1"]

print("Edges Shapes (UTM coordinates list):")
print("="*80)
for edge_id in targets:
    edge = net.getEdge(edge_id)
    if edge is not None:
        shape = edge.getShape()
        print(f"\nEdge: {edge_id} | Length: {edge.getLength():.2f}m")
        for i, pt in enumerate(shape):
            print(f"  Point {i}: ({pt[0]:.2f}, {pt[1]:.2f})")
