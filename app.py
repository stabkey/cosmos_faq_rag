import streamlit as st

top_page = st.Page(page="contents/top_page.py", title="ホーム", icon="🏠")
cosmos_page = st.Page(page="contents/to_cosmosdb.py", title="データの登録", icon="🌎")
chat_page = st.Page(page="contents/chat_with_cosmosDB.py", title="DBと会話", icon="💬")
view_page = st.Page(page="contents/view_data.py" , title="データ表示", icon="👀")

pg = st.navigation([top_page, cosmos_page, chat_page, view_page])
pg.run()