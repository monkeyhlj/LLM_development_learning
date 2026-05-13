# LLM_development_learning

Learning Demo Records：

*注：不同demo对应依赖环境可能有所不一样，都在对应demo的requirements文件中。*

Catalogue：

LangChain related - LLM_demo对应博客文档：[AI Agent开发课程笔记记录 - 基础篇-CSDN博客](https://blog.csdn.net/hhhmonkey/article/details/160315195?spm=1001.2014.3001.5501)

LangChain Advanced：[LangChain - V1.0-CSDN博客](https://blog.csdn.net/hhhmonkey/article/details/160770038?spm=1001.2014.3001.5501)

LangGraph Advanced：[基于LangGraph的Agent-CSDN博客](https://blog.csdn.net/hhhmonkey/article/details/160796006?spm=1001.2014.3001.5501)

RAG related - RAG_demo对应博客文档：[AI Agent开发课程笔记记录 - 提升篇 About RAG-CSDN博客](https://blog.csdn.net/hhhmonkey/article/details/160339585?spm=1001.2014.3001.5501)

Skills related - test-project对应博客文档：[OpenCode安装以及Agent skills使用测试-CSDN博客](https://blog.csdn.net/hhhmonkey/article/details/160363982?spm=1001.2014.3001.5501)

Skills Advanced - Agent_skills_demo：[Agent Skills简单理解-CSDN博客](https://blog.csdn.net/hhhmonkey/article/details/161026464?sharetype=blogdetail&sharerId=161026464&sharerefer=PC&sharesource=hhhmonkey&spm=1011.2480.3001.8118)

Project related - llm-developing-assistantgpt：still in progress...

**目录结构：**

```
LLM_development_learning/
├── .git/
├── .gitignore
├── README.md
├── Agent_skills_demo/
│   ├── demo1/
│   │   ├── .env
│   │   ├── langgraph.json
│   │   ├── main.py
│   │   ├── pyproject.toml
│   │   ├── readme.md
│   │   ├── requirements.txt
│   │   ├── skills/
│   │   │   └── example_skill/
│   │   │       ├── SKILL.md
│   │   │       └── scripts/
│   │   │           └── example_script.py
│   │   ├── src/
│   │   │   └── agent/
│   │   │       ├── __init__.py
│   │   │       ├── class_multi_agent.py
│   │   │       ├── class_skills_agent_backup.py
│   │   │       ├── class_skills_list_backup.py
│   │   │       ├── mcp_tool_config.py
│   │   │       ├── skills_agent.py
│   │   │       ├── skills_list.py
│   │   │       ├── logs/
│   │   │       ├── llm/
│   │   │       │   ├── __init__.py
│   │   │       │   ├── env_utils.py
│   │   │       │   ├── log_utils.py
│   │   │       │   └── my_llm.py
│   │   │       └── skills/
│   │   │           ├── README.md
│   │   │           ├── gaode_navigation/
│   │   │           │   └── SKILL.md
│   │   │           ├── railway_booking/
│   │   │           │   └── SKILL.md
│   │   │           └── weather_query/
│   │   │               ├── SKILL.md
│   │   │               └── scripts/
│   │   │                   └── fake_weather_service.py
│   │   └── tests/
│   │       └── test_skills_agent.py
│   └── demo2/
│       └── requirements.txt
├── LangChain/
│   ├── .env
│   ├── .idea/
│   ├── .langgraph_api/
│   ├── agent_env/
│   ├── langgraph.json
│   ├── pyproject.toml
│   ├── readme.md
│   ├── requirements.txt
│   ├── test.sql
│   ├── src/
│   │   ├── app.py
│   │   └── agent/
│   │       ├── my_agent1.py
│   │       ├── my_agent2.py
│   │       ├── my_agent3.py
│   │       ├── my_llm.py
│   │       ├── text_to_sql_agent.py
│   │       ├── logs/
│   │       ├── tools/
│   │       └── utils/
│   ├── static/
│   │   ├── script.js
│   │   └── style.css
│   └── templates/
│       └── chat.html
├── LangGraph/
│   ├── project1/
│   │   ├── .env
│   │   ├── agent_env/
│   │   ├── langgrapg01-入门和组件.ipynb
│   │   ├── langgraph02-构筑有记忆能恢复的智能体.ipynb
│   │   ├── langgraph03-人机协作与历史回溯.ipynb
│   │   ├── langgraph04-多智能体系统.ipynb
│   │   ├── requirements.txt
│   │   ├── checkpoints.db
│   │   ├── content_review.db
│   │   ├── content_review.db-shm
│   │   ├── content_review.db-wal
│   │   ├── personal_assistant.db
│   │   ├── personal_assistant.db-shm
│   │   ├── personal_assistant.db-wal
│   │   ├── pipeline.db
│   │   └── demo-agent/
│   │       └── ...
│   └── project2/
│       ├── .gitignore
│       ├── .idea/
│       ├── langgraph_demo/
│       ├── langgraph_test_venv/
│       └── readme.md
├── LLM_demo/
│   ├── 01_LLM.ipynb
│   ├── 02_LLM_local_ollama.ipynb
│   ├── 03_LangChain关键对象.ipynb
│   ├── 04_LangChain记忆系统.ipynb
│   ├── 05_LangChain文本嵌入.ipynb
│   ├── 06_LangChain工具封装与调用.ipynb
│   ├── city.csv
│   ├── requirements.txt
│   ├── 政策文件.txt
│   ├── agent_env/
│   ├── bge-small-zh-v1.5/            (Embedding模型文件)
│   │   └── ...
│   └── chromadb/                     (向量数据库)
│       └── ...
├── RAG_demo/
│   ├── .env
│   ├── agent_env/
│   ├── requirements.txt
│   ├── deepseek_faiss_搭建本地知识库检索.ipynb
│   ├── qwen-agent-multi-files.ipynb
│   ├── local_rag_chroma_db/          (向量数据库)
│   ├── docs/
│   │   ├── 各种资料文件txt，pdf等
│   ├── Internet_docs/
│   │   ├── Lecture 1 Overview.ipynb
│   │   ├── Lecture 2 Indexing.ipynb
│   │   ├── Lecture 3 Retrieval and generation.ipynb
│   │   ├── Lecture 4 Multi Query.ipynb
│   │   ├── Lecture 5 RAG-Fusion.ipynb
│   │   ├── lecture 6 Decomposition.ipynb
│   │   ├── Lecture 7 Step Back.ipynb
│   │   ├── Lecture 8 Hype.ipynb
│   │   ├── Lecture 9 Routing.ipynb
│   │   ├── Lecture 10 Query Structuring.ipynb
│   │   ├── Lecture 11 Multi-Reporesentation indexing.ipynb
│   │   ├── Lecture 12 PARPTOR.ipynb
│   │   ├── Lecture 13 ColBert.ipynb
│   │   ├── Lecture 14 Re-ranking.ipynb
│   │   ├── Lecture 15 CRAG.ipynb
│   │   ├── vectorEmbedding_and_similarity.ipynb
│   │   ├── 文本向量化.py
│   │   ├── 文档切割.ipynb
│   │   ├── RAG优化技巧.pdf
│   │   ├── RAG简易流程.pdf
│   │   └── 评估指标.pdf
│   ├── qwen_agent/
│   │   └── ...
│   └── workspace/
│       └── tools/
│           ├── doc_parser/
│           └── simple_doc_parser/
├── llm-developing-assistantgpt/
│   ├── app.py
│   ├── AssistantGPT.py
│   ├── config.py
│   ├── db_qdrant.py
│   ├── file_processor.py
│   ├── file_processor_helper.py
│   ├── utils.py
│   ├── requirements.txt
│   ├── README.md
│   └── assets/
│       └── ...
└── test-project/
    ├── .env
    ├── .gitignore
    ├── .venv/
    ├── index.html
    └── .opencode/
        ├── .gitignore
        ├── package-lock.json
        ├── package.json
        └── skills/
            ├── frontend-design/
            ├── server-status-check/
            ├── site-users-count/
            ├── skill-creator/
            └── xlsx/
```
