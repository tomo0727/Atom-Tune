import os
import pandas as pd

# CSVが保存されているディレクトリ
input_dir = r"C:\Users\tomo7\Geeksalon\product\scraping"
output_path = os.path.join(input_dir, "merged.csv")

# すべてのCSVファイルを取得
csv_files = [f for f in os.listdir(input_dir) if f.startswith("table_") and f.endswith(".csv")]

# CSVを順に読み込んで結合
df_list = []
for file in csv_files:
    path = os.path.join(input_dir, file)
    df = pd.read_csv(path, header=None)
    df_list.append(df)

# 縦方向に結合（ignore_index=Trueで連番に）
merged_df = pd.concat(df_list, ignore_index=True)

# 保存
merged_df.to_csv(output_path, index=False, encoding='utf-8-sig')

print(f"✅ 結合完了！: {output_path}")
