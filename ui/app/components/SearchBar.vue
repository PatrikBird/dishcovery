<script setup>
// Search state
const searchQuery = ref('')
const searchChips = ref([])

// Mock search functionality
const handleSearch = () => {
  if (!searchQuery.value.trim()) return

  // Convert search to chip
  const chip = {
    id: Date.now(),
    label: searchQuery.value.trim(),
    type: 'query'
  }

  searchChips.value.push(chip)
  searchQuery.value = ''

  console.log('Search executed with chips:', searchChips.value)
}

const removeChip = (chipId) => {
  searchChips.value = searchChips.value.filter(chip => chip.id !== chipId)
}
</script>

<template>
  <div class="search-bar-container">
    <!-- Smart Search Input -->
    <div class="relative">
      <UInput v-model="searchQuery" placeholder="Search recipes by ingredients, cuisine, or name..."
        class="search-input font-mono text-base" size="xl" :ui="{
          base: 'border-b-4 border-carbon-500 bg-transparent focus:border-carbon-600 rounded-none shadow-none',
          padding: { xl: 'px-4 py-4' }
        }" @keydown.enter="handleSearch" />

      <!-- Search Button -->
      <UButton class="absolute right-2 top-1/2 transform -translate-y-1/2 rounded-none" color="carbon" variant="ghost"
        size="sm" @click="handleSearch">
        Search
      </UButton>
    </div>

    <!-- Search Chips Container -->
    <div v-if="searchChips.length" class="flex flex-wrap gap-2 mt-3">
      <UBadge v-for="chip in searchChips" :key="chip.id"
        class="font-mono rounded-none bg-carbon-100 text-carbon-900 border border-carbon-300" size="sm">
        {{ chip.label }}
        <UButton class="ml-2 text-carbon-700 hover:text-carbon-900" variant="link" size="xs"
          @click="removeChip(chip.id)">
          ×
        </UButton>
      </UBadge>
    </div>
  </div>
</template>

<style scoped>
.search-input {
  font-family: 'IBM Plex Mono', monospace;
}
</style>
