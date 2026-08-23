## SignalFlow 인프라 구축 : 대규모 스트리밍 파이프라인 과정 이해 및 트러블 슈팅

### Introduction

2년차 프론트엔드 엔지니어이자, 최근에 프로덕트 엔지니어로 포지션을 확장하는 시점에서 UI와 상태 관리를 주로 다뤄왔습니다.
최근 AI Agent와 LLM RAG 기반 서비스를 다루면서 **데이터 파이프라인 인프라** 관련한 개념 확보가 필요함을 느꼈습니다.

프론트엔드 측에서 사용자에게 제공하는 인터랙션, 스트리밍 UI 구현만으로 UX 개선의 한계점이 있음과,
**Downstream 데이터 파이프라인**의 품질과 **Latency(지연 시간)** 이 UX 안정화에 큰 축을 담당한다는 사실을 파악했습니다.

### Flink TaskManger 메모리 : State TTL과 Rocks DB의 존재 이유

#### [문제 상황]

뉴스 API와 웹 스크랩퍼를 통해 유입되는 raw 스트림 데이터를 다루는 과정에서, 네트워크 재시도나 수집기 이중 실행이 발생할 수 있습니다.
이 경우, 동일한 `event_id`를 가진 중복 데이터가 유입될 수 있고, 실제 측정해본 결과 약 12% 가량 유입됨을 확인했습니다.

본 데이터들이 그대로 **ElasticSearch(Vector DB)**로 넘어간다면, RAG 검색 시 동일 뉴스 문서가 상위 컨텍스트를 도배하는 **중복 인덱스 오염 문제**가 발생하게 됩니다.

#### [해결 과정]

##### 상용 관리형 서비스 (e.g. **Redis**, **AWS Kinesis Analytics**) 대신에 **Flink SQL** 을 사용해본 이유

처음 문제를 해결하고자 할때 Managed Flink나 Redis 기반의 Deduplication을 생각해봤습니다.
하지만 Redis를 두고 초당 수천~수만건의 Read/Write I/O가 발생하는 환경에 놓인다면 네트워크 Latency와 DB 비용 부담이 커질거로 예상했습니다.

스트림 엔진 내부 메모리 상에서 **Event-Time Window 기반 중복 제거**를 처리해보는 방법이 수십 밀리초(ms) 지연 시간 이내에 수행되며 여러 비용 부담을 줄일 수 있는 해결책으로 생각해봤습니다.

```sql
INSERT INTO deduplicated_events
SELECT event_id, source, category, content, ts
FROM(
    SELECT *, ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY ts ASC) as row_num
    FROM raw_events
) WHERE row_num = 1

```

초기에는 다음과 같은 쿼리문을 생각하여 로컬 테스트에는 성공했지만, 실 애플리케이션 구동을 해보니 문제가 발생했습니다.

Flink TaskManager의 Pod가 `java.lang.OutOfMemoryError: Java heap Space` 오류를 명시하며, CrashLoopBackOff 현상이 나타났습니다.

여기서 원인을 생각해보면, 기본적으로 스트림 처리는 무한히 흘러가는 데이터입니다.
Flink가 중복 여부를 판단하라면 이전에 유입된 이벤트 id를 메모리(State) 등에 기억해야 합니다.
`State TTL (유효 기간)` 을 지정하지 않았다보니, 유입되는 모든 Key값들이 JVM Heap 메모리에 쌓이다 결국 한계에 닿았던 문제였습니다.

##### State TTL 제어 및 RocksDB Backend 전환

State TTL을 우선 기본 1시간으로 설정하여 이전에 들어온 Key들을 State에서 자동으로 삭제하도록 수명 주기를 지정했습니다.

```
t_env.get_config().get_configuration().set_string("table.exec.state.ttl", "1h")

```

또한, 혹여나 State TTL 설정만으로 해결이 불가능한 수에 대비하여, JVM Heap 메모리의 한계를 극복하기 위해 메모리와 디스크를 적절히 활용하는 C++ 기반 RocksDB로 State를 변경했었습니다.
