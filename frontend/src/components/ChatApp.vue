<template>
  <div class="chat-app">
    <nav class="content mb-3 tabs">
      <router-link to="/agent-chat" class="tab" active-class="active">
        SRL-Interview
      </router-link>
      <router-link to="/llm-chat" class="tab" active-class="active">
        LLM-Chat
      </router-link>
      <router-link to="/document-chat" class="tab" active-class="active">
        Dokumenten-Chat
      </router-link>
    </nav>

    <router-view />
  </div>
</template>

<script>
import Vue from "vue";

export default Vue.extend({
  name: "ChatApp"
});
</script>

<style scoped>
.chat-app {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* 👈 important for Moodle iframe */
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
