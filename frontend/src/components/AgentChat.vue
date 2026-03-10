<template>
  <div class="content" role="main">
    <div class="chat-header mb-3">
      <h3 id="chat-title">SRL-Interview</h3>

      <ChatSettings
        v-if="$store.getters.showSettings"
        :documents="[]"
      />
    </div>

    <button
      v-if="!chatStarted"
      @click="startChat"
      class="btn btn-primary start-btn"
    >
      Start Interview
    </button>

    <ChatUI
      :messages="messages"
      @requestChatResponse="requestAgentChat"
      aria-labelledby="chat-title"
    />
  </div>
</template>

<script>
import Vue from "vue";
import ChatSettings from "./ChatSettings.vue";
import ChatUI from "./ChatUI.vue";
import Communication from "../classes/communication";

export default Vue.extend({
  name: "AgentChat",

  components: {
    ChatSettings,
    ChatUI
  },

  data() {
    return {
      messages: [],
      messageId: 0,
      chatStarted: false,
      is_loading: false
    };
  },

  methods: {
    nextId() {
      return ++this.messageId;
    },

    async startChat() {
      try {
        this.is_loading = true;

        const userid = this.$store.getters.getUser;

        const res = await Communication.startConversation({
          language: "de",
          userid
        });

        this.messages.push({
          id: this.nextId(),
          author: "bot",
          message: res.message
        });

        this.chatStarted = true;
      } catch (err) {
        console.error(err);
        this.messages.push({
          id: this.nextId(),
          author: "bot",
          message: "Fehler beim Start des Interviews."
        });
      } finally {
        this.is_loading = false;
      }
    },

    async requestAgentChat(text) {
      if (!this.chatStarted) return;

      const userid = this.$store.getters.getUser;

      this.messages.push({
        id: this.nextId(),
        author: "user",
        message: text
      });

      try {
        this.is_loading = true;

        const res = await Communication.sendMessage({
          userid,
          message: text
        });

        this.messages.push({
          id: this.nextId(),
          author: "bot",
          message: res.message
        });
      } catch (err) {
        console.error(err);
        this.messages.push({
          id: this.nextId(),
          author: "bot",
          message: "Fehler bei der Antwort des SRL-Agenten."
        });
      } finally {
        this.is_loading = false;
      }
    }
  }
});
</script>

<style scoped>
.content {
  max-width: 830px;
  margin: 0 auto;
}

.start-btn {
  margin-bottom: 15px;
}
</style>
