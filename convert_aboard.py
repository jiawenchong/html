# -*- coding: utf-8 -*-
"""
convert_aboard.py

用途：
  把 sample.json（GitHub 上那份）轉成可以直接餵給 aboard.html 的
  data/building_aboard.json。

要解決的兩個問題：
  1.  \n 問題：
      sample.json 的每個值（K27P2 / xiao / RW）其實是「被字串化兩次」的 JSON，
      整段被當成字串存起來，所以裡面塞滿了跳脫字元 \n。
      => 用 json.loads 把字串再解析一次，就能還原成真正的巢狀 JSON 物件。

  2.  標題（key）對不上的問題：
      sample.json 的最上層是 K27P2 / xiao / RW 這種「分組外殼」，
      但 aboard.html 只認得 result.progress 底下的專案名稱
      （例如 "K27-P2 建廠計劃"、"FAB 5 Plan" ...）。
      原本的 aboard.json 沒有 xiao 這種外層標題，
      => 把三個外殼底下的 progress 全部「攤平 / 合併」成同一個 result.progress。
"""

import json
import argparse


def load_and_unescape(path):
    """讀取 sample.json，並把每個被字串化的值還原成 JSON 物件（解決 \\n 問題）。"""
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)            # 第一層解析：拿到 { "K27P2": "<字串>", ... }

    sections = {}
    for wrapper_key, value in raw.items():
        if isinstance(value, str):
            # 第二層解析：把塞滿 \n 的字串還原成真正的物件
            sections[wrapper_key] = json.loads(value)
        else:
            # 已經是物件就直接使用
            sections[wrapper_key] = value
    return sections


def merge_sections(sections, br=False):
    """把 K27P2 / xiao / RW 各自的 result.progress 合併成單一 result.progress。"""
    merged_progress = {}
    report_date = None

    for wrapper_key, obj in sections.items():
        result = obj.get("result", {}) if isinstance(obj, dict) else {}

        # 取報告日期（各區塊都一樣，取第一個即可）
        if report_date is None:
            report_date = result.get("report_date")

        progress = result.get("progress", {}) or {}
        for project_name, items in progress.items():
            if project_name in merged_progress:
                # 萬一不同外殼出現同名專案，就把項目接在一起
                merged_progress[project_name].extend(items)
            else:
                merged_progress[project_name] = list(items)

    # 選用：把欄位內容真正的換行 \n 轉成 <br>，
    # 讓多行的 PROGRESS 在 aboard.html 的表格裡能正確斷行顯示。
    if br:
        for items in merged_progress.values():
            for item in items:
                for field, val in item.items():
                    if isinstance(val, str):
                        item[field] = val.replace("\n", "<br>")

    return {"result": {"report_date": report_date, "progress": merged_progress}}


def main():
    parser = argparse.ArgumentParser(description="把 sample.json 轉成 aboard.html 用的 building_aboard.json")
    parser.add_argument("-i", "--input", default="sample.json", help="來源檔（預設 sample.json）")
    parser.add_argument("-o", "--output", default="data/building_aboard.json", help="輸出檔（預設 data/building_aboard.json）")
    parser.add_argument("--br", action="store_true", help="把內文的 \\n 換行轉成 <br>（讓表格能正確斷行）")
    args = parser.parse_args()

    sections = load_and_unescape(args.input)
    merged = merge_sections(sections, br=args.br)

    import os
    out_dir = os.path.dirname(args.output)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    # 簡單回報
    keys = list(merged["result"]["progress"].keys())
    print(f"[OK] 已輸出：{args.output}")
    print(f"[OK] report_date：{merged['result']['report_date']}")
    print(f"[OK] 合併後的專案（共 {len(keys)} 個）：")
    for k in keys:
        print(f"      - {k}（{len(merged['result']['progress'][k])} 筆）")


if __name__ == "__main__":
    main()
