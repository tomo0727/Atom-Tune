# app.py
import os
import re
import json
import time
from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import openai
from tqdm import tqdm

# ---------- 設定 ----------
CSV_PATH = "datas/2024.csv"
CACHE_FILE = "descriptions_cache.json"
SENTENCE_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"  # 日本語対応で軽量
OPENAI_MODEL = "gpt-4o-mini"   # 利用可能なモデルに合わせて変更可
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # 必ず環境変数で設定
if not OPENAI_API_KEY:
    raise RuntimeError("環境変数 OPENAI_API_KEY を設定してください。")
openai.api_key = OPENAI_API_KEY

# ---------- Flask ----------
app = Flask(__name__)

# ---------- ユーティリティ: 音名→MIDI ----------
NOTE_MAP = {"C":0,"C#":1,"DB":1,"D":2,"D#":3,"EB":3,"E":4,"F":5,"F#":6,"GB":6,"G":7,"G#":8,"AB":8,"A":9,"A#":10,"BB":10,"B":11}
_note_pattern = re.compile(r"(?:low|mid|hi)?\s*(\d)?\s*([A-Ga-g])(#|♯|b|♭)?")

def normalize_note_str(s: str):
    if not isinstance(s, str) or not s.strip():
        return None
    s = s.strip()
    m = re.search(r"(low|mid|hi)?\s*(\d)\s*([A-Ga-g])(#|♯|b|♭)?", s)
    if m:
        prefix = m.group(1) or ""
        octave = int(m.group(2))
        note = m.group(3).upper()
        acc = m.group(4) or ""
        if acc in ("♯", "#"): acc = "#"
        if acc in ("♭", "b"): acc = "b"
        return f"{prefix}{octave}{note}{acc}"
    m2 = _note_pattern.search(s)
    if not m2:
        return None
    octave = m2.group(1) or "1"
    note = m2.group(2).upper()
    acc = m2.group(3) or ""
    if acc in ("♯", "#"): acc = "#"
    if acc in ("♭", "b"): acc = "b"
    return f"mid{octave}{note}{acc}"

def note_to_midi(note_str: str):
    s = normalize_note_str(note_str)
    if not s: return None
    m = re.search(r"(low|mid|hi)?(\d)([A-G])(#|b)?", s)
    if not m:
        return None
    prefix = m.group(1) or ""
    octave_digit = int(m.group(2))
    note = m.group(3)
    acc = m.group(4) or ""
    key = note + (acc if acc else "")
    key = key.replace("♯", "#").replace("♭", "b")
    if key not in NOTE_MAP:
        return None
    midi_octave = octave_digit + 3
    midi = 12 * midi_octave + NOTE_MAP[key]
    if prefix == "low":
        midi -= 12
    elif prefix == "hi":
        midi += 12
    return int(midi)

# ---------- キャッシュ ----------
def load_cache(path=CACHE_FILE):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(cache, path=CACHE_FILE):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

CACHE = load_cache()

# ---------- OpenAI による説明生成（キャッシュ付き） ----------
def describe_song_with_openai(title: str, artist: str, retries=2):
    key = f"{artist}___{title}"
    if key in CACHE:
        return CACHE[key]
    prompt = (
        f"あなたは音楽解説者です。日本語で短い一文（〜40文字程度）で答えてください。\n"
        f"曲名: 「{title}」\nアーティスト: {artist}\n"
        "この曲はどんな雰囲気（感情や場面、テンポの印象など）かを端的に表現してください。\n"
        "例: 「失恋の痛みを静かに綴る感動的なバラード。」"
    )
    for i in range(retries+1):
        try:
            resp = openai.ChatCompletion.create(
                model=OPENAI_MODEL,
                messages=[{"role":"user","content":prompt}],
                max_tokens=60,
                temperature=0.2
            )
            text = None
            if resp and "choices" in resp and len(resp["choices"])>0:
                choice = resp["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    text = choice["message"]["content"].strip()
                elif "text" in choice:
                    text = choice["text"].strip()
            text = text or "説明が取得できませんでした。"
            CACHE[key] = text
            # 余裕をもって保存（呼び出し後）
            save_cache(CACHE)
            time.sleep(0.15)
            return text
        except Exception as e:
            wait = (i+1)*1.0
            print(f"OpenAI error try {i+1}: {e}. wait {wait}s")
            time.sleep(wait)
    text = "説明を生成できませんでした。"
    CACHE[key] = text
    save_cache(CACHE)
    return text

# ---------- データ読み込み（アプリ起動時） ----------
def load_dataset(path=CSV_PATH):
    df = pd.read_csv(path, header=None, names=["タイトル","アーティスト","最低音","最高音","年代"])
    # MIDI 数値列
    df["min_midi"] = df["最低音"].apply(lambda x: note_to_midi(x) if pd.notna(x) else None)
    df["max_midi"] = df["最高音"].apply(lambda x: note_to_midi(x) if pd.notna(x) else None)
    df["年代"] = pd.to_numeric(df["年代"], errors="coerce")
    return df

DATA = load_dataset()

# ---------- ルート ----------
@app.route("/", methods=["GET"])
def index():
    # 提示用の雰囲気タグ例（自由に更新）
    mood_tags = ["切ない","爽やか","力強い","落ち着いた","アップテンポ","感動的","夜向け","明るい"]
    return render_template("index.html", moods=mood_tags)

@app.route("/recommend", methods=["POST"])
def recommend():
    # フォームから受け取り
    user_min_note = request.form.get("min_note", "mid1G").strip()
    user_max_note = request.form.get("max_note", "hiB").strip()
    year_min = int(request.form.get("year_min", 2010))
    year_max = int(request.form.get("year_max", 2024))
    # mood はタグ選択または自由入力（優先）
    mood_input = request.form.get("mood_input", "").strip()
    mood_select = request.form.get("mood_select", "").strip()
    user_mood = mood_input if mood_input else mood_select

    # 入力検証
    min_midi = note_to_midi(user_min_note)
    max_midi = note_to_midi(user_max_note)
    if min_midi is None or max_midi is None:
        return "音域の指定が解析できませんでした（例: mid1G 形式で指定）", 400

    # まず音域・年代でフィルタ
    mask = (
        (DATA["min_midi"].notna()) &
        (DATA["max_midi"].notna()) &
        (DATA["min_midi"] >= min_midi) &
        (DATA["max_midi"] <= max_midi) &
        (DATA["年代"].notna()) &
        (DATA["年代"] >= year_min) &
        (DATA["年代"] <= year_max)
    )
    filtered = DATA[mask].copy()
    if filtered.empty:
        return render_template("index.html", moods=[], error="条件に合う曲が見つかりませんでした。")

    # 各曲について説明（OpenAI → キャッシュ）
    descriptions = []
    for _, row in tqdm(filtered.iterrows(), total=len(filtered), desc="generate"):
        title = row["タイトル"]
        artist = row["アーティスト"]
        desc = describe_song_with_openai(title, artist)
        descriptions.append(desc)
    filtered["説明"] = descriptions

    # ベクトル化（sentence-transformers）
    model = SentenceTransformer(SENTENCE_MODEL)
    song_texts = filtered["説明"].tolist()
    song_emb = model.encode(song_texts, show_progress_bar=False)
    user_emb = model.encode([user_mood])

    sims = cosine_similarity(user_emb, song_emb)[0]
    filtered["類似度"] = sims
    result = filtered.sort_values("類似度", ascending=False).head(5)

    # 結果をテンプレートへ渡す
    results = result[["タイトル","アーティスト","年代","最低音","最高音","説明","類似度"]].to_dict(orient="records")
    return render_template("index.html", moods=[], results=results, prev={
        "min_note": user_min_note,
        "max_note": user_max_note,
        "year_min": year_min,
        "year_max": year_max,
        "user_mood": user_mood
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
