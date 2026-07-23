---
type: DirectoryIndex
title: プレイブックインデックス
description: 信号機や交差点レーン接続の手動微調整手順（プレイブック）のインデックス。
timestamp: 2026-06-25T15:55:00+09:00
---

# プレイブックインデックス

本フォルダは、自動変換されたシミュレーション上の道路・交差点データに対して、実世界の運用状態に一致させるための「手動微調整・チューニング手順書」を管理しています。

## 構成コンセプト

* [信号制御・レーン接続調整プレイブック (signal_tuning.md)](./signal_tuning.md): 右折専用レーン指定、信号有無の変更、マッピング情報の直接補正手順の説明。
* [交差点パッチWebエディタ操作マニュアル (editor_instructions.md)](./editor_instructions.md): Webエディタによる直感的な車線設定、右折レーン形式設定、車線別流出先定義の編集手順の説明。

## プレイブックに関連するパッチパス
* `city-akita/data/patch/nodes.nod.xml`: 信号あり/なし・優先道路タイプの変更定義。
* `city-akita/data/patch/connections.con.xml`: レーンレベルでの接続制御定義。
* `city-akita/data/match_table.json`: 紐付け定義。
