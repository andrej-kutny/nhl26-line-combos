"""
Player models for NHL 26 Line Combos Optimizer.

Contains base and specific player type models (forwards, defense, goalies).
"""

from pydantic import BaseModel, Field


class PlayerBase(BaseModel):
    """Base model for all player types with common attributes."""
    # Identity
    id: int = Field(..., description="Database auto-increment ID (unique per card)")
    player_id: int = Field(..., description="Player ID (shared across multiple cards)")
    
    # Names (resolved from lookup tables)
    first_name: str = Field("", description="Player's first name")
    last_name: str = Field("", description="Player's last name")
    
    # Card attributes
    img: str = Field(..., description="Card image filename")
    event: str = Field(..., description="Card event/release type (e.g., ICON, HH, CAP)")
    nationality: str = Field(..., description="Player nationality")
    league: str = Field(..., description="League (NHL, NHLAA, etc.)")
    team: str = Field(..., description="Team abbreviation")
    
    # Physical attributes
    weight: float = Field(..., description="Weight in kg")
    height: int = Field(..., description="Height in cm")
    salary: float = Field(..., description="Salary cost")
    overall: int = Field(..., ge=1, le=99, description="Overall rating (OVR)")
    
    @property
    def full_name(self) -> str:
        """Return player's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def matches_condition(self, condition_type: str, condition_key: str) -> bool:
        """
        Check if player matches a line combo condition.
        
        This method is crucial for ASP integration - it determines
        which players can activate which line combinations.
        
        Args:
            condition_type: One of "team", "nationality", "event"
            condition_key: The value to match (e.g., "DET", "CANADA", "ICON")
            
        Returns:
            True if the player matches the condition
        """
        condition_type = condition_type.lower()
        condition_key = condition_key.upper()
        
        if condition_type == "team":
            return self.team.upper() == condition_key
        elif condition_type == "nationality":
            return self.nationality.upper() == condition_key
        elif condition_type == "event":
            return self.event.upper() == condition_key
        return False


class ForwardPlayer(PlayerBase):
    """Forward player with offensive stats."""
    position: str = Field(..., description="Specific position: C, LW, or RW")
    
    # Offensive stats
    deking: int = Field(..., ge=1, le=99)
    hand_eye: int = Field(..., ge=1, le=99)
    passing: int = Field(..., ge=1, le=99)
    puck_control: int = Field(..., ge=1, le=99)
    slap_shot_accuracy: int = Field(..., ge=1, le=99)
    slap_shot_power: int = Field(..., ge=1, le=99)
    wrist_shot_accuracy: int = Field(..., ge=1, le=99)
    wrist_shot_power: int = Field(..., ge=1, le=99)
    
    # Skating stats
    acceleration: int = Field(..., ge=1, le=99)
    agility: int = Field(..., ge=1, le=99)
    balance: int = Field(..., ge=1, le=99)
    endurance: int = Field(..., ge=1, le=99)
    speed: int = Field(..., ge=1, le=99)
    
    # Awareness & defensive stats
    discipline: int = Field(..., ge=1, le=99)
    off_awareness: int = Field(..., ge=1, le=99)
    def_awareness: int = Field(..., ge=1, le=99)
    faceoffs: int = Field(..., ge=1, le=99)
    shot_blocking: int = Field(..., ge=1, le=99)
    stick_checking: int = Field(..., ge=1, le=99)
    
    # Physical stats
    aggression: int = Field(..., ge=1, le=99)
    body_checking: int = Field(..., ge=1, le=99)
    durability: int = Field(..., ge=1, le=99)
    fighting_skill: int = Field(..., ge=1, le=99)
    strength: int = Field(..., ge=1, le=99)


class DefensePlayer(PlayerBase):
    """Defense player with defensive stats."""
    position: str = Field(..., description="Specific position: LD or RD")
    
    # Offensive stats (same as forwards)
    deking: int = Field(..., ge=1, le=99)
    hand_eye: int = Field(..., ge=1, le=99)
    passing: int = Field(..., ge=1, le=99)
    puck_control: int = Field(..., ge=1, le=99)
    slap_shot_accuracy: int = Field(..., ge=1, le=99)
    slap_shot_power: int = Field(..., ge=1, le=99)
    wrist_shot_accuracy: int = Field(..., ge=1, le=99)
    wrist_shot_power: int = Field(..., ge=1, le=99)
    
    # Skating stats
    acceleration: int = Field(..., ge=1, le=99)
    agility: int = Field(..., ge=1, le=99)
    balance: int = Field(..., ge=1, le=99)
    endurance: int = Field(..., ge=1, le=99)
    speed: int = Field(..., ge=1, le=99)
    
    # Awareness & defensive stats
    discipline: int = Field(..., ge=1, le=99)
    off_awareness: int = Field(..., ge=1, le=99)
    def_awareness: int = Field(..., ge=1, le=99)
    faceoffs: int = Field(..., ge=1, le=99)
    shot_blocking: int = Field(..., ge=1, le=99)
    stick_checking: int = Field(..., ge=1, le=99)
    
    # Physical stats
    aggression: int = Field(..., ge=1, le=99)
    body_checking: int = Field(..., ge=1, le=99)
    durability: int = Field(..., ge=1, le=99)
    fighting_skill: int = Field(..., ge=1, le=99)
    strength: int = Field(..., ge=1, le=99)


class Goalie(PlayerBase):
    """Goalie player with goalie-specific stats."""
    position: str = Field(default="G", description="Always G")
    
    # Goalie-specific stats
    passing: int = Field(..., ge=1, le=99)
    agility: int = Field(..., ge=1, le=99)
    speed: int = Field(..., ge=1, le=99)
    aggression: int = Field(..., ge=1, le=99)
    glove_high: int = Field(..., ge=1, le=99)
    glove_low: int = Field(..., ge=1, le=99)
    five_hole: int = Field(..., ge=1, le=99)
    stick_high: int = Field(..., ge=1, le=99)
    stick_low: int = Field(..., ge=1, le=99)
    shot_recovery: int = Field(..., ge=1, le=99)
    positioning: int = Field(..., ge=1, le=99)
    breakaway: int = Field(..., ge=1, le=99)
    vision: int = Field(..., ge=1, le=99)
    poke_check: int = Field(..., ge=1, le=99)
    rebound_control: int = Field(..., ge=1, le=99)


class Player(BaseModel):
    """Generic player model (can be forward, defense, or goalie)."""
    id: int
    player_id: int
    first_name: str = ""
    last_name: str = ""
    img: str
    event: str
    nationality: str
    league: str
    team: str
    weight: float
    height: int
    salary: float
    overall: int
    position: str
    
    @property
    def full_name(self) -> str:
        """Return player's full name."""
        return f"{self.first_name} {self.last_name}".strip()
