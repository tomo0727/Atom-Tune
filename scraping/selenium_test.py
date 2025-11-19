from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

#Chromeドライバオプションを設定
chrome_options = Options()
chrome_options.add_argument('--headless') #ヘッドレスモードで起動

# Chromeドライバを自動インストールして起動
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# 指定したURLのページを開く
url = 'https://news.yahoo.co.jp'
driver.get(url)

# ページをスクロールしてデータを読み込む
SCROLL_PAUSE_TIME = 2  # スクロールの待機時間
scroll_count = 3  # スクロール回数

# ページの高さを取得
last_height = driver.execute_script('return document.body.scrollHeight')

# スクロールを繰り返す
for _ in range(scroll_count):
    # ページをスクロール
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
    # ページが読み込まれるまで待機
    time.sleep(SCROLL_PAUSE_TIME)
    # 新しい高さを取得
    new_height = driver.execute_script('return document.body.scrollHeight')
    # 高さが変わっていなければ終了
    if new_height == last_height:
        break
    last_height = new_height

# スクロール後のページのソースコードを取得
html = driver.page_source

# スクレイピングしたHTMLをBeautiful Soupで解析
soup = BeautifulSoup(html, 'html.parser')

# 特定の要素を抽出
titles = soup.select('title')
for title in titles:
    print(title.text)
    

# ドライバを終了
driver.quit()
