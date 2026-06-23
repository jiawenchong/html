import json
import os
import subprocess

def clean_text(text):
    if not text: return ""
    return str(text).replace('\n', '<br>').replace('"', '&quot;')

def generate_notes_report():
    # 預設讀取正式環境的網路磁碟路徑；若不存在則退回腳本所在目錄的本機檔案，
    # 讓這支程式在本機也能直接吃下 building_aboard.json
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidate_paths = [
        r"\\10.10.51.67\d$\FAC_Web\agent_platform\html_files\data\building_aboard.json",
        os.path.join(base_dir, "building_aboard.json"),
        os.path.join(base_dir, "data", "building_aboard.json"),
    ]
    json_path = next((p for p in candidate_paths if os.path.exists(p)), None)
    if not json_path:
        print("❌ 找不到 JSON 檔案，已嘗試以下路徑：")
        for p in candidate_paths:
            print(f"   - {p}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    res = data.get("result", {})
    report_date = res.get("report_date", "--")
    progress_data = res.get("progress", {})
    BUILDING_ORDER = ["K27-P2", "KL I", "FAB 5", "RW", "KL II", "楠電", "K18B", "Zone3", "K3B"]

    # 先依 BUILDING_ORDER 對應 JSON key（保留排序與顯示名稱），
    # 再把沒被對應到的 key 補在後面，確保 building_aboard.json 內所有專案
    # 都會被渲染（即使標題與設定不一致，例如「桃電 前期規劃&建廠計劃」也不會漏掉）
    used_keys = set()
    groups = []  # (顯示名稱, JSON key)
    for b_target in BUILDING_ORDER:
        matched_key = next(
            (k for k in progress_data.keys()
             if k not in used_keys and b_target in k
             and not (b_target == "KL I" and "KL II" in k)),
            None
        )
        if matched_key:
            used_keys.add(matched_key)
            groups.append((b_target, matched_key))
    for k in progress_data.keys():
        if k not in used_keys:
            groups.append((k, k))

    rows_html = ""
    for b_target, matched_key in groups:
        items = progress_data[matched_key]
        row_count = len(items)
        
        for i, item in enumerate(items):
            pm = clean_text(item.get("PM_NAME", "-"))
            task = clean_text(item.get("TASK", "-"))
            comment = clean_text(item.get("PROGRESS", ""))
            ai_summary = clean_text(item.get("SUMMARY", ""))
            ai_reasonable = clean_text(item.get("REASONABLE", ""))
            
            ai_font_color = "#16a34a"
            ai_bg_color = "#f8fafc"
            summary_font_color = "#64748b"
            
            if "不合理" in ai_reasonable:
                ai_font_color = "#dc2626"
                ai_bg_color = "#fce8e6"
                summary_font_color = "#7f1d1d"
            elif "提醒" in ai_reasonable:
                ai_font_color = "#ffffff"
                ai_bg_color = "#64748b"
                summary_font_color = "#f1f5f9"

            indicator = item.get("INDICATOR", "")
            if "紅" in indicator or "黃" in indicator:
                status_text = "Delay"
                status_color = "#dc2626"
            elif "綠" in indicator:
                status_text = "On Time"
                status_color = "#16a34a"
            else:
                status_text = clean_text(indicator) if indicator else "-"
                status_color = "#475569"
            
            building_bg = "#f1f5f9"

            rows_html += f"""
            <tr>
                {f'<td align="center" bgcolor="{building_bg}" rowspan="{row_count}" style="border:1px solid #cbd5e1;"><b><font size="3">{b_target}</font></b></td>' if i == 0 else ''}
                <td align="center" style="border:1px solid #cbd5e1;"><font size="3"><b>{pm}</b></font></td>
                <td style="border:1px solid #cbd5e1;"><font size="3"><b>{task}</b></font></td>
                <td align="center" style="border:1px solid #cbd5e1;">
                    <b><font size="3" color="{status_color}">{status_text}</font></b>
                </td>
                <td style="border:1px solid #cbd5e1;"><font size="3" color="#475569">{comment}</font></td>
                <td bgcolor="{ai_bg_color}" style="border:1px solid #cbd5e1;">
                    <font size="1" color="#94a3b8">AI ANALYSIS</font><br>
                    <b><font size="3" color="{ai_font_color}">{ai_reasonable}</font></b><br>
                    <font size="2" color="{summary_font_color}">{ai_summary}</font>
                </td>
            </tr>"""

    full_html = f"""
    <html>
    <head><meta http-equiv="Content-Type" content="text/html; charset=big5"></head>
    <body style="background-color:#F5F5F3; margin:0; padding:20px;">
        <table width="100%" border="0" cellpadding="0" cellspacing="0" style="border-bottom:3px solid #0f172a;">
            <tr>
                <td style="padding-bottom:10px;">
                    <font size="6" color="#1e293b"><i><b>建廠@Board Review Agent</b></i></font><br>
                    <font size="2" color="#64748b"><b>Powered by AI Agent - Pensieve</b></font>
                </td>
                <td align="right" valign="middle" style="padding-bottom:10px;">
                    <div style="padding:8px 15px; display:inline-block; white-space:nowrap;">
                        <font size="6" color="#000000"><b>{report_date}</b></font>
                    </div>
                </td>
            </tr>
        </table>
        <br>
        <table width="100%" border="1" cellpadding="10" cellspacing="0" style="border-collapse:collapse; background-color:#ffffff; border:1px solid #cbd5e1;">
            <tr bgcolor="#f8fafc">
                <th width="10%"><font color="#475569" size="2">Building</font></th>
                <th width="10%"><font color="#475569" size="2">PM</font></th>
                <th width="22%"><font color="#475569" size="2">Task</font></th>
                <th width="8%"><font color="#475569" size="2">進度狀態</font></th>
                <th width="25%"><font color="#475569" size="2">Comment</font></th>
                <th width="25%"><font color="#475569" size="2">AI Analysis</font></th>
            </tr>
            {rows_html}
        </table>
    </body>
    </html>
    """

    single_line = "".join(line.strip() for line in full_html.splitlines())
    try:
        final_bytes = single_line.encode('big5', errors='ignore')
        process = subprocess.Popen(['clip'], stdin=subprocess.PIPE, shell=True)
        process.communicate(input=final_bytes)
        print("✅ 成功！報告已複製，日期欄位已修正為橫向排列。")
    except Exception as e:
        print(f"❌ 複製失敗: {e}")

if __name__ == "__main__":
    generate_notes_report()
