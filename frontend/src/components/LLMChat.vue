<template>
  <div id="container" class="content" role="main">
    <div class="chat-header mb-3 w100">
      <h3 class="d-flex justify-content-betweenx xalign-items-center mb-3">
        <span id="chat-title">LLM-Chat</span>
        <button
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
      <RAGChatSettings v-if="$store.getters.showSettings" :documents="[]" />
    </div>

    <ChatUI :messages="messages" @requestChatResponse="requestServerChat" />
  </div>
</template>

<script lang="ts">
import Vue from "vue";
import { mapGetters } from "vuex";
import RAGChatSettings from "./ChatSettings.vue";
import ChatUI from "./ChatUI.vue";
import Communication from "../classes/communication";

export default Vue.extend({
  name: "LLMChat",
  components: {
    RAGChatSettings: RAGChatSettings,
    ChatUI: ChatUI,
  },
  props: {
    show_setting: Boolean,
  },
  data() {
    return {
      messages: [],
      messageId: 0,
    };
  },
  mounted: function () {},
  methods: {
    getNextMessageId: function () {
      this.messageId++;
      return this.messageId;
    },

    requestServerChat: async function (message) {
      console.log(1);
      let _this = this;
      if (this.$store.getters.getChatModus !== "llm-chat") {
        console.error(
          "@LLMChat: llm-chat not selected as modus: " +
            this.$store.getters.getChatModus
        );
        return;
      }
      if (message == null || message.length == 0) {
        console.error("@LLMChat: Received empty message for LLM request");
      }
      console.log(22);
      //@ts-ignore
      let new_message = {
        author: "user",
        message: message,
        id: this.getNextMessageId(),
      };
      this.messages.push(new_message);
      console.log(3);
      Communication.webservice("triggerEvent", {
        cmid: _this.$store.getters.getCMID,
        action: "llm_request",
        value: JSON.stringify(new_message),
      });
      console.log(4);
      //@ts-ignore
      let message_pos = this.messages.push({
        author: "bot",
        message: "",
        id: this.getNextMessageId(),
      });
      //let message_pos = this.messages.length;

      let postData = new FormData();
      postData.append("model", this.pluginSettings.model);
      postData.append("hostname", this.pluginSettings.llmhostname);
      postData.append("prompt", message);
      //postData.append('coursemoduleid', this.courseModuleID);
      //postData.append('pageinstanceid', this.pageInstanceId);
      console.log("postadata", postData);
      const base = new URL(M.cfg.wwwroot + "/");
      const url = new URL("./mod/openchat/llm_stream.php", base);

      const response = await fetch(url, {
        method: "POST",
        body: postData,
      });

      /*
      // Future work: connect to External API. Currently streaming and no-cache is nt supported by the External API.
      const res = await Communication.webservice("llm_request", {
          model: this.pluginSettings.model,
          hostname: this.pluginSettings.model,
          prompt: message,
      });
      const response = await res;
      */

      if (!response.body) {
        console.error("No response body (stream unsupported)");
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      let completeText = "";
      console.log("before loop", response);
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });

        // Ollama returns JSON per line
        const lines = chunk.split("\n").filter((line) => line.trim() !== "");
        for (const line of lines) {
          try {
            const parsed = JSON.parse(line);
            if (parsed.done) break;
            const content = parsed.response;
            completeText += content;

            // Optionally update a live DOM element
            console.log("Chunk:", content);
            //@ts-ignore
            _this.messages[message_pos - 1].message =
              _this.messages[message_pos - 1].message + content;

            //document.getElementById('output').textContent = completeText;
          } catch (e) {
            console.warn("Failed to parse chunk", line, e);
          }
        }
      }
      Communication.webservice("triggerEvent", {
        cmid: _this.$store.getters.getCMID,
        action: "llm_response",
        value: JSON.stringify(_this.messages[message_pos - 1]),
      });

      console.log("Final response:", completeText);
      //this.messages[message_pos - 1].message = completeText;
    },
  },
  computed: {
    ...mapGetters({
      pluginSettings: "getPluginSettings",
      pageinstanceid: "getPageInstanceId",
      coursemoduleid: "getCourseModuleId",
    }),
  },
});
</script>

<style scoped>
.content {
  border: none;
  max-width: 830px;
  margin: 0 auto;
}

.menu {
  display: block;
  width: 500px;
}

#chat input {
  font-size: 1.1em;
  padding: 2px;
  margin-right: 2px;
}

#chat .chat-input {
  margin-top: 30px;
  padding-top: 10px;
  border-top: #222222 1px solid;
}

#chat .chat-message {
  display: block;
  padding: 8px 10px;
  font-size: 1.1em;
  margin-bottom: 5px;
  width: 300px;
  border-radius: 2% 2%;
  border: solid 1px #555;
}

.settings-icon {
  font-size: 1.5em;
  color: #555;
  cursor: pointer;
}

.settings-icon:hover {
  color: #004c97;
}
</style>
