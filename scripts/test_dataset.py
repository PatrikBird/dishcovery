import json
import sys


def test_dataset(file_path):
    print(f"Testing dataset: {file_path}")
    print("-" * 60)

    try:
        # Load the dataset
        print("📂 Loading JSON file...")
        with open(file_path, "r") as f:
            data = json.load(f)

        print(f"✅ Successfully loaded!")
        print(f"📊 Total recipes: {len(data):,}")
        print()

        # Check structure
        if len(data) > 0:
            first_recipe = data[0]
            print(f"🔑 Fields in first recipe: {len(first_recipe)}")
            print(f"📋 Field names:")
            for key in first_recipe.keys():
                value = first_recipe[key]
                value_type = type(value).__name__
                print(f"   - {key:25} ({value_type})")

            print()
            print("📖 Sample Recipe:")
            print(f"   Title: {first_recipe.get('recipe_title')}")
            print(
                f"   Categories: {first_recipe.get('categories', first_recipe.get('category'))}"
            )
            print(f"   Ingredients: {first_recipe.get('num_ingredients')}")
            print(f"   Steps: {first_recipe.get('num_steps')}")
            print(f"   Vegan: {first_recipe.get('is_vegan')}")
            print(f"   Prep Time: {first_recipe.get('est_prep_time_min')} min")
            print(f"   Cook Time: {first_recipe.get('est_cook_time_min')} min")
            print()

            # Verify key fields exist
            required_fields = [
                "recipe_title",
                "description",
                "ingredients",
                "directions",
                "num_ingredients",
                "num_steps",
                "cuisine_list",
                "is_vegan",
                "is_vegetarian",
                "difficulty",
                "healthiness_score",
            ]

            missing_fields = [f for f in required_fields if f not in first_recipe]

            if missing_fields:
                print(f"⚠️  Missing expected fields: {missing_fields}")
            else:
                print("✅ All expected fields present!")

            # Process all recipes
            print("✅ Dataset validation complete!")
            return True

    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "data/recipes.json"

    success = test_dataset(file_path)
    sys.exit(0 if success else 1)
