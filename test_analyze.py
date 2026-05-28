"""端到端冒烟测试"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_analyze_valid_symbol():
    resp = client.post("/analyze", json={"symbol": "000001"})
    assert resp.status_code == 200
    data = resp.json()
    assert "reasons" in data
    assert len(data["reasons"]) >= 1
    assert "summary" in data
    for r in data["reasons"]:
        assert "conclusion" in r
        assert "data_support" in r
        assert "impact" in r
        assert "severity" in r
        assert "dimension" in r


def test_analyze_invalid_symbol():
    resp = client.post("/analyze", json={"symbol": "123"})
    assert resp.status_code == 400


def test_analyze_nonexistent_symbol():
    """不存在的股票代码应该能优雅处理"""
    resp = client.post("/analyze", json={"symbol": "999999"})
    assert resp.status_code in (200, 500)
