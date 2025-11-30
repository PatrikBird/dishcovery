<script setup lang="ts">
const props = defineProps({
  recipe: {
    type: Object,
    required: true
  }
})

// Cuisine glyph mapping
const getCuisineGlyph = (cuisine) => {
  const glyphs = {
    italian: '🍝',
    american: '🍔',
    mexican: '🌮',
    asian: '🥢',
    french: '🥐',
    indian: '🍛',
    japanese: '🍱',
    chinese: '🥟',
    greek: '🫒',
    thai: '🌶️'
  }
  return glyphs[cuisine] || '🍽️'
}
</script>

<template>
  <div
    class="recipe-card border border-coolgray-200 dark:border-coolgray-700 bg-white dark:bg-coolgray-900 p-4 @container">

    <!-- Recipe Header with ID -->
    <div class="recipe-header flex items-start justify-between mb-3">
      <!-- Recipe ID Block -->
      <div class="recipe-id-block">
        <div class="recipe-id font-mono text-lg font-bold text-carbon-600 dark:text-carbon-400">
          {{ recipe.id }}
        </div>
        <div class="recipe-glyph text-2xl text-coolgray-400" :title="recipe.cuisine">
          {{ getCuisineGlyph(recipe.cuisine) }}
        </div>
      </div>

      <!-- Quick Stats -->
      <div class="quick-stats flex gap-4 text-xs font-mono text-coolgray-600 dark:text-coolgray-400">
        <span class="difficulty-badge px-2 py-1 border border-coolgray-300 dark:border-coolgray-600 rounded-none">
          {{ recipe.difficulty.toUpperCase() }}
        </span>
        <span class="health-score">H{{ recipe.healthiness_score }}</span>
      </div>
    </div>

    <!-- Recipe Title -->
    <h3 class="recipe-title text-carbon-heading-03 font-semibold text-coolgray-900 dark:text-coolgray-50 mb-3">
      {{ recipe.title }}
    </h3>

    <!-- Recipe Striations (Data Grid) -->
    <div class="recipe-data space-y-2 mb-4">

      <!-- Time Row -->
      <div
        class="data-row flex justify-between items-center py-1 border-b border-coolgray-100 dark:border-coolgray-800">
        <span class="data-label font-mono text-sm text-coolgray-600 dark:text-coolgray-400">TIME</span>
        <span class="data-value font-mono text-sm text-coolgray-900 dark:text-coolgray-50">
          {{ recipe.prep_time }}m prep + {{ recipe.cook_time }}m cook
        </span>
      </div>

      <!-- Ingredients Row -->
      <div
        class="data-row flex justify-between items-center py-1 border-b border-coolgray-100 dark:border-coolgray-800">
        <span class="data-label font-mono text-sm text-coolgray-600 dark:text-coolgray-400">INGREDIENTS</span>
        <span class="data-value font-mono text-sm text-coolgray-900 dark:text-coolgray-50">
          {{ recipe.ingredients_count }} items
        </span>
      </div>

      <!-- Cuisine Row -->
      <div
        class="data-row flex justify-between items-center py-1 border-b border-coolgray-100 dark:border-coolgray-800">
        <span class="data-label font-mono text-sm text-coolgray-600 dark:text-coolgray-400">CUISINE</span>
        <span class="data-value font-mono text-sm text-coolgray-900 dark:text-coolgray-50 capitalize">
          {{ recipe.cuisine }}
        </span>
      </div>

    </div>

    <!-- Recipe Tags/Badges -->
    <div class="recipe-tags flex flex-wrap gap-2 mb-4">
      <UBadge v-if="recipe.is_vegan"
        class="font-mono rounded-none bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" size="xs">
        VEGAN
      </UBadge>
      <UBadge v-else-if="recipe.is_vegetarian"
        class="font-mono rounded-none bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200" size="xs">
        VEGETARIAN
      </UBadge>
    </div>

    <!-- Recipe Actions -->
    <div class="recipe-actions flex gap-2 @lg:gap-3">
      <UButton color="carbon" variant="solid" size="xs" class="rounded-none font-mono flex-1 @lg:flex-none">
        VIEW RECIPE
      </UButton>
      <UButton color="coolgray" variant="outline" size="xs" class="rounded-none font-mono">
        SAVE
      </UButton>
    </div>

  </div>
</template>

<style scoped>
/* Ensure proper container query behavior */
.recipe-card {
  container-type: inline-size;
}

/* Responsive adjustments using container queries */
@container (min-width: 400px) {
  .recipe-actions {
    justify-content: flex-start;
  }
}
</style>
