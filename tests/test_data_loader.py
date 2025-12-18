"""
Tests for the data loader module.

Run with: pytest tests/test_data_loader.py -v
"""

import pytest
from src.core.data import DataLoader, get_data_loader
from src.core.models import ForwardPlayer, DefensePlayer, Goalie, ForwardLineCombo, DefenseLineCombo


class TestDataLoader:
    """Test suite for DataLoader."""
    
    @pytest.fixture
    def loader(self):
        """Create a DataLoader instance."""
        return get_data_loader()
    
    def test_load_forwards(self, loader):
        """Test loading forward players."""
        forwards = loader.get_forwards()
        
        assert len(forwards) > 0, "Should load at least one forward"
        assert all(isinstance(p, ForwardPlayer) for p in forwards)
        
        # Check first player has required fields
        player = forwards[0]
        assert player.id is not None
        assert player.overall > 0
        assert player.team
        assert player.nationality
        assert player.event
    
    def test_load_defense(self, loader):
        """Test loading defense players."""
        defense = loader.get_defense()
        
        assert len(defense) > 0, "Should load at least one defense player"
        assert all(isinstance(p, DefensePlayer) for p in defense)
    
    def test_load_goalies(self, loader):
        """Test loading goalies."""
        goalies = loader.get_goalies()
        
        assert len(goalies) > 0, "Should load at least one goalie"
        assert all(isinstance(p, Goalie) for p in goalies)
    
    def test_load_forward_combos(self, loader):
        """Test loading forward line combinations."""
        combos = loader.get_forward_combos()
        
        assert len(combos) > 0, "Should load at least one forward combo"
        assert all(isinstance(c, ForwardLineCombo) for c in combos)
        
        # Check combo structure
        combo = combos[0]
        assert combo.id is not None
        assert combo.reward_amount >= 0
        assert combo.reward_type is not None
        assert len(combo.get_conditions()) == 3
    
    def test_load_defense_combos(self, loader):
        """Test loading defense line combinations."""
        combos = loader.get_defense_combos()
        
        assert len(combos) > 0, "Should load at least one defense combo"
        assert all(isinstance(c, DefenseLineCombo) for c in combos)
        
        # Check combo structure
        combo = combos[0]
        assert len(combo.get_conditions()) == 2
    
    def test_player_names_resolved(self, loader):
        """Test that player names are resolved from ID files."""
        forwards = loader.get_forwards()
        
        # At least some players should have names
        named_players = [p for p in forwards if p.first_name and p.last_name]
        assert len(named_players) > 0, "Some players should have resolved names"
    
    def test_filter_players_by_ovr(self, loader):
        """Test filtering players by minimum OVR."""
        forwards = loader.get_forwards()
        
        filtered = loader.filter_players(forwards, min_ovr=85)
        
        assert all(p.overall >= 85 for p in filtered)
        assert len(filtered) < len(forwards), "Filtering should reduce count"
    
    def test_filter_players_by_team(self, loader):
        """Test filtering players by team."""
        forwards = loader.get_forwards()
        
        filtered = loader.filter_players(forwards, team="DET")
        
        assert all(p.team.upper() == "DET" for p in filtered)
    
    def test_filter_players_excluded(self, loader):
        """Test excluding specific player IDs."""
        forwards = loader.get_forwards()
        
        # Get some IDs to exclude
        exclude_ids = [forwards[0].id, forwards[1].id]
        
        filtered = loader.filter_players(forwards, excluded_ids=exclude_ids)
        
        assert all(p.id not in exclude_ids for p in filtered)
    
    def test_player_matches_condition(self, loader):
        """Test player condition matching."""
        forwards = loader.get_forwards()
        player = forwards[0]
        
        # Should match own attributes
        assert player.matches_condition("team", player.team)
        assert player.matches_condition("nationality", player.nationality)
        assert player.matches_condition("event", player.event)
        
        # Should not match different values
        assert not player.matches_condition("team", "INVALID_TEAM")
    
    def test_get_stats(self, loader):
        """Test statistics generation."""
        stats = loader.get_stats()
        
        assert "players" in stats
        assert "combos" in stats
        assert "teams" in stats
        assert "nationalities" in stats
        
        assert stats["players"]["forwards"] > 0
        assert stats["combos"]["forward_combos"] > 0


class TestDataLoaderSingleton:
    """Test singleton behavior."""
    
    def test_same_instance(self):
        """Test that get_data_loader returns same instance."""
        loader1 = get_data_loader()
        loader2 = get_data_loader()
        
        # Should be the same cached instance
        assert loader1 is loader2

