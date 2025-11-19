from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import csv
import os
import time

# ====== ① ChromeDriverの自動セットアップ ======
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# ====== ② ページを開く ======
url = "https://w.atwiki.jp/saikouon_dokoda/pages/472.html"
driver.get(url)

# ページの内容が完全に読み込まれるまで少し待つ
time.sleep(3)

# ====== ③ ページのHTMLを取得 ======
html = driver.page_source
soup = BeautifulSoup(html, "html.parser")

# ====== ④ 出力フォルダを作成 ======
output_dir = r"C:\Users\tomo7\Geeksalon\product\scraping"
os.makedirs(output_dir, exist_ok=True)

# ====== rowspanを展開する関数 ======
def expand_rowspan_table(table):
    rows = table.find_all("tr")
    expanded = []
    rowspan_map = {}  # {(行番号, 列番号): (残り行数, 値)}

    for row_idx, tr in enumerate(rows):
        cells = tr.find_all(['td', 'th'])
        expanded_row = []
        col_idx = 0

        # まず、上のrowspanセルを埋める
        while (row_idx, col_idx) in rowspan_map:
            expanded_row.append(rowspan_map[(row_idx, col_idx)][1])
            rowspan_map[(row_idx, col_idx)] = (rowspan_map[(row_idx, col_idx)][0] - 1,
                                               rowspan_map[(row_idx, col_idx)][1])
            # 残り行数が0なら削除
            if rowspan_map[(row_idx, col_idx)][0] <= 0:
                del rowspan_map[(row_idx, col_idx)]
            col_idx += 1

        # 現在のセルを処理
        for cell in cells:
            text = cell.get_text(strip=True)
            rowspan = int(cell.get("rowspan", 1))

            expanded_row.append(text)

            # rowspanセルを記録
            if rowspan > 1:
                for r in range(1, rowspan):
                    rowspan_map[(row_idx + r, col_idx)] = (rowspan - r, text)

            col_idx += 1

        expanded.append(expanded_row)

    return expanded


# ====== ⑤ テーブルを抽出 ======
tables = soup.find_all("table")

count = 0

# ====== ⑥ 各テーブルをCSVに保存 ======
for tab in tables:
    class_names = tab.get("class", [])
    if "atwiki_table_color" in class_names:
        count += 1
        output_path = os.path.join(output_dir, f"table_{count}.csv")

        # rowspan展開
        expanded_table = expand_rowspan_table(tab)

        # CSVに保存
        with open(output_path, "w", encoding='utf-8-sig', newline="") as file:
            writer = csv.writer(file)
            writer.writerows(expanded_table)

        print(f"✅ {output_path} を作成しました")

# ====== ⑦ 結果を出力 ======
print(f"完了: {count} 個のテーブルを保存しました。")

# ====== ⑧ 終了 ======
driver.quit()
