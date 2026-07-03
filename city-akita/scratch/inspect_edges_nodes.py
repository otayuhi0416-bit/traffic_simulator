import os
import sumolib

net_file = "network/akita.net.xml"
if not os.path.exists(net_file):
    # パッチなしで一度ビルドしたネットワークがあるはずですが、
    # 直前にビルドが失敗したため削除されてしまっています。
    # そこで、パッチなしの状態で一度だけテンポラリにビルドし、
    # そのファイルから情報を取得します。
    pass

net = sumolib.net.readNet(net_file)

targets = ["-461237392#5", "461237392#4", "-124585729#1", "-124585729#0", "-124579517#1", "-124579517#0"]

print("Edges From/To nodes:")
print("="*60)
for edge_id in targets:
    edge = net.getEdge(edge_id)
    if edge is not None:
        print(f"Edge: {edge_id:<20} | From Node: {edge.getFromNode().getID():<30} | To Node: {edge.getToNode().getID():<30}")
