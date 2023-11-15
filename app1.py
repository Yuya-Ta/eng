import streamlit as st
import openai
import json
import pandas as pd
from dotenv import load_dotenv
import os

# Streamlitレイアウトのスタイルをカスタマイズ
st.set_page_config(page_title="英作文AI学習ツールβ", layout="wide")

# 環境変数の読み込み
load_dotenv()
data_json=None
# OpenAI APIの設定
openai.api_key = os.getenv("OPENAI_API_KEY")

# CSSスタイルを追加
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css") # CSSファイルをここに配置

def generate_topic():
    try:
        # ここにTopicを生成するためのプロンプトを記述
        prompt = "Generate an interesting topic for English composition practice.Please choose a random question from a wide range of questions."
        # 最大トークン数を設定（例: 20トークン）
        max_token = 20
        response_topic=openai.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
            {"role": "user", "content": prompt}               
        ],
        max_tokens=max_token
        )
        return response_topic.choices[0].message.content
    except Exception as e:
        print("An error occurred:", e)
        return None
    
def grade_essay(essay, topic):
    try:
        prompt = (
            f" Score the following English essay in Japanese, considering these:\n\n"
            "1. Scoring(in Japanese): Rate out of 100 based on:\n"
            "   - Content (25 pts): Does it include the required content (opinion, reasons)?\n"
            "   - Structure (25 pts): Is the essay's structure clear and logical?\n"
            "   - Vocabulary (25 pts): Is appropriate vocabulary used correctly?\n"
            "   - Grammar (25 pts): Variety and correctness of sentence structures.\n"
            "   and add total point\n\n"
            "2. Identify and correct grammatical errors in the essay (in Japanese).\n"
            "Display the English text before correction and the English text after correction.If the user's sentence is completely correct, output the word none for both before and after.\n\n"
            "3. Identify areas for content improvement (in Japanese).\n\n"
            "4. Correct and rewrite [Answer] accurately.120-150 words. Include word count (e.g., 122 words).(in English)\n\n"
            "[TOPIC]\n"
            f"'{topic}'\n"
            "[Answer]\n\n"
            f"'{essay}'\n\n"
            "[Output format]\n"
            "Please return the data as a JSON string in the following format.You must output in JSON format only. You are not allowed to output in any other format\n"
            '{{"scoring": {{"content": {{"score": integer, "comment": string}}, "structure": {{"score": integer, "comment": string}}, "vocabulary": {{"score": integer, "comment": string}}, "grammar": {{"score": integer, "comment": string}}, "total": {{"score": integer, "comment": string}}}}, "identifyAndCorrectGrammaticalErrors": {{"before": string, "after": string, "comment": string}}, "identifyContentImprovementAreas": {{"content": string}}, "correctAndRewrite": {{"content": string}}}}'
            "\n\n lang:ja"
            )
        max_token = 800
        response_answer=openai.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=[
             {
            "role": "system",
            "content": "You are a writing assessment expert.Please correct the English composition for Japanese student. Please output in JSON format."
            },
            {"role": "user", "content": prompt}               
        ],
        max_tokens=max_token,
        response_format={ "type": "json_object" }
        )
        return response_answer.choices[0].message.content
    except Exception as e:
        print("An error occurred:", e)
        return None

# Streamlitアプリのレイアウトとスタイリング
st.title("英作文AI学習ツールβ", anchor=None)
st.header('英作文のお題')
if 'topic' in st.session_state:
    st.subheader(st.session_state['topic'])
elif st.button("TOPICを生成する"):
    with st.spinner('お題生成中です。10秒待って生成されなければ再度ボタンを押してください。'):
        topic = generate_topic()
        st.session_state['topic'] = topic


# 最大文字数を定義
max_chars = 800
st.header('作成した英作文を入力する')
essay = st.text_area("以下のテキストエリアにお題に対する英作文を100wordを目安に記入してください。:", height=300)
if len(essay) > max_chars:
    st.warning(f"入力されたテキストは{len(essay)}文字です。{max_chars}文字以内で入力してください。")
    essay = essay[:max_chars]  # 最大文字数を超えた部分を削除

if st.button("英作文を添削する"):
        with st.spinner('添削中...60秒ほどお待ちください'):
            if essay and 'topic' in st.session_state:
                data_json = grade_essay(essay, st.session_state['topic'])
            else:
                st.error("まずはTOPICを生成してください。")

if data_json is not None:
    # Parse JSON
    data = json.loads(data_json)

    # Convert 'scoring' and 'identifyAndCorrectGrammaticalErrors' to DataFrame for tabular display
    scoring_df = pd.DataFrame(data['scoring']).T
    grammar_df = pd.DataFrame([data['identifyAndCorrectGrammaticalErrors']])

    # スタイリングされた表の表示
    def styled_table(df):
        return st.table(df.style.set_table_styles([{"selector": "th", "props": [("font-size", "16px")]}]))

    # スコアリングと文法的な誤りのセクションをスタイリングして表示
    st.header("採点")
    styled_table(scoring_df)

    st.header("文章内の修正点")
    styled_table(grammar_df)

    # その他のセクションの表示
    st.header("改善のためのアドバイス")
    st.write(data["identifyContentImprovementAreas"]["content"])

    st.header("模範解答例")
    st.write(data["correctAndRewrite"]["content"])
