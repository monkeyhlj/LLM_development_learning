# LLM_development_learning

Learning Demo Records：

注：不同demo对应依赖环境可能有所不一样，都在对应demo的requirements文件中。

Catalogue：

LangChain related - LLM_demo对应博客文档：[AI Agent开发课程笔记记录 - 基础篇-CSDN博客](https://blog.csdn.net/hhhmonkey/article/details/160315195?spm=1001.2014.3001.5501)

LangChain Advanced：still in progress...

LangGraph Advanced：still in progress...

RAG related - RAG_demo对应博客文档：[AI Agent开发课程笔记记录 - 提升篇 About RAG-CSDN博客](https://blog.csdn.net/hhhmonkey/article/details/160339585?spm=1001.2014.3001.5501)

Skills related - test-project对应博客文档：[OpenCode安装以及Agent skills使用测试-CSDN博客](https://blog.csdn.net/hhhmonkey/article/details/160363982?spm=1001.2014.3001.5501)

Skills Advanced - Agent_skills_demo：still in progress...

Project related - llm-developing-assistantgpt：still in progress...

*后续有时间就会陆续更新。。。*

目录结构：
```
LLM_development_learning/
├── .gitignore
├── README.md
├── Agent_skills_demo/
│   └── test.ipynb
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
│   ├── agent_env/                    (虚拟环境, 已忽略内容)
│   ├── bge-small-zh-v1.5/            (Embedding模型文件, 已忽略内容)
│   └── chromadb/                     (向量数据库, 已忽略内容)
├── LangChain/
│   └── test.ipynb
├── LangGraph/
│   ├── project1/
│   │   ├── langgrapg01-入门和组件.ipynb
│   │   ├── langgraph02-构筑有记忆能恢复的智能体.ipynb
│   │   ├── langgraph03-人机协作.ipynb
│   │   ├── requirements.txt
│   │   ├── agent_env/                (虚拟环境, 已忽略内容)
│   │   ├── checkpoints.db
│   │   ├── personal_assistant.db
│   │   └── pipeline.db
│   └── project2/
│       └── test.ipynb
├── RAG_demo/
│   ├── .env
│   ├── requirements.txt
│   ├── deepseek_faiss_搭建本地知识库检索.ipynb
│   ├── qwen-agent-multi-files.ipynb
│   ├── agent_env/                    (虚拟环境, 已忽略内容)
│   ├── local_rag_chroma_db/          (向量数据库, 已忽略内容)
│   ├── docs/
│   │   ├── 各种PDF及TXT文件
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
│   │   ├── vector_embedding_and_similarity.ipynb
│   │   ├── 文本向量化.py
│   │   ├── 文档切割.ipynb
│   │   ├── RAG优化技巧.pdf
│   │   ├── RAG简易流程.pdf
│   │   └── 评估指标.pdf
│   ├── qwen_agent/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── log.py
│   │   ├── multi_agent_hub.py
│   │   ├── settings.py
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── article_agent.py
│   │   │   ├── assistant.py
│   │   │   ├── dialogue_retrieval_agent.py
│   │   │   ├── dialogue_simulator.py
│   │   │   ├── doc_qa/
│   │   │   ├── fncall_agent.py
│   │   │   ├── group_chat.py
│   │   │   ├── group_chat_auto_router.py
│   │   │   ├── group_chat_creator.py
│   │   │   ├── human_simulator.py
│   │   │   ├── keygen_strategies/
│   │   │   ├── memo_assistant.py
│   │   │   ├── react_chat.py
│   │   │   ├── router.py
│   │   │   ├── tir_agent.py
│   │   │   ├── user_agent.py
│   │   │   ├── virtual_memory_agent.py
│   │   │   ├── write_from_scratch.py
│   │   │   └── writing/
│   │   ├── gui/
│   │   │   ├── __init__.py
│   │   │   ├── gradio_dep.py
│   │   │   ├── gradio_utils.py
│   │   │   ├── utils.py
│   │   │   ├── web_ui.py
│   │   │   └── assets/
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── azure.py
│   │   │   ├── base.py
│   │   │   ├── function_calling.py
│   │   │   ├── fncall_prompts/
│   │   │   ├── oai.py
│   │   │   ├── openvino.py
│   │   │   ├── qwen_dashscope.py
│   │   │   ├── qwenomni_oai.py
│   │   │   ├── qwenaudio_dashscope.py
│   │   │   ├── qwenvl_dashscope.py
│   │   │   ├── qwenvl_oai.py
│   │   │   ├── schema.py
│   │   │   └── transformers_llm.py
│   │   ├── memory/
│   │   │   ├── __init__.py
│   │   │   ├── es_memory.py
│   │   │   └── memory.py
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── code_interpreter.py
│   │   │   ├── doc_parser.py
│   │   │   ├── es_retrieval.py
│   │   │   ├── es_vector_retrieval.py
│   │   │   ├── extract_doc_vocabulary.py
│   │   │   ├── image_gen.py
│   │   │   ├── mcp_manager.py
│   │   │   ├── python_executor.py
│   │   │   ├── retrieval.py
│   │   │   ├── search_tools/
│   │   │   ├── simple_doc_parser.py
│   │   │   ├── storage.py
│   │   │   ├── web_extractor.py
│   │   │   ├── web_search.py
│   │   │   ├── resource/
│   │   │   └── amap_weather.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── output_beautify.py
│   │   │   ├── parallel_executor.py
│   │   │   ├── str_processing.py
│   │   │   ├── tokenization_qwen.py
│   │   │   ├── utils.py
│   │   │   └── qwen.tiktoken
│   │   └── note/
│   │       └── base_explained.md
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
│       ├── DjangoBook2.0中文版.pdf
│       ├── chatGPT 入门指南.pdf
│       └── img.png
└── test-project/
    ├── .env
    ├── .gitignore
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
