# 青森市中心部 交通渋滞シミュレーション (SUMO)

本プロジェクトは、秋田県秋田市中心部を対象に、OSMから自動生成された道路網と、実世界の断面交通量および信号制御オープンデータを連動させた交通シミュレーション環境です。

## 動作要件
- **Python 3.12+**
- **SUMO (Simulation of Urban MObility) 1.27.0+**
- 必要なPythonパッケージ (インストール済):
  ```bash
  pip install -r requirements.txt
  ```

## フォルダ構成
- `data/`: OSMデータ、交差点座標リスト、マッピングテーブル。
- `scripts/`: 地図のダウンロード、スクレイピング、マッピング、交通量変換用の Python スクリプト。
- `network/`: SUMO道路網データ（`.net.xml`）。
- `demand/`: 断面交通量から生成された交通需要（ルート・フロー）定義。
- `sim/`: SUMOの設定ファイルおよびTraCIによるシミュレーション起動スクリプト。
- `resources/`: 秋田県警の信号・断面交通量のオープンデータ（配置済み）。

## 実行手順

### 1. 道路網のビルド (初回、または地図更新時のみ)
```bash
# OSM地図データのダウンロード
python scripts/download_osm.py

# SUMO道路網のビルド
python network/build_network.py
```

### 2. 交差点マッピングの生成 (初回、または地図更新時のみ)
```bash
# 交差点位置情報のスクレイピング
python scripts/scrape_intersections.py

# SUMOノードとオープンデータ交差点の紐付け生成
python scripts/match_network.py
```

### 3. 指定した曜日・時間帯の需要生成とシミュレーション実行
シミュレーションで再現したい日付と開始時間を指定して実行します。

* **交通需要（flow）の生成**:
  ```bash
  # 例: 2026年4月8日 (水) 朝 8:00 〜 9:00 の断面交通量を反映
  python scripts/process_traffic.py 2026/04/08 8
  ```
  ※日付や時間は CSV に存在する範囲で任意に指定可能です。

* **シミュレーションの起動 (信号スプリット制御の自動適用)**:
  ```bash
  # GUIあり (SUMO-GUIが起動します)
  python sim/run_simulation.py 2026/04/08 8

  # GUIなし (CUIで高速にシミュレーションを完走させます)
  python sim/run_simulation.py 2026/04/08 8 --nogui
  ```

## 信号や交差点接続の修正方法
自動変換された道路網の接続などに現実と異なる点がある場合、以下のパッチファイルに定義を追記して `python network/build_network.py` を実行することで、再現可能な修正を適用できます。

- `data/patch/nodes.nod.xml`: 信号機の有無や交差点タイプの変更。
- `data/patch/connections.con.xml`: レーン同士の接続関係（右折専用レーンの指定など）の修正。
- `data/match_table.json`: 自動紐付けされた交差点とSUMOエッジのマッピングの直接修正。
