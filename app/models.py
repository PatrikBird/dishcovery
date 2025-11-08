from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class CookSpeed(str, Enum):
    FAST = "fast"
    MEDIUM = "medium"
    SLOW = "slow"


class SearchRequest(BaseModel):
    """Request model for recipe search - all fields are optional for maximum flexibility"""

    # Text search
    query: Optional[str] = Field(
        None,
        description="Text search across recipe titles, descriptions, ingredients, and directions",
        example="pasta",
    )
    fuzziness: Optional[str] = Field(
        "AUTO",
        description="Fuzzy matching level: 0 (exact), 1, 2, or AUTO (recommended)",
        example="AUTO",
    )

    # Cuisine and category filters
    cuisines: Optional[List[str]] = Field(
        None,
        description="Filter by one or more cuisine types",
        example=["italian", "asian"],
    )

    # Difficulty and timing
    difficulty: Optional[DifficultyLevel] = Field(
        None, description="Recipe difficulty level"
    )
    max_prep_time: Optional[int] = Field(
        None, ge=0, description="Maximum prep time in minutes", example=30
    )
    max_cook_time: Optional[int] = Field(
        None, ge=0, description="Maximum cook time in minutes", example=60
    )

    # Dietary preferences
    is_vegan: Optional[bool] = Field(None, description="Filter for vegan recipes")
    is_vegetarian: Optional[bool] = Field(
        None, description="Filter for vegetarian recipes"
    )
    is_gluten_free: Optional[bool] = Field(
        None, description="Filter for gluten-free recipes"
    )
    is_dairy_free: Optional[bool] = Field(
        None, description="Filter for dairy-free recipes"
    )
    is_nut_free: Optional[bool] = Field(None, description="Filter for nut-free recipes")

    # Health and nutrition
    min_healthiness: Optional[int] = Field(
        None, ge=0, le=100, description="Minimum healthiness score (0-100)", example=70
    )
    max_healthiness: Optional[int] = Field(
        None, ge=0, le=100, description="Maximum healthiness score (0-100)", example=90
    )

    # Pagination
    size: int = Field(
        10, ge=1, le=100, description="Number of results to return", example=10
    )
    from_: int = Field(
        0, ge=0, description="Offset for pagination (0-based)", alias="from", example=0
    )


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
    directions_raw: Optional[List[str]] = None  # Array of direction strings


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
