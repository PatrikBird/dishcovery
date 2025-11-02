from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class DifficultyLevel(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class CookSpeed(str, Enum):
    FAST = "fast"
    MEDIUM = "medium"
    SLOW = "slow"


class SearchRequest(BaseModel):
    """Request model for advanced search"""

    query: Optional[str] = Field(
        None, description="Text search across title, description, ingredients"
    )
    cuisines: Optional[List[str]] = Field(None, description="Filter by cuisine types")
    difficulty: Optional[DifficultyLevel] = Field(
        None, description="Recipe difficulty level"
    )
    max_prep_time: Optional[int] = Field(
        None, description="Maximum prep time in minutes"
    )
    max_cook_time: Optional[int] = Field(
        None, description="Maximum cook time in minutes"
    )
    is_vegan: Optional[bool] = Field(None, description="Filter for vegan recipes")
    is_vegetarian: Optional[bool] = Field(
        None, description="Filter for vegetarian recipes"
    )
    is_gluten_free: Optional[bool] = Field(
        None, description="Filter for gluten-free recipes"
    )
    min_healthiness: Optional[int] = Field(
        None, ge=0, le=100, description="Minimum healthiness score (0-100)"
    )
    size: int = Field(10, ge=1, le=100, description="Number of results to return")
    from_: int = Field(0, ge=0, description="Offset for pagination", alias="from")


class Recipe(BaseModel):
    """Recipe response model"""

    recipe_title: str
    description: Optional[str] = None
    cuisine_list: Optional[List[str]] = None
    difficulty: Optional[str] = None
    est_prep_time_min: Optional[int] = None
    est_cook_time_min: Optional[int] = None
    is_vegan: Optional[bool] = None
    is_vegetarian: Optional[bool] = None
    is_gluten_free: Optional[bool] = None
    healthiness_score: Optional[int] = None
    ingredients_raw: Optional[List[str]] = None  # Array of ingredient strings
    directions_raw: Optional[List[str]] = None   # Array of direction strings


class SearchResponse(BaseModel):
    """Search results response"""

    total: int = Field(description="Total number of matching recipes")
    recipes: List[Recipe] = Field(description="Array of recipe results")
    took_ms: int = Field(description="Search execution time in milliseconds")


class BulkLoadResponse(BaseModel):
    """Response for bulk data loading"""

    loaded_count: int
    failed_count: int
    total_time_seconds: float
    message: str
