<template>
  <div class="chat-app">
    <nav class="content mb-3 tabs">
      <router-link to="/agent-chat" class="tab" active-class="active">
        Interview zu Lernstrategien
      </router-link>
      <router-link to="/survey" class="tab" active-class="active">
        Umfrage
      </router-link>
      <router-link to="/dashboard/teacher" class="tab" active-class="active">
        Lehrenden Dashboard
      </router-link>
      <router-link to="/dashboard/reseacher" class="tab" active-class="active">
        Researcher Dashboard
      </router-link>
    </nav>
    <router-view class="chat-app__view" />
  </div>
</template>

<script>
import Vue from "vue";

export default Vue.extend({
  name: "ChatApp",
});
</script>

<style scoped>
.chat-app {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-app__view {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: auto;
}

.content {
  max-width: 100%;
  margin: 0 auto;
  padding: 8px;
}

.tabs {
  display: flex;
  flex-wrap: wrap;
}

.tab {
  margin-right: 12px;
  padding: 6px 10px;
  text-decoration: none;
  color: #333;
  border-bottom: 2px solid transparent;
}

.tab.active {
  border-bottom: 2px solid #1976d2;
  font-weight: 600;
}
</style>
