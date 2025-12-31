<script>
import Vue from "vue";
import ChatSettings from "./ChatSettings.vue";
import ChatUI from "./ChatUI.vue";
import Communication from "../classes/communication";

export default Vue.extend({
  name: "ChatApp",

  components: {
    ChatSettings,
    ChatUI,
  },

  data() {
    return {
      messages: [],
      messageId: 0,
      is_loading: false,
      chatStarted: false,
    };
  },

  methods: {
    getNextMessageId() {
      this.messageId += 1;
      return this.messageId;
    },

    async startChat() {
      try {
        this.is_loading = true;
        const userid = this.$store.getters.getUser;

        const response = await Communication.startConversation({
          language: "de",
          userid,
        });

        this.messages.push({
          id: this.getNextMessageId(),
          author: "bot",
          message: response.message,
        });

        this.chatStarted = true;
      } catch (err) {
        console.error("Failed to start SRL interview:", err);
        this.messages.push({
          id: this.getNextMessageId(),
          author: "bot",
          message: "Fehler beim Start des Interviews.",
        });
      } finally {
        this.is_loading = false;
      }
    },

    async requestAgentChat(userMessage) {
      if (!this.chatStarted) return;

      const userid = this.$store.getters.getUser;

      this.messages.push({
        id: this.getNextMessageId(),
        author: "user",
        message: userMessage,
      });

      try {
        this.is_loading = true;

        const response = await Communication.sendMessage({
          userid,
          message: userMessage,
        });

        this.messages.push({
          id: this.getNextMessageId(),
          author: "bot",
          message: response.message,
        });
      } catch (err) {
        console.error("SRL Agent error:", err);
        this.messages.push({
          id: this.getNextMessageId(),
          author: "bot",
          message: "Fehler bei der Antwort des SRL-Agenten.",
        });
      } finally {
        this.is_loading = false;
      }
    },
  },
});
</script>
