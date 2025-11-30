<script setup lang="ts">
const results = ref([])
const sortBy = ref('relevance')
const isLoading = ref(false)

const sortOptions = [
  { label: 'Relevance', value: 'relevance' },
  { label: 'Prep Time ↑', value: 'prep_time_asc' },
  { label: 'Prep Time ↓', value: 'prep_time_desc' },
  { label: 'Healthiness ↑', value: 'health_asc' },
  { label: 'Healthiness ↓', value: 'health_desc' }
]

const generateMockRecipe = (id) => ({
  id: `R${String(id).padStart(4, '0')}`,
  title: [
    'Spicy Thai Basil Chicken Stir Fry',
    'Classic Italian Carbonara',
    'Mexican Street Corn Salad',
    'Mediterranean Quinoa Bowl',
    'Korean BBQ Beef Tacos',
    'Indian Butter Chicken Curry',
    'Japanese Teriyaki Salmon',
    'French Onion Soup',
    'Greek Lemon Herb Roasted Chicken',
    'Chinese Kung Pao Chicken'
  ][Math.floor(Math.random() * 10)],
  prep_time: Math.floor(Math.random() * 45) + 10,
  cook_time: Math.floor(Math.random() * 60) + 15,
  difficulty: ['easy', 'medium', 'hard'][Math.floor(Math.random() * 3)],
  cuisine: ['italian', 'american', 'mexican', 'asian', 'french'][Math.floor(Math.random() * 5)],
  healthiness_score: Math.floor(Math.random() * 100) + 1,
  is_vegan: Math.random() > 0.8,
  is_vegetarian: Math.random() > 0.6,
  ingredients_count: Math.floor(Math.random() * 15) + 5
})

// Initialize with mock data
const initializeMockData = () => {
  results.value = Array.from({ length: 10 }, (_, i) => generateMockRecipe(i + 1))
}

const loadMore = async () => {
  isLoading.value = true

  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 800))

  // Add more mock results
  const newResults = Array.from({ length: 10 }, (_, i) =>
    generateMockRecipe(results.value.length + i + 1)
  )

  results.value.push(...newResults)
  isLoading.value = false
}

// Initialize on mount
onMounted(() => {
  initializeMockData()
})
</script>

<template>
  <div class="results-feed-container @container">

    <!-- Results Header -->
    <div class="results-header mb-6 pb-4 border-b border-coolgray-200 dark:border-coolgray-700">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-carbon-heading-04 font-mono font-semibold text-coolgray-900 dark:text-coolgray-50">
            RECIPE DISCOVERY
          </h1>
          <p class="text-carbon-body-01 text-coolgray-600 dark:text-coolgray-400 mt-1 font-mono">
            {{ results.length.toLocaleString() }} recipes found
          </p>
        </div>

        <!-- Sort Controls -->
        <USelect v-model="sortBy" :options="sortOptions" class="font-mono rounded-none min-w-[200px]" size="sm" />
      </div>
    </div>

    <!-- Results Grid -->
    <div class="results-grid space-y-4">
      <RecipeCard v-for="recipe in results" :key="recipe.id" :recipe="recipe" class="@sm:@container" />

      <!-- Load More Button -->
      <div class="text-center pt-8">
        <UButton color="carbon" variant="outline" size="lg" class="rounded-none font-mono px-8" :loading="isLoading"
          @click="loadMore">
          Load More Results
        </UButton>
      </div>
    </div>
  </div>
</template>
