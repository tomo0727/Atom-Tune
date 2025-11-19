from flask import Flask, render_template_string
import pandas as pd
import os

app = Flask(__name__)

# CSVファイルのパス
csv_path = r"C:\Users\tomo7\Geeksalon\product\scraping\merged.csv"

@app.route('/')
def index():
    if not os.path.exists(csv_path):
        return "<h2>❌ merged.csv が見つかりません。</h2>"

    # CSVを読み込み（ヘッダーなし想定）
    df = pd.read_csv(csv_path, header=None)

    # テーブルをHTML化
    table_html = df.to_html(classes='table table-striped table-bordered', index=False, header=False)

    # Bootstrapで見やすく整形
    html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <title>ボカロ音域データ一覧</title>
        <link rel="stylesheet"
              href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">
        <style>
            body {{
                background-color: #f8f9fa;
                padding: 30px;
            }}
            h1 {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .table {{
                background-color: white;
            }}
        </style>
    </head>
    <body>
        <h1>🎵 ボカロ音域データ一覧</h1>
        <div class="container">{table_html}</div>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == '__main__':
    app.run(debug=True)
