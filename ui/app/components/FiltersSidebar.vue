<script setup lang="ts">
// Mock data for filters
const cuisineOptions = ref([
  { label: 'Italian', value: 'italian', count: 1247 },
  { label: 'American', value: 'american', count: 3891 },
  { label: 'Mexican', value: 'mexican', count: 892 },
  { label: 'Asian', value: 'asian', count: 2156 },
  { label: 'French', value: 'french', count: 445 }
])

const applyFilters = () => {
  console.log('Applying filters...')
  // TODO: Implement filter application
}

const clearFilters = () => {
  console.log('Clearing filters...')
  // TODO: Implement filter clearing
}
</script>

<template>
  <div class="filters-sidebar-container">
    <!-- Sidebar Header -->
    <div class="border-b border-coolgray-200 dark:border-coolgray-700 pb-4 mb-6">
      <h2 class="text-carbon-heading-03 font-mono font-semibold text-coolgray-900 dark:text-coolgray-50">
        FILTERS
      </h2>
      <p class="text-carbon-body-01 text-coolgray-600 dark:text-coolgray-400 mt-1">
        Refine your search
      </p>
    </div>

    <!-- Filter Groups -->
    <div class="space-y-6">

      <!-- Cuisine Filter -->
      <div class="filter-group">
        <UAccordion :items="[{
          label: 'Cuisine',
          slot: 'cuisine',
          defaultOpen: true
        }]" :ui="{ wrapper: 'rounded-none border-coolgray-200 dark:border-coolgray-700' }">
          <template #cuisine>
            <div class="space-y-2 pt-3">
              <UCheckbox v-for="cuisine in cuisineOptions" :key="cuisine.value"
                :label="`${cuisine.label} (${cuisine.count})`" :value="cuisine.value" class="font-mono text-sm" />
            </div>
          </template>
        </UAccordion>
      </div>

      <!-- Dietary Restrictions -->
      <div class="filter-group">
        <UAccordion :items="[{
          label: 'Dietary',
          slot: 'dietary'
        }]" :ui="{ wrapper: 'rounded-none border-coolgray-200 dark:border-coolgray-700' }">
          <template #dietary>
            <div class="space-y-2 pt-3">
              <UCheckbox label="Vegan" class="font-mono text-sm" />
              <UCheckbox label="Vegetarian" class="font-mono text-sm" />
              <UCheckbox label="Gluten-Free" class="font-mono text-sm" />
              <UCheckbox label="Dairy-Free" class="font-mono text-sm" />
            </div>
          </template>
        </UAccordion>
      </div>

      <!-- Time Constraints -->
      <div class="filter-group">
        <UAccordion :items="[{
          label: 'Time Constraints',
          slot: 'time'
        }]" :ui="{ wrapper: 'rounded-none border-coolgray-200 dark:border-coolgray-700' }">
          <template #time>
            <div class="space-y-4 pt-3">
              <!-- Prep Time -->
              <div>
                <label class="block text-sm font-mono text-coolgray-700 dark:text-coolgray-300 mb-2">
                  Max Prep Time (min)
                </label>
                <UInput type="number" placeholder="30" class="font-mono rounded-none" size="sm" />
              </div>

              <!-- Cook Time -->
              <div>
                <label class="block text-sm font-mono text-coolgray-700 dark:text-coolgray-300 mb-2">
                  Max Cook Time (min)
                </label>
                <UInput type="number" placeholder="60" class="font-mono rounded-none" size="sm" />
              </div>
            </div>
          </template>
        </UAccordion>
      </div>

    </div>

    <!-- Filter Actions -->
    <div class="mt-8 pt-6 border-t border-coolgray-200 dark:border-coolgray-700 space-y-3">
      <UButton color="carbon" variant="solid" size="sm" class="w-full rounded-none font-mono" @click="applyFilters">
        Apply Filters
      </UButton>
      <UButton color="coolgray" variant="outline" size="sm" class="w-full rounded-none font-mono" @click="clearFilters">
        Clear All
      </UButton>
    </div>
  </div>
</template>
