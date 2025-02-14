import streamlit as st

st.title("Top Page")
st.info("Cosmos DB にデータを登録し、会話するアプリケーションです。")
st.markdown(
    """
    ## 使い方
    1. 左のサイドバーから`データの登録`をクリックして、データを登録します。
    2. `DBと会話`をクリックして、Cosmos DBに登録したデータと会話します。
    3. `データ表示`をクリックして、登録済みのデータを表示します。
    """
)