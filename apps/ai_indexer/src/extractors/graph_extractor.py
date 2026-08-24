import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

extract_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a Knowledge Graph Extractor. Extract Subject-Predicate-Object triples from the text.
Return ONLY a valid JSON array of objects with keys: 'subject', 'predicate', 'object', 'subject_type', 'object_type'."""),
    ("user", "Text: {text}")
])

def extract_triples(text:str):
    chain = extract_prompt | llm
    res = chain.invoke({"text": text})

    try:
        return json.loads(res.content.strip())
    except Exception:
        return []
