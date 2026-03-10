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
  name: "ChatApp",

  computed: {
    userid() {
      return localStorage.getItem("userid");
    },
    client() {
      return "web";
    }
  },

  mounted() {
    document.addEventListener("visibilitychange", this.handleVisibilityChange);
    window.addEventListener("beforeunload", this.handleTabClose);

    this.logTabEvent("TAB_ENTER");
  },

  beforeDestroy() {
    document.removeEventListener("visibilitychange", this.handleVisibilityChange);
    window.removeEventListener("beforeunload", this.handleTabClose);
  },

  methods: {
    handleVisibilityChange() {
      if (document.visibilityState === "visible") {
        this.logTabEvent("TAB_ENTER");
      } else {
        this.logTabEvent("TAB_LEAVE");
      }
    },

    handleTabClose() {
      if (!this.userid) return;

      const blob = new Blob(
        [JSON.stringify({
          event: "TAB_CLOSE",
          timestamp: new Date().toISOString(),
          userid: this.userid,
          client: this.client
        })],
        { type: "application/json" }
      );

      navigator.sendBeacon("/api/log-tab-event", blob);
    },

    logTabEvent(eventType) {
      if (!this.userid) return;

      fetch("/api/log-tab-event", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          event: eventType,
          timestamp: new Date().toISOString(),
          userid: this.userid,
          client: this.client
        })
      }).catch(console.error);
    }
  }
});
</script>




<style scoped>
.chat-app {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* important for Moodle iframe */
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
