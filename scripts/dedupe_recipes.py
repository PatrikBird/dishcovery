#!/usr/bin/env python3
"""
Deduplicate recipes by merging duplicate entries.

Duplicates are identified by matching recipe_title + ingredients.
When duplicates are found, categories and subcategories are merged into lists.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def generate_recipe_key(recipe: dict) -> str:
    """
    Generate a unique key for a recipe based on title and ingredients.

    Key = lowercase(title) + "|" + sorted lowercase ingredients joined by "||"
    """
    title = recipe.get("recipe_title", "").lower().strip()

    # Get ingredients list and normalize
    ingredients = recipe.get("ingredients", [])
    if isinstance(ingredients, list):
        normalized_ingredients = sorted([ing.lower().strip() for ing in ingredients])
    else:
        normalized_ingredients = []

    ingredients_str = "||".join(normalized_ingredients)
    return f"{title}|{ingredients_str}"


def regenerate_combined_text(recipe: dict) -> str:
    """
    Regenerate the combined_text field to include all categories/subcategories.

    Format: title + categories + subcategories + ingredients + directions
    """
    parts = []

    # Title
    title = recipe.get("recipe_title", "")
    if title:
        parts.append(title.lower())

    # All categories
    categories = recipe.get("categories", [])
    for cat in categories:
        parts.append(cat.lower())

    # All subcategories
    subcategories = recipe.get("subcategories", [])
    for subcat in subcategories:
        parts.append(subcat.lower())

    # Ingredients (raw format with quantities)
    ingredients = recipe.get("ingredients", [])
    for ing in ingredients:
        parts.append(ing.lower() if isinstance(ing, str) else str(ing))

    # Directions
    directions_text = recipe.get("directions_text", "")
    if directions_text:
        parts.append(directions_text.lower())

    return " ".join(parts)


def merge_recipes(recipes: list[dict]) -> dict:
    """
    Merge a list of duplicate recipes into a single recipe.

    - Uses the first recipe as the base
    - Collects all unique categories into 'categories' list
    - Collects all unique subcategories into 'subcategories' list
    - Regenerates combined_text to include all categories
    - Removes old 'category' and 'subcategory' fields
    """
    if not recipes:
        return {}

    # Use first recipe as base
    merged = recipes[0].copy()

    # Collect all unique categories and subcategories
    categories = set()
    subcategories = set()

    for recipe in recipes:
        cat = recipe.get("category")
        if cat:
            categories.add(cat)

        subcat = recipe.get("subcategory")
        if subcat:
            subcategories.add(subcat)

    # Replace singular fields with lists
    merged["categories"] = sorted(list(categories))
    merged["subcategories"] = sorted(list(subcategories))

    # Remove old singular fields
    merged.pop("category", None)
    merged.pop("subcategory", None)

    # Regenerate combined_text
    merged["combined_text"] = regenerate_combined_text(merged)

    return merged


def deduplicate_recipes(recipes: list[dict]) -> tuple[list[dict], dict]:
    """
    Deduplicate recipes and return merged results with statistics.

    Returns:
        - List of deduplicated recipes
        - Statistics dictionary
    """
    # Group recipes by their unique key
    groups = defaultdict(list)

    for recipe in recipes:
        key = generate_recipe_key(recipe)
        groups[key].append(recipe)

    # Merge each group
    deduplicated = []
    duplicate_counts = []

    for key, group in groups.items():
        merged = merge_recipes(group)
        deduplicated.append(merged)

        if len(group) > 1:
            duplicate_counts.append(
                {
                    "title": merged.get("recipe_title", "Unknown"),
                    "count": len(group),
                    "categories": merged.get("categories", []),
                }
            )

    # Sort duplicate_counts by count descending
    duplicate_counts.sort(key=lambda x: x["count"], reverse=True)

    stats = {
        "total_before": len(recipes),
        "total_after": len(deduplicated),
        "duplicates_removed": len(recipes) - len(deduplicated),
        "unique_duplicated_recipes": len(duplicate_counts),
        "top_duplicates": duplicate_counts[:10],
    }

    return deduplicated, stats


def main():
    parser = argparse.ArgumentParser(
        description="Deduplicate recipes by merging entries with same title and ingredients"
    )
    parser.add_argument(
        "--input",
        "-i",
        default="data/recipes.json",
        help="Input JSON file path (default: data/recipes.json)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="data/recipes_cleaned.json",
        help="Output JSON file path (default: data/recipes_cleaned.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze duplicates without writing output file",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    # Validate input file
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    # Load recipes
    print(f"Loading recipes from {input_path}...")
    with open(input_path, "r", encoding="utf-8") as f:
        recipes = json.load(f)

    print(f"Loaded {len(recipes):,} recipes")

    # Deduplicate
    print("Deduplicating...")
    deduplicated, stats = deduplicate_recipes(recipes)

    # Print statistics
    print()
    print("=" * 60)
    print("DEDUPLICATION RESULTS")
    print("=" * 60)
    print(f"Total recipes before:    {stats['total_before']:,}")
    print(f"Total recipes after:     {stats['total_after']:,}")
    print(f"Duplicates removed:      {stats['duplicates_removed']:,}")
    print(f"Recipes with duplicates: {stats['unique_duplicated_recipes']:,}")
    print()

    if stats["top_duplicates"]:
        print("Top 10 most duplicated recipes:")
        print("-" * 60)
        for i, dup in enumerate(stats["top_duplicates"], 1):
            cats = ", ".join(dup["categories"][:3])
            if len(dup["categories"]) > 3:
                cats += f" (+{len(dup['categories']) - 3} more)"
            print(f"  {i:2}. {dup['title'][:40]:<40} ({dup['count']}x)")
            print(f"      Categories: {cats}")
        print()

    # Write output
    if args.dry_run:
        print("Dry run - no output file written")
    else:
        print(f"Writing deduplicated recipes to {output_path}...")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(deduplicated, f, indent=2, ensure_ascii=False)
        print(f"Done! Output written to {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
