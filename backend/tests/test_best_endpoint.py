"""
Tests for the /best endpoint (Goal 1 results API).

Run with: pytest tests/test_best_endpoint.py -v
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.core.data import get_results_store


client = TestClient(app)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_run():
    """Create a sample Goal 1 run with data for testing."""
    store = get_results_store()
    
    # Create a test run
    run_id = store.create_run(
        position_type="forward",
        optimization_mode="ovr",
        parameters={"k": 200, "test": True},
    )
    
    # Add some Stage A results
    store.store_stage_a_result(run_id, 1, [1, 5, 12], gain_ovr=6)
    
    # Add some concrete lines (using real player IDs from the database)
    # We'll use IDs that should exist in the test database
    store.store_concrete_line(
        run_id=run_id,
        player_ids=[1, 2, 3],  # First 3 forwards
        activated_combo_ids=[1, 5],
        total_ovr=270,
        total_salary=15000000.0,
        ranking_score=276.0,
    )
    store.store_concrete_line(
        run_id=run_id,
        player_ids=[4, 5, 6],
        activated_combo_ids=[12],
        total_ovr=265,
        total_salary=14000000.0,
        ranking_score=267.0,
    )
    
    yield run_id
    
    # Cleanup
    store.delete_run(run_id)


@pytest.fixture
def empty_run():
    """Create an empty run (no lines) for testing edge cases."""
    store = get_results_store()
    
    run_id = store.create_run(
        position_type="defense",
        optimization_mode="sal",
        parameters={"test": True},
    )
    
    yield run_id
    
    store.delete_run(run_id)


# =============================================================================
# LIST RUNS TESTS
# =============================================================================

class TestListRuns:
    """Tests for GET /best/runs"""
    
    def test_list_runs_empty(self):
        """Returns empty list when no runs exist for a filter."""
        response = client.get("/best/runs?position_type=defense&optimization_mode=ovr_sal_ap")
        
        assert response.status_code == 200
        data = response.json()
        assert "runs" in data
        assert isinstance(data["runs"], list)
    
    def test_list_runs_with_data(self, sample_run):
        """Returns runs when data exists."""
        response = client.get("/best/runs?position_type=forward&optimization_mode=ovr")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["runs"]) >= 1
        
        # Find our test run
        test_runs = [r for r in data["runs"] if r["id"] == sample_run]
        assert len(test_runs) == 1
        assert test_runs[0]["position_type"] == "forward"
        assert test_runs[0]["optimization_mode"] == "ovr"
    
    def test_list_runs_limit(self, sample_run):
        """Respects limit parameter."""
        response = client.get("/best/runs?limit=1")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["runs"]) <= 1


# =============================================================================
# GET BEST LINES TESTS
# =============================================================================

class TestGetBestLines:
    """Tests for GET /best/{pos}/{mode}"""
    
    def test_get_best_lines_success(self, sample_run):
        """Successfully returns best lines with player details."""
        response = client.get("/best/forward/ovr")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["position_type"] == "forward"
        assert data["optimization_mode"] == "ovr"
        assert "run" in data
        assert "lines" in data
        assert data["total_lines"] >= 1
    
    def test_get_best_lines_with_player_details(self, sample_run):
        """Lines include enriched player information."""
        response = client.get("/best/forward/ovr?limit=1")
        
        assert response.status_code == 200
        data = response.json()
        
        if data["lines"]:
            line = data["lines"][0]
            assert "players" in line
            assert "activated_combo_ids" in line
            assert "total_ovr" in line
            assert "ranking_score" in line
            
            # Check player details
            if line["players"]:
                player = line["players"][0]
                assert "id" in player
                assert "first_name" in player
                assert "last_name" in player
                assert "overall" in player
                assert "team" in player
    
    def test_get_best_lines_empty_result(self):
        """Returns empty lines when no results exist."""
        # Use a mode that likely has no results
        response = client.get("/best/defense/ovr_sal_ap")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        # Either no run or no lines
        assert data["total_lines"] == 0 or data["run"] is None
    
    def test_get_best_lines_invalid_position(self):
        """Returns 400 for invalid position type."""
        response = client.get("/best/goalie/ovr")
        
        assert response.status_code == 400
        assert "Invalid position" in response.json()["detail"]
    
    def test_get_best_lines_invalid_mode(self):
        """Returns 400 for invalid optimization mode."""
        response = client.get("/best/forward/invalid")
        
        assert response.status_code == 400
        assert "Invalid optimization mode" in response.json()["detail"]
    
    def test_get_best_lines_pagination(self, sample_run):
        """Supports pagination with limit and offset."""
        # Get first page
        response1 = client.get("/best/forward/ovr?limit=1&offset=0")
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Get second page
        response2 = client.get("/best/forward/ovr?limit=1&offset=1")
        assert response2.status_code == 200
        data2 = response2.json()
        
        # If we have 2+ lines, they should be different
        if data1["lines"] and data2["lines"]:
            assert data1["lines"][0]["id"] != data2["lines"][0]["id"]
    
    def test_get_best_lines_specific_run(self, sample_run):
        """Can query a specific run by ID."""
        response = client.get(f"/best/forward/ovr?run_id={sample_run}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["run"]["id"] == sample_run
    
    def test_get_best_lines_wrong_run_type(self, sample_run):
        """Returns 400 when run_id doesn't match requested pos/mode."""
        # sample_run is forward/ovr, request defense/ovr
        response = client.get(f"/best/defense/ovr?run_id={sample_run}")
        
        assert response.status_code == 400
        assert "not" in response.json()["detail"].lower()
    
    def test_get_best_lines_nonexistent_run(self):
        """Returns 404 for non-existent run ID."""
        response = client.get("/best/forward/ovr?run_id=999999")
        
        assert response.status_code == 404


# =============================================================================
# SUMMARY ENDPOINT TESTS
# =============================================================================

class TestGetSummary:
    """Tests for GET /best/{pos}/{mode}/summary"""
    
    def test_summary_with_data(self, sample_run):
        """Returns summary when data exists."""
        response = client.get("/best/forward/ovr/summary")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["has_results"] is True
        assert data["position_type"] == "forward"
        assert data["optimization_mode"] == "ovr"
        assert "run" in data
        assert "total_lines" in data
        assert "top_scores" in data
    
    def test_summary_no_data(self):
        """Returns has_results=False when no data exists."""
        response = client.get("/best/defense/ovr_sal_ap/summary")
        
        assert response.status_code == 200
        data = response.json()
        
        # Either has_results is False or total_lines is 0
        if not data["has_results"]:
            assert data["run"] is None
    
    def test_summary_invalid_params(self):
        """Returns 400 for invalid parameters."""
        response = client.get("/best/invalid/ovr/summary")
        assert response.status_code == 400


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """End-to-end integration tests."""
    
    def test_full_workflow(self, sample_run):
        """Test the full workflow: list runs -> get lines."""
        # 1. List runs
        runs_response = client.get("/best/runs?position_type=forward")
        assert runs_response.status_code == 200
        runs = runs_response.json()["runs"]
        
        # Find our test run
        test_run = next((r for r in runs if r["id"] == sample_run), None)
        assert test_run is not None
        
        # 2. Get summary
        summary_response = client.get(f"/best/forward/ovr/summary?run_id={sample_run}")
        assert summary_response.status_code == 200
        summary = summary_response.json()
        assert summary["total_lines"] >= 1
        
        # 3. Get detailed lines
        lines_response = client.get(f"/best/forward/ovr?run_id={sample_run}")
        assert lines_response.status_code == 200
        lines_data = lines_response.json()
        
        assert len(lines_data["lines"]) == summary["total_lines"]
