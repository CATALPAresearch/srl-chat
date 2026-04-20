<template>
  <div id="container" class="content agent-chat" role="main">
    <div class="chat-header mb-3 w100">
      <h3 class="d-flex justify-content-betweenx xalign-items-center mb-3">
        <span id="chat-title">Agent-Chat</span>
        <button
          hidden
          @click="$store.commit('toggleShowSettings', 1)"
          class="btn btn-link settings-icon-button"
          aria-controls="settings-panel"
          :aria-expanded="$store.getters.showSettings.toString()"
          aria-label="Einstellungen öffnen oder schließen"
          title="Einstellungen"
          style="margin-top: 0px"
        >
          <font-awesome-icon
            class="settings-icon"
            icon="cog"
            aria-hidden="true"
          />
        </button>
      </h3>
      <div id="intro">
        {{ $store.getters.getPluginSettings.intro }}
      </div>
      <ChatSettings hidden v-if="$store.getters.showSettings" :documents="[]" />
    </div>

    <button
      v-if="!chatStarted"
      @click="startChat"
      class="btn btn-primary start-btn w-25"
    >
      Start Chat
    </button>
    <ChatUI
      :messages="messages"
      :is_loading="is_loading"
      @requestChatResponse="requestAgentChat"
      aria-labelledby="chat-title"
    />
  </div>
</template>

<script lang="ts">
import axios from "axios";
import Vue from "vue";
//import { mapGetters } from 'vuex'
import ChatSettings from "./ChatSettings.vue";
import ChatUI from "./ChatUI.vue";
import Communication from "../classes/communication";

export default Vue.extend({
  name: "AgentChat",
  components: {
    ChatSettings: ChatSettings,
    ChatUI: ChatUI,
  },
  data() {
    return {
      messages: [],
      messageId: 0,
      error_msg: "",
      is_loading: false,
      host: "http://localhost:5000",
      chatStarted: false,
      userInput: "",
      tabHiddenAt: null,
      mouseTraceBuffer: [],
      mouseSessionId: null,
      mouseTraceInterval: null,
      mouseSampleInterval: null,
      lastMouseX: undefined,
      lastMouseY: undefined,
    };
  },

  methods: {
    getNextMessageId: function () {
      this.messageId++;
      return this.messageId;
    },

    startChat: async function () {
      console.log("Started Chat");
      this.setupTabVisibilityTracking();
      this.setupMouseTracking();
      let _this = this;
      // curl -X POST http://localhost:5000/startConversation -H "Content-Type: application/json" -d '{ "language": "en", "client": "discord", "userid": "none"}'
      await axios
        .post(this.host + "/startConversation", {
          language: "en",
          client: "discord",
          userid: this.$store.getters.getUser,
        })
        .then((response) => {
          _this.is_loading = false;
          console.log("/startConversation: ", response);
          _this.messages.push({
            message:
              (response.data && response.data.message) || "Chat started!",
            author: "bot",
            id: _this.getNextMessageId(),
          });
          _this.chatStarted = true;
        })
        .catch((error) => {
          _this.is_loading = false;
          console.error("Error starting chat:", error);
        });
    },

    requestAgentChat: async function (message) {
      if (this.$store.getters.getChatModus !== "agent-chat") {
        return;
      }

      this.is_loading = true;

      //@ts-ignore
      let new_message = {
        author: "user",
        message: message,
        id: this.getNextMessageId(),
      };
      this.messages.push(new_message);
      Communication.webservice("triggerEvent", {
        cmid: this.$store.getters.getCMID,
        action: "agent_request",
        value: JSON.stringify(new_message),
      });

      // TODO: let admin define the url of the agent webservice
      //const base = new URL(this.$store.getters.getRAGWebserviceHost);

      const bot_placeholder = {
        author: "bot",
        message: "",
        id: this.getNextMessageId(),
      };
      const bot_pos = this.messages.push(bot_placeholder) - 1;

      await axios
        .post(this.host + "/reply", {
          message: message,
          client: "discord",
          userid: this.$store.getters.getUser,
        })
        .then((response) => {
          this.is_loading = false;
          console.log("/reply: ", response);
          this.$set(this.messages, bot_pos, {
            author: "bot",
            message: (response.data && response.data.message) || response.data,
            id: bot_placeholder.id,
          });
          this.wait_video_generation = false;
        })
        .catch((error) => {
          this.is_loading = false;
          console.error("Error sending message:", error);
          this.$set(this.messages, bot_pos, {
            author: "bot",
            message: "Error: Unable to get a response.",
            id: bot_placeholder.id,
          });
        });
    },

    setupTabVisibilityTracking: function () {
      const _this = this;
      document.addEventListener("visibilitychange", function () {
        const event = document.hidden ? "tab_hidden" : "tab_visible";
        const timestamp = Math.floor(Date.now() / 1000);

        if (document.hidden) {
          _this.tabHiddenAt = timestamp;
        }

        axios
          .post(_this.host + "/log/tab_event", {
            userid: _this.$store.getters.getUser,
            client: "discord",
            event: event,
            timestamp: timestamp,
          })
          .catch(function (error) {
            console.warn("Tab event logging failed:", error);
          });

        console.log("Tab visibility changed:", event, "at", timestamp);
      });
    },

    setupMouseTracking: function () {
      const _this = this;
      this.mouseSessionId = "session_" + Date.now();

      // Sample mouse position every 2 seconds
      this.mouseSampleInterval = setInterval(function () {
        if (_this.lastMouseX !== undefined && _this.lastMouseY !== undefined) {
          _this.mouseTraceBuffer.push({
            x: _this.lastMouseX,
            y: _this.lastMouseY,
            page_width: window.innerWidth,
            page_height: window.innerHeight,
            timestamp: Math.floor(Date.now() / 1000),
          });
        }
      }, 2000);

      // Send batch every 10 seconds
      this.mouseTraceInterval = setInterval(function () {
        if (_this.mouseTraceBuffer.length > 0) {
          const batch = _this.mouseTraceBuffer.splice(0);
          axios
            .post(_this.host + "/log/mouse_traces", {
              userid: _this.$store.getters.getUser,
              client: "discord",
              session_id: _this.mouseSessionId,
              traces: batch,
            })
            .catch(function (error) {
              console.warn("Mouse trace logging failed:", error);
            });
        }
      }, 10000);

      // Track mouse position
      document.addEventListener("mousemove", function (e) {
        _this.lastMouseX = e.clientX;
        _this.lastMouseY = e.clientY;
      });
    },

    stopMouseTracking: function () {
      if (this.mouseTraceInterval) clearInterval(this.mouseTraceInterval);
      if (this.mouseSampleInterval) clearInterval(this.mouseSampleInterval);
    },
  },

  beforeDestroy() {
    this.stopMouseTracking();
  },
});
</script>

<style scoped>
.sr-only {
  position: absolute;
  left: -9999px;
  width: 1px;
  height: 1px;
  overflow: hidden;
}

.chat-widget {
  max-width: 400px;
  margin: auto;
  font-family: Arial, sans-serif;
}

.chat-container {
  border: 1px solid #ccc;
  padding: 10px;
  border-radius: 5px;
  background: #f9f9f9;
}

.messages {
  max-height: 300px;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
}

.user-message {
  align-self: flex-end;
  background-color: #007bff;
  color: white;
  padding: 8px;
  border-radius: 10px;
  margin: 5px;
}

.server-message {
  align-self: flex-start;
  background-color: #e0e0e0;
  padding: 8px;
  border-radius: 10px;
  margin: 5px;
}

.chat-input {
  display: flex;
  margin-top: 10px;
}

.chat-input input {
  flex-grow: 1;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 5px;
}

.chat-input button {
  padding: 8px 15px;
  margin-left: 5px;
  border: none;
  background-color: #28a745;
  color: white;
  cursor: pointer;
}

.agent-chat {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
</style>
