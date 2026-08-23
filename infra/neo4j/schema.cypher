CREATE CONSTRAINT FOR (c:Company) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT FOR (e:Event) REQUIRE e.id IS UNIQUE;

// 그래프 관계 모델 예시: (Event)-[:MENTIONS]->(Company), (Event)-[:BELONGS_TO]->(Category)
