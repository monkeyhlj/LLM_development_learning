pip install langchain langchain-openai dotenv ipykernel

pip install --upgrade "langgraph-cli[inmem]"

pip install -e .

langgraph dev

---

pip install sqlalchemy psycopg2-binary loguru

langgraph dev --allow-blocking
