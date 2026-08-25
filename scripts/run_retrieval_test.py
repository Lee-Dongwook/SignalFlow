from apps.retrieval.pipeline import AdvancedGraphRAGPipeline

def main():
    print("Advanced GraphRAG Retrieval Test")
    pipeline = AdvancedGraphRAGPipeline()

    dummy_query = "Kafka 연동 장애 발생"
    dummy_vector = [0.01] * 768

    result = pipeline.run(query_text=dummy_query, query_vector=dummy_vector, candidate_k=5, final_top_n=2)

    print("\n[Retrieval 결과]")
    print(f"- 쿼리: {result['query']}")
    print(f"- Rerank된 최상위 문서 수: {len(result['documents'])}")
    for doc in result['documents']:
        print(f"  * ID: {doc['event_id']} | Score: {doc['rerank_score']:.4f} | Payload: {doc['payload'][:40]}...")

    print(f"- 추출된 지식 그래프 관계 수: {len(result['graph_context'])}")
    for rel in result['graph_context']:
        print(f"  * Graph Context: {rel}")

if __name__ == "__main__":
    main()
