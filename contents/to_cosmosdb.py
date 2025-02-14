import streamlit as st
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import json
import uuid
from azure.cosmos import CosmosClient
import pandas as pd
import tiktoken

load_dotenv()

output_format = {
    "type": "function",
    "function": {
        "name": "keywords",
        "description": "入力されたデータを分析し、詳細にデータを分類します。",
        "parameters": {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "array",
                    "description": "データの内容に関連するキーワードを記載します。",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "required": ["keywords"]
        }
    }
}

st.set_page_config(layout="wide")

# CosmosDBの接続情報を環境変数から取得
cosmos_endpoint = os.getenv("COSMOSDB_ENDPOINT")
cosmos_key = os.getenv("COSMOSDB_KEY")
cosmos_database_name = os.getenv("COSMOSDB_DATABASE_NAME")

# CosmosDBクライアントを作成
cosmos_client = CosmosClient(cosmos_endpoint, cosmos_key)
cosmos_database = cosmos_client.get_database_client(cosmos_database_name)

# コンテナ一覧の取得
containers = list(cosmos_database.list_containers())

container_list = []
for container in containers:
    container_list.append(container["id"])

# Azure OpenAIのクライアントを作成
azure_openai_client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-10-21"
)

select_container = st.sidebar.selectbox(
    "CosmosDBのコンテナを選択",
    container_list
)

# トークナイザーを初期化
tokenizer = tiktoken.get_encoding("cl100k_base")

cosmos_container = cosmos_database.get_container_client(select_container)

# タブの作成
tab1, tab2 = st.tabs(["フォームで登録", "CSVで登録"])

with tab1:
    st.title("Cosmos DBに登録（フォーム）")
    st.info("フォームに入力された情報をベクトル化してCosmos DBに登録します。")

    with st.form("input_form"):
        question = st.text_input("質問")
        answer = st.text_area("回答")
        category = st.text_input("カテゴリ")
        submit_button = st.form_submit_button(label="ベクトル化して登録")

    marge_text = f"## 質問\n{question}\n\n## 回答\n{answer}"
    if submit_button:
        # キーワードを生成
        response = azure_openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "ユーザーが入力した内容から、キーワード10~15個程度抽出してください。"},
                {"role": "user", "content": marge_text}
            ],
            tools=[output_format],
            temperature=0.3,
            max_tokens=128000,
            max_completion_tokens=128000
        )

        result = response.choices[0].message.tool_calls[0].function.arguments
        data = json.loads(result)
        keywords = data["keywords"]

        # ベクトル化
        vector_content = azure_openai_client.embeddings.create(
            input=marge_text,
            model="text-embedding-3-large"
        )

        # データをCosmos DBに登録
        item = {
            "id": str(uuid.uuid4()),
            "is_searchable": True,
            "category": category,
            "question": question,
            "answer": answer,
            "marge_text": marge_text,
            "keywords": keywords,
            "vector_content": vector_content.data[0].embedding,
        }

        try:
            cosmos_container.create_item(body=item)
            st.success("データがCosmosDBに登録されました!")
        except Exception as e:
            st.error("データの登録に失敗しました: " + str(e))

with tab2:
    st.title("Cosmos DBに登録（CSV）")
    st.info("CSVファイルをアップロードしてデータをCosmos DBに登録します。")

    # サンプルのCSVファイルを形式を表示
    sample_csv = pd.DataFrame({
        "question": ["質問1", "質問2", "質問3"],
        "answer": ["回答1", "回答2", "回答3"],
        "category": ["カテゴリ1", "カテゴリ2","カテゴリ3"]
    })
    st.write("以下の形式でCSVファイルをアップロードしてください。")
    st.write(sample_csv)

    uploaded_file = st.file_uploader("CSVファイルをアップロード", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write(df)

        if st.button("データを登録"):
            for index, row in df.iterrows():

                # 質問と回答をマージ
                question_text = row["question"]
                answer_text = row["answer"]

                marge_text = f"## 質問\n{question_text}\n\n## 回答\n{answer_text}"

                response = azure_openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "ユーザーが入力した内容から、キーワード10~15個程度抽出してください。"},
                        {"role": "user", "content": marge_text}
                    ],
                    tools=[output_format],
                    temperature=0.3
                )

                result = response.choices[0].message.tool_calls[0].function.arguments
                data = json.loads(result)
                keywords = data["keywords"]

                vector_content = azure_openai_client.embeddings.create(
                    input=marge_text,
                    model="text-embedding-3-large",
                )

                item = {
                    "id": str(uuid.uuid4()),
                    "is_searchable": True,
                    "category": row["category"],
                    "question": question_text,
                    "answer": answer_text,
                    "marge_text": marge_text,
                    "keywords": keywords,
                    "vector_content": vector_content.data[0].embedding,
                }

                tokens = tokenizer.encode(marge_text)
                token_count = len(tokens)

                try:
                    cosmos_container.create_item(body=item)
                    # 何行目のデータが何トークンで登録されたか表示
                    st.write(f"{index + 1}行目のデータが{token_count}トークンで登録されました。")

                except Exception as e:
                    st.error("データの登録に失敗しました: " + str(e))
                    st.write(f"{index + 1}行目のデータが{token_count}トークンで登録できませんでした。")

            st.success("CSVファイルのデータがCosmosDBに登録されました!")