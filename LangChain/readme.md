pip install langchain langchain-openai dotenv ipykernel

pip install --upgrade "langgraph-cli[inmem]"

pip install -e .

langgraph dev

---

pip install sqlalchemy psycopg2-binary loguru

langgraph dev --allow-blocking

---
fastapi添加文件结构：
```commandline
project/
├── src/
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── my_llm.py
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   └── text_to_sql_tools.py
│   │   └── utils/
│   │       └── db_utils.py
│   └── app.py
├── templates/
│   └── chat.html
├── static/
│   ├── style.css
│   └── script.js
├── .env
└── requirements.txt
```

