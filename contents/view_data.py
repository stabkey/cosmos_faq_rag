import streamlit as st
from azure.cosmos import CosmosClient
import os
from dotenv import load_dotenv
import pandas as pd

st.set_page_config(layout="wide")

# .envファイルから環境変数をロード
load_dotenv()

# CosmosDBの接続情報
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

# Streamlitアプリケーションの設定
st.title("CosmosDBデータ表示アプリ")
st.info("CosmosDBに登録されているデータを表示します。")

# CosmosDBからデータを取得
container = cosmos_database.get_container_client(select_container)
query = "SELECT c.category, c.question, c.answer, c.keywords FROM c"
items = container.query_items(
    query=query,
    enable_cross_partition_query=True
)

# データの表示
st.subheader("登録されているデータ:")

# 登録されているデータをデータフレームとして表示
df = pd.DataFrame(items)
st.dataframe(df)
