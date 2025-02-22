## 環境変数の設定

1. ルートに`.env`ファイルを作成します。
2. `sample.env`の内容を貼り付けます。
3. Azure OpneAI のキーとエンドポイントはリソースから確認します。
    - Azure OpenAI のリソースにアクセスします。
    - 左のナビゲーションから、「キーとエンドポイント」を選択します。
    - `AZURE_OPENAI_API_KEY`は「キー 1」または、「キー 2」の値に書き換えます。
    - `AZURE_OPENAI_ENDPOINT`ば、「エンドポイント」の値に書き換えます。
4. Cosmos DB の情報はリソースから確認します。
    - Azure Portal から、作成したCosmosDB にアクセスします。
    - 左のナビゲーションから、「設定」>「キー」を選択します。
    - `COSMOSDB_ENDPOINT` は「URI」の値に書き換えます。
    -  `COSMOSDB_KEY` は「PRIMARY KEY」または、「SECONDARY KEY」の値に書き換えます。
    - `COSMOSDB_DATABASE_NAME` は、作成したデータベースの名前に書き換えます。
        - Cosmos DB のリソース名ではなく、データベースの名前になります。

## 手順

Python の仮想環境の作成と有効化

```shell
python -m venv .venv
.venv\Scripts\activate
```

必要なライブラリのインストール

```shell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

アプリの実行

```shell
streamlit run app.py
```