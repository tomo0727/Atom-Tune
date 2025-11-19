import csv
import requests
from bs4 import BeautifulSoup
import os

url = "https://w.atwiki.jp/saikouon_dokoda/pages/472.html"
headers = {"User-Agent": "Mozilla/5.0"}
res = requests.get(url, headers=headers)
res.encoding = "utf-8"
soup = BeautifulSoup(res.text, "html.parser")

tables = soup.find_all("table")

output_dir = r"C:\Users\tomo7\Geeksalon\product\scraping"
os.makedirs(output_dir, exist_ok=True)

count = 0

for tab in tables:
    class_names = tab.get("class", [])
    # "atwiki_table_color" を含むすべてのテーブルを対象
    if "atwiki_table_color" in class_names:
        count += 1
        output_path = os.path.join(output_dir, f"table_{count}.csv")

        with open(output_path, "w", encoding='utf-8', newline="") as file:
            writer = csv.writer(file)
            rows = tab.find_all("tr")
            for row in rows:
                csvRow = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                writer.writerow(csvRow)

        print(f"✅ {output_path} を作成しました")

print(f"完了: {count} 個のテーブルを保存しました。")
