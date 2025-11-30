<script setup lang="ts">
const showMobileFilters = ref(false)
</script>

<template>
  <div class="dishcovery-app min-h-screen bg-coolgray-50 dark:bg-coolgray-950 text-coolgray-900 dark:text-coolgray-50">
    <NuxtRouteAnnouncer />

    <!-- Main App Layout Grid -->
    <div class="h-screen grid grid-rows-[auto_1fr] grid-cols-1 md:grid-cols-[min(25vw,320px)_1fr]">

      <!-- Header Search Bar -->
      <header
        class="@container/search col-span-full border-b border-coolgray-200 dark:border-coolgray-700 bg-white dark:bg-coolgray-900">
        <div class="p-4 @lg/search:px-8">
          <SearchBar />
        </div>
      </header>

      <!-- Filters Sidebar (Desktop) -->
      <aside
        class="@container/sidebar hidden md:block border-r border-coolgray-200 dark:border-coolgray-700 bg-white dark:bg-coolgray-900 overflow-y-auto">
        <div class="p-4 @xs/sidebar:p-2 @lg/sidebar:p-6">
          <FiltersSidebar />
        </div>
      </aside>

      <!-- Main Content Area -->
      <main class="@container/main overflow-y-auto bg-coolgray-50 dark:bg-coolgray-950">
        <div class="p-4 @xl/main:max-w-6xl @xl/main:mx-auto">
          <ResultsFeed />
        </div>
      </main>

    </div>

    <!-- Mobile Filter Button (when sidebar hidden) -->
    <UButton class="md:hidden fixed bottom-4 right-4 z-50" color="carbon" variant="solid" size="lg"
      @click="showMobileFilters = true">
      Filters
    </UButton>

    <!-- Mobile Off-Canvas Drawer (TODO: implement) -->
    <!-- Will slide over from left/right on mobile -->

  </div>
</template>
