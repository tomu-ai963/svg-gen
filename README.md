# svg-gen 🎨

X（旧Twitter）投稿用の幾何学模様SVGを自動生成するPythonスクリプトです。
白背景 × ゴールド線スタイルをベースに、AIと一緒に作りました。

## 対応図形

| オプション | 模様 |
|-----------|------|
| hexagon   | 六角形タイリング |
| circle    | 同心円グリッド |
| triangle  | 三角形タイリング |
| grid      | 格子模様 |
| star      | 六芒星タイリング |

## カラープリセット

`gold` / `lightgold` / `deepgold` / `silver` / `white` / `rose`

## 使い方

```bash
# デフォルト（六角形・ゴールド）
python svg_gen.py

# オプション指定
python svg_gen.py --shape star --density 6 --color rose --rotate 30
動作環境
Python 3.x（標準ライブラリのみ）
Termux（Android）で動作確認済み
作者
@tomu_ai_dev
AIと協働するフリーランスAIエンジニアを目指して独学中。
