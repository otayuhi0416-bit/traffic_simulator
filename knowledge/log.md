---
type: UpdateHistory
title: 更新履歴 (log.md)
description: ナレッジベースの変更および更新の歴史。
timestamp: 2026-06-25T16:01:00+09:00
---

# 更新履歴 (log.md)

本ファイルは、秋田市交通シミュレーションプロジェクトのナレッジベース（OKF Bundle）に対する変更履歴を時系列に記録するログファイルです。

## [2026-06-25] ナレッジベースの新規開設

*   **更新者**: Antigravity (AIエージェント)
*   **概要**: OKF v0.1 仕様に準拠したナレッジベースの設計および初期構築。
*   **追加されたコンセプトドキュメント**:
    *   `knowledge/index.md`: ナレッジベース全体のルートインデックス。
    *   `knowledge/project_overview.md`: プロジェクトの全体目的、技術スタック、およびアーキテクチャフローの解説。
    *   `knowledge/data/index.md` & `osm_map.md` & `intersections.md`: 地図データ（OSM）および交差点マッピングテーブル（`match_table.json`）の定義。
    *   `knowledge/network/index.md` & `road_network.md`: SUMO道路網（.net.xml）のビルド処理および手動パッチ適用の説明。
    *   `knowledge/demand/index.md` & `traffic_flow.md`: 断面交通量データ（秋田県警CSV）からのルート・フロー需要生成アルゴリズムの解説。
    *   `knowledge/simulation/index.md` & `sumo_sim.md`: `akita.sumocfg` の構成設定および TraCI による動的な信号スプリット適用処理の解説。
    *   `knowledge/playbooks/index.md` & `signal_tuning.md`: レーン接続や信号機の有無などの手動微調整ガイド（プレイブック）。

## [2026-07-16] 交差点パッチWebエディタのUI向上と幾何計算の高度化

*   **更新者**: Antigravity (AIエージェント)
*   **概要**: 交差点パッチWebエディタでの左側通行アライメント対応、極小エッジ（20cm）対応、直進/右左折矢印の干渉を回避する高度な幾何座標制御を実装し、操作マニュアルとスクリーンショットを追加。
*   **修正・追加ファイル**:
    *   [index.html](file:///c:/Users/Genno_Shirou/Documents/works/traffic_simulator/city-akita/web_editor/templates/index.html): 
        *   矢印の分岐開始点 `D` を `35px` 手前、矢印セグメント長 `L_arrow` を `20px` に延長し、自然なワイド分岐に変更。
        *   右左折案内矢印について、直進案内矢印との干渉を避けるため `16px` 手前に引き下げるアライメントを実装。
        *   `pMid`（折れ曲がり点）を車線中心線上（左右ズレ0）に配置する厳密なベクトル計算式 $d_{mid} = H_{offset} + k \cdot (\vec{u}_{out} \cdot \vec{u}_{in})$ に変更し、曲がる手前での逆方向への膨らみ（S字軌跡）を完全に排除。
        *   左側通行用データ（index 0 = 左側/外側）を正しく画面の左側に配置するため、SVG描画のオフセット計算のインデックス順序を反転。
        *   極小エッジ（20cm程度）で方向ベクトルが逆転する現象を防ぐため、エッジ長（`edgeLen`）に応じた動的スケール制限を導入。
    *   [editor_instructions.md](file:///c:/Users/Genno_Shirou/Documents/works/traffic_simulator/knowledge/playbooks/editor_instructions.md): 交差点パッチWebエディタの操作マニュアル。
    *   `knowledge/resources/editor_main.png` & `editor_editing.png`: マニュアル用エディタのスクリーンショット画像。
