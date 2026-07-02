"""
svg_gen.py - 幾何学模様SVG自動生成スクリプト
白背景 × ゴールド線スタイル（X投稿用）

使い方（従来のテンプレートモード）:
  python svg_gen.py
  python svg_gen.py --shape hexagon --density 5 --color gold --rotate 30
  python svg_gen.py --shape circle --density 8 --output my_svg.svg
  python svg_gen.py --shape triangle --density 4 --stroke-width 1.5

使い方（AIモード / Claude Sonnet 5がデザインを決定）:
  export ANTHROPIC_API_KEY=sk-ant-...
  python svg_gen.py --ai --prompt "秋の夕暮れ、温かみのあるゴールド"
  python svg_gen.py --ai --prompt "静謐な冬の朝、シルバーと白の対比" --output winter.svg
"""

import argparse
import json
import math
import os
import sys
import urllib.error
import urllib.request


# ===== カラープリセット =====
COLOR_PRESETS = {
    "gold":        "#D4AF37",
    "lightgold":   "#F0D060",
    "deepgold":    "#B8860B",
    "silver":      "#C0C0C0",
    "white":       "#FFFFFF",
    "rose":        "#C8A08A",
}


def hex_points(cx, cy, r, rotate_deg=0):
    """六角形の頂点リストを返す"""
    points = []
    for i in range(6):
        angle = math.radians(60 * i + rotate_deg)
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        points.append((x, y))
    return points


def polygon_str(points):
    return " ".join(f"{x:.3f},{y:.3f}" for x, y in points)


# ===== 形状生成関数 =====

def generate_hexagon(width, height, density, stroke_color, stroke_width, rotate):
    """六角形タイリング"""
    elements = []
    r = min(width, height) / (density * 2.2)
    h_spacing = r * 1.732
    v_spacing = r * 1.5

    rows = int(height / v_spacing) + 2
    cols = int(width / h_spacing) + 2

    for row in range(-1, rows + 1):
        for col in range(-1, cols + 1):
            cx = col * h_spacing + (h_spacing / 2 if row % 2 else 0)
            cy = row * v_spacing
            pts = hex_points(cx, cy, r * 0.9, rotate)
            elements.append(
                f'<polygon points="{polygon_str(pts)}" '
                f'fill="none" stroke="{stroke_color}" stroke-width="{stroke_width:.2f}"/>'
            )
    return elements


def generate_circle(width, height, density, stroke_color, stroke_width, rotate):
    """同心円 + グリッド配置"""
    elements = []
    spacing = min(width, height) / (density + 1)
    rings = 3

    cols = int(width / spacing) + 2
    rows = int(height / spacing) + 2

    for row in range(-1, rows + 1):
        for col in range(-1, cols + 1):
            cx = col * spacing
            cy = row * spacing
            for k in range(1, rings + 1):
                r = spacing * 0.45 * (k / rings)
                elements.append(
                    f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r:.3f}" '
                    f'fill="none" stroke="{stroke_color}" stroke-width="{stroke_width:.2f}"/>'
                )
    return elements


def generate_triangle(width, height, density, stroke_color, stroke_width, rotate):
    """三角形タイリング"""
    elements = []
    size = min(width, height) / (density * 1.5)
    h = size * math.sqrt(3) / 2

    cols = int(width / size) + 3
    rows = int(height / h) + 3

    for row in range(-1, rows + 1):
        for col in range(-1, cols + 1):
            x0 = col * size - (size / 2 if row % 2 else 0)
            y0 = row * h
            # 上向き三角
            pts_up = [
                (x0, y0 + h),
                (x0 + size / 2, y0),
                (x0 + size, y0 + h),
            ]
            # 下向き三角
            pts_down = [
                (x0 + size / 2, y0),
                (x0 + size, y0 + h),
                (x0 + size * 1.5, y0),
            ]
            for pts in [pts_up, pts_down]:
                # rotate適用
                cx = sum(p[0] for p in pts) / 3
                cy = sum(p[1] for p in pts) / 3
                rad = math.radians(rotate)
                rotated = [
                    (
                        cx + (p[0] - cx) * math.cos(rad) - (p[1] - cy) * math.sin(rad),
                        cy + (p[0] - cx) * math.sin(rad) + (p[1] - cy) * math.cos(rad),
                    )
                    for p in pts
                ]
                elements.append(
                    f'<polygon points="{polygon_str(rotated)}" '
                    f'fill="none" stroke="{stroke_color}" stroke-width="{stroke_width:.2f}"/>'
                )
    return elements


def generate_grid(width, height, density, stroke_color, stroke_width, rotate):
    """格子（グリッド）模様"""
    elements = []
    spacing = min(width, height) / (density * 2)

    cols = int(width / spacing) + 2
    rows = int(height / spacing) + 2

    for col in range(-1, cols + 1):
        x = col * spacing
        elements.append(
            f'<line x1="{x:.3f}" y1="-10" x2="{x:.3f}" y2="{height + 10}" '
            f'stroke="{stroke_color}" stroke-width="{stroke_width:.2f}"/>'
        )
    for row in range(-1, rows + 1):
        y = row * spacing
        elements.append(
            f'<line x1="-10" y1="{y:.3f}" x2="{width + 10}" y2="{y:.3f}" '
            f'stroke="{stroke_color}" stroke-width="{stroke_width:.2f}"/>'
        )

    # 斜め格子（rotateで角度）
    if rotate != 0:
        diag_spacing = spacing * 1.414
        for i in range(-cols, cols + rows + 2):
            x1 = i * diag_spacing
            elements.append(
                f'<line x1="{x1:.3f}" y1="-10" '
                f'x2="{x1 + height + 20:.3f}" y2="{height + 10}" '
                f'stroke="{stroke_color}" stroke-width="{stroke_width * 0.5:.2f}" opacity="0.4"/>'
            )

    return elements


def generate_star(width, height, density, stroke_color, stroke_width, rotate):
    """星形（六芒星）タイリング"""
    elements = []
    r_outer = min(width, height) / (density * 2.5)
    r_inner = r_outer * 0.4
    spacing = r_outer * 2.2

    cols = int(width / spacing) + 2
    rows = int(height / spacing) + 2

    for row in range(-1, rows + 1):
        for col in range(-1, cols + 1):
            cx = col * spacing + (spacing / 2 if row % 2 else 0)
            cy = row * spacing
            pts = []
            for i in range(12):
                angle = math.radians(30 * i + rotate)
                r = r_outer if i % 2 == 0 else r_inner
                pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
            elements.append(
                f'<polygon points="{polygon_str(pts)}" '
                f'fill="none" stroke="{stroke_color}" stroke-width="{stroke_width:.2f}"/>'
            )
    return elements


SHAPES = {
    "hexagon":  generate_hexagon,
    "circle":   generate_circle,
    "triangle": generate_triangle,
    "grid":     generate_grid,
    "star":     generate_star,
}


# ===== レイヤー描画 & SVG組み立て =====

def render_layer(shape, width, height, density, color, stroke_width, rotate):
    """1レイヤー分の要素を生成する（プリセット色名 or #RRGGBB 両対応）"""
    stroke_color = COLOR_PRESETS.get(color, color)
    gen_func = SHAPES.get(shape)
    if gen_func is None:
        raise ValueError(shape)
    return gen_func(width, height, density, stroke_color, stroke_width, rotate)


def build_svg(width, height, layer_groups, comment=None):
    """(elements, opacity) のリストから最終的なSVG文字列を組み立てる"""
    svg_lines = []
    if comment:
        safe_comment = comment.replace("--", "―")
        svg_lines.append(f'<!-- {safe_comment} -->')

    svg_lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
    )
    svg_lines.append(f'  <rect width="{width}" height="{height}" fill="white"/>')
    svg_lines.append('  <clipPath id="clip">')
    svg_lines.append(f'    <rect width="{width}" height="{height}"/>')
    svg_lines.append('  </clipPath>')

    for elements, opacity in layer_groups:
        svg_lines.append(f'  <g clip-path="url(#clip)" opacity="{opacity:.2f}">')
        svg_lines.extend(f'    {el}' for el in elements)
        svg_lines.append('  </g>')

    svg_lines.append('</svg>')
    return "\n".join(svg_lines)


# ===== SVG生成メイン（テンプレートモード） =====

def generate_svg(shape, width, height, density, color, stroke_width, rotate, output):
    try:
        elements = render_layer(shape, width, height, density, color, stroke_width, rotate)
    except ValueError:
        print(f"[ERROR] 未対応の形状: {shape}")
        print(f"使用可能: {', '.join(SHAPES.keys())}")
        sys.exit(1)

    stroke_color = COLOR_PRESETS.get(color, color)
    svg_content = build_svg(width, height, [(elements, 1.0)])

    with open(output, "w", encoding="utf-8") as f:
        f.write(svg_content)

    print(f"[OK] SVG生成完了: {output}")
    print(f"     形状={shape}, 密度={density}, 色={stroke_color}, 回転={rotate}°, サイズ={width}x{height}")


# ===== AIモード（Claude Sonnet 5がデザインを決定） =====

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-5"

AI_SYSTEM_PROMPT = f"""あなたはSVG幾何学模様のアートディレクターです。
白背景 × ゴールド系ラインを基調とした、X（旧Twitter）投稿用パターンのデザイン仕様を考えます。

利用可能な形状: {', '.join(SHAPES.keys())}
色は #RRGGBB 形式で指定してください。白背景に映える上品な配色を基本としつつ、
与えられたテーマの雰囲気（季節・時間帯・感情など）に応じて調整してください。

出力は必ず以下のJSON形式のみとしてください。前置き・説明文・Markdownのコードブロック記法は一切不要です。

{{
  "concept": "デザインコンセプトの一言説明（日本語、30文字程度）",
  "layers": [
    {{"shape": "hexagon", "density": 5, "color": "#D4AF37", "stroke_width": 1.2, "rotate": 0, "opacity": 1.0}}
  ]
}}

layersは1〜2個。2個の場合は、ベースとなる模様に、別形状・別色・低めのopacityのアクセント模様を
重ねることで奥行きを出してください。density は 2〜10 程度、stroke_width は 0.5〜2.5 程度が目安です。
"""


def call_claude(prompt, model, api_key):
    body = json.dumps({
        "model": model,
        "max_tokens": 1000,
        "system": AI_SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        print(f"[ERROR] Claude API呼び出しに失敗しました ({e.code}): {detail}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"[ERROR] ネットワークエラー: {e}")
        sys.exit(1)

    text_blocks = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
    raw_text = "".join(text_blocks).strip()

    # Markdownのコードブロックで囲まれて返ってきた場合の保険
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        print("[ERROR] Claudeの応答をJSONとして解析できませんでした:")
        print(raw_text)
        sys.exit(1)


def generate_svg_ai(prompt, width, height, output, model):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[ERROR] 環境変数 ANTHROPIC_API_KEY が設定されていません。")
        print("        例: export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    print(f"[INFO] Claude ({model}) にデザインを相談中... テーマ: {prompt}")
    design = call_claude(prompt, model, api_key)

    concept = design.get("concept", "")
    layers = design.get("layers", [])
    if not layers:
        print("[ERROR] Claudeの応答にlayersが含まれていませんでした。")
        sys.exit(1)

    layer_groups = []
    for layer in layers:
        shape = layer.get("shape", "hexagon")
        try:
            elements = render_layer(
                shape=shape,
                width=width,
                height=height,
                density=layer.get("density", 5),
                color=layer.get("color", "gold"),
                stroke_width=layer.get("stroke_width", 1.2),
                rotate=layer.get("rotate", 0),
            )
        except ValueError:
            print(f"[WARN] Claudeが未対応の形状を指定したためスキップ: {shape}")
            continue
        layer_groups.append((elements, layer.get("opacity", 1.0)))

    if not layer_groups:
        print("[ERROR] 有効なレイヤーが1つも生成できませんでした。")
        sys.exit(1)

    svg_content = build_svg(width, height, layer_groups, comment=concept)

    with open(output, "w", encoding="utf-8") as f:
        f.write(svg_content)

    print(f"[OK] AI生成SVG完了: {output}")
    print(f"     コンセプト: {concept}")
    for layer in layers:
        print(
            f"     - {layer.get('shape')}: 色={layer.get('color')}, "
            f"密度={layer.get('density')}, 回転={layer.get('rotate')}°, "
            f"不透明度={layer.get('opacity', 1.0)}"
        )


# ===== CLI =====

def main():
    parser = argparse.ArgumentParser(
        description="幾何学模様SVG自動生成スクリプト（白背景×ゴールド線 / AIモード対応）"
    )
    parser.add_argument(
        "--shape", "-s",
        default="hexagon",
        choices=list(SHAPES.keys()),
        help=f"形状の種類 (default: hexagon) [{', '.join(SHAPES.keys())}]"
    )
    parser.add_argument(
        "--density", "-d",
        type=int,
        default=5,
        help="模様の密度・繰り返し数 (default: 5)"
    )
    parser.add_argument(
        "--color", "-c",
        default="gold",
        help=f"線の色 プリセット or #RRGGBB (default: gold) [{', '.join(COLOR_PRESETS.keys())}]"
    )
    parser.add_argument(
        "--stroke-width", "-w",
        type=float,
        default=1.2,
        dest="stroke_width",
        help="線の太さ (default: 1.2)"
    )
    parser.add_argument(
        "--rotate", "-r",
        type=float,
        default=0,
        help="回転角度（度） (default: 0)"
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1200,
        help="SVG幅px (default: 1200)"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=675,
        help="SVG高さpx (default: 675, X投稿推奨サイズ)"
    )
    parser.add_argument(
        "--output", "-o",
        default="output.svg",
        help="出力ファイル名 (default: output.svg)"
    )
    parser.add_argument(
        "--ai",
        action="store_true",
        help="Claude APIにデザイン仕様（形状・色・密度・回転・重ね合わせ）を決めさせるAIモード"
    )
    parser.add_argument(
        "--prompt", "-p",
        type=str,
        default=None,
        help="AIモード用のテーマ・プロンプト（例: '秋の夕暮れ、温かみのあるゴールド'）"
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"AIモードで使用するモデル (default: {DEFAULT_MODEL})"
    )

    args = parser.parse_args()

    if args.ai:
        if not args.prompt:
            print("[ERROR] --ai モードには --prompt でテーマを指定してください。")
            print('        例: python svg_gen.py --ai --prompt "秋の夕暮れ、温かみのあるゴールド"')
            sys.exit(1)
        generate_svg_ai(
            prompt=args.prompt,
            width=args.width,
            height=args.height,
            output=args.output,
            model=args.model,
        )
    else:
        generate_svg(
            shape=args.shape,
            width=args.width,
            height=args.height,
            density=args.density,
            color=args.color,
            stroke_width=args.stroke_width,
            rotate=args.rotate,
            output=args.output,
        )


if __name__ == "__main__":
    main()
