import streamlit as st
from openai import AzureOpenAI
from azure.cosmos import CosmosClient
import os
from dotenv import load_dotenv

# .envファイルから環境変数をロード
load_dotenv()

st.set_page_config(layout="wide")

# Azure OpenAIの接続情報
azure_openai_client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"), 
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
    api_version="2024-10-21"
)

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

with st.sidebar:

    # コンテナを選択
    select_container = st.sidebar.selectbox("コンテナを選択してください。" ,container_list)
    
    container = cosmos_database.get_container_client(select_container)
    query = "SELECT DISTINCT VALUE c.category FROM c"
    categories = list(container.query_items(
        query=query, 
        enable_cross_partition_query=True
    ))

    select_category = st.sidebar.selectbox("カテゴリを選択してください", [""] + categories)

# Streamlitアプリケーションの設定
st.title("ベクトル検索アプリ")
st.info("Azure OpenAIとCosmosDBを使用したベクトル検索ツールです。")

# ユーザーの入力を受け取る
user_input = st.chat_input("検索キーワードを入力してください:")

# 会話履歴がない場合は初期化
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 会話履歴を表示
for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        st.write(chat["content"])

if user_input:

    with st.chat_message("user"):
        st.write(user_input)

    # Azure OpenAIを使ってベクトルを生成
    vector_query = azure_openai_client.embeddings.create(
        input=user_input,
        model="text-embedding-3-large"
    )

    filter_condition = []
    if select_category:
        filter_condition.append(f"c.category = '{select_category}'")
    
    filter_query = " AND ".join(filter_condition) if filter_condition else "1=1"

    context = ""
    search_result = []
    for item in container.query_items(
        query=f"""
        SELECT TOP 5 c.question, c.answer, c.marge_text, VectorDistance(c.vector_content,@embedding) AS SimilarityScore
        FROM c
        WHERE {filter_query}
        ORDER BY VectorDistance(c.vector_content,@embedding)
        """,
        parameters=[
        {"name": "@embedding", "value": vector_query.data[0].embedding}
        ],
        enable_cross_partition_query=True):

        if item["SimilarityScore"] > 0.3:
            context += f"検索結果: {item['marge_text']}\n\n"
            search_result.append(item)

    response = azure_openai_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"""
                ## タスク
                - ハルシネーションを防ぐためAIが持っている知識を使わないでください。
                - ユーザーからの問い合わせに対して、**必ず検索結果からのみ回答してください。**
                - 検索結果が空の場合は、「○○についての情報は見つかりませんでした。他にお探しの情報やご質問があれば、ぜひお知らせください」と回答してください。
                - 検索結果に該当する情報が見つからなかった場合は、「他にお探しの情報やご質問があれば、ぜひお知らせください」とお答えください。
                - 近い検索結果がある場合は、「○○」についての情報は「△△」にあります。と回答してください。
                - リンクなども維持して出力してください。
                
                ## 検索結果
                \n{context}
                """
            },
            {
                "role": "user",
                "content": user_input
            }
        ],
        model="gpt-4o-mini",
        temperature=0.5,
    )
    
    with st.chat_message("assistant"):
        st.markdown(response.choices[0].message.content)
    
    # 会話履歴に追加
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_input
    })
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": response.choices[0].message.content
    })

    # サイドバーに検索結果を表示
    with st.sidebar:
        st.subheader("検索結果:")
        for result in search_result:
            with st.expander(f"Q: {result['question']}"):
                st.html(f"A: {result['answer']}")
                st.write(f"スコア: {result['SimilarityScore']}")