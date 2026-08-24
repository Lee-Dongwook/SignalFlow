import pytest
from kubernetes import client, config

@pytest.fixture(scope="module")
def k8s_client():
    config.load_kube_config()
    return client.CoreV1Api()

def test_k8s_cluster_health(k8s_client):
    """클러스터 노드 상태가 Ready인지 확인"""
    nodes = k8s_client.list_node()
    assert len(nodes.items) > 0
    for node in nodes.items:
        status = [c.type for c in node.status.conditions if c.type == 'Ready' and c.status == 'True']
        assert 'Ready' in status

def test_flink_jobmanager_pod_status(k8s_client):
    """JobManager Pod가 정상적으로 Running 상태로 올라왔는지 확인"""
    pods = k8s_client.list_namespaced_pod(namespace="default", label_selector="app=flink-jobmanager")
    assert len(pods.items) > 0
    assert pods.items[0].status.phase in ["Running", "Pending"]
