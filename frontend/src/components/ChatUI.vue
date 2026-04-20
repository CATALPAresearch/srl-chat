<template>
  <div id="chat" class="container-fluid px-2 py-3 chat-ui">
    <div class="chat-messages" ref="messageList">
      <div v-for="(m, index) in messages" :key="m.id || index">
        <article
          :class="
            m.author == 'bot'
              ? 'chat-message ml-auto user-bot'
              : 'chat-message user-human'
          "
        >
          <div
            v-if="m.message == ''"
            role="status"
            aria-live="polite"
            aria-atomic="true"
          >
            <font-awesome-icon
              class="fa-spin"
              icon="spinner"
              aria-hidden="true"
            />
            <span class="sr-only">Nachricht wird geladen</span>
          </div>
          <VueShowdown
            :markdown="m.message"
            flavor="github"
            :options="{ emoji: true }"
          />
          <div
            v-if="m.author == 'bot' && m.message != ''"
            class="message-actions"
          >
            <button
              type="button"
              class="btn btn-link"
              aria-label="Antwort kopieren"
              title="Kopieren"
              v-if="!copied"
              @click="copyMessageToClipboard(m.message, index)"
            >
              <font-awesome-icon icon="copy" />
            </button>
            <span v-if="copied" aria-live="assertive" class="copied-feedback">
              <span class="sr-only">Nachricht wurde kopiert</span>
              <font-awesome-icon icon="check" />
            </span>
            <button
              type="button"
              class="btn btn-link"
              aria-label="Antwort positiv bewerten"
              title="Gefällt mir"
              @click="sendRating('up', index)"
            >
              <font-awesome-icon icon="thumbs-up" />
            </button>
            <button
              type="button"
              class="btn btn-link"
              aria-label="Antwort negativ bewerten"
              title="Gefällt mir nicht"
              @click="sendRating('down', index)"
            >
              <font-awesome-icon icon="thumbs-down" />
            </button>
          </div>
        </article>
      </div>
    </div>
    <fieldset>
      <legend class="sr-only">Neue Nachricht schreiben</legend>
      <div class="w-100 chat-input">
        <div>
          <label for="chatTextarea" class="sr-only">Gib deine Frage ein</label>
          <textarea
            ref="chatTextarea"
            class="w50 chat-textarea"
            v-model="chat_message"
            @keyup.enter="handleEnter"
            @input="resizeTextarea"
            placeholder="Frag etwas"
            role="textbox"
          />
          <div class="d-flex justify-content-between align-items-center mb-3">
            <font-awesome-icon
              v-if="is_loading"
              class="fa-spin"
              icon="spinner"
              aria-hidden="true"
            />
            <span v-else style="width: 1em; display: inline-block" />

            <button
              type="button"
              class="btn btn-primary"
              @click="handleChatMessage"
              :disabled="chat_message.length == 0 || is_loading"
            >
              <font-awesome-icon icon="arrow-up" />
            </button>
          </div>
        </div>
      </div>
    </fieldset>
  </div>
</template>

<script lang="ts">
import Vue from "vue";
import { mapGetters, mapState } from "vuex";
import Communication from "../classes/communication";
import { VueShowdown } from "vue-showdown";

export default Vue.extend({
  name: "ChatUI",
  props: {
    messages: Object,
    is_loading: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      chat_message: "",
      error_msg: "",
      copied: false,
    };
  },
  components: {
    VueShowdown: VueShowdown,
  },
  computed: {
    ...mapState(["strings"]),
  },
  mounted: function () {},
  watch: {
    messages: {
      deep: true,
      handler() {
        this.$nextTick(() => {
          const el = this.$refs.messageList;
          if (el) el.scrollTop = el.scrollHeight;
        });
      },
    },
  },
  methods: {
    ...mapGetters({
      //rag_webservice_host: 'getRAGWebserviceHost',
    }),
    handleEnter(event) {
      if (event.shiftKey) {
        return;
      }
      this.handleChatMessage();
    },
    handleChatMessage: function () {
      this.$emit("requestChatResponse", this.chat_message);
      this.chat_message = ""; // reset input field
      this.$nextTick(() => {
        this.$refs.chatTextarea.focus();
      });
    },
    resizeTextarea: function () {
      const textarea = this.$refs.chatTextarea;
      textarea.style.height = "auto"; // Reset height
      textarea.style.height = textarea.scrollHeight + "px"; // Set height dynamically
    },
    copyMessageToClipboard: function (text, message_index) {
      var _this = this;
      navigator.clipboard
        .writeText(text)
        .then(() => {
          this.copied = true;
          setTimeout(() => (this.copied = false), 2000);
        })
        .catch((err) => {
          console.error("Failed to copy:", err);
        });
      Communication.webservice("triggerEvent", {
        cmid: _this.$store.getters.getCMID,
        action: "copy_response",
        value: JSON.stringify({ copied: text, index: message_index }),
      });
    },
    sendRating: function (rating, message_index) {
      var _this = this;
      let params = {
        request: this.messages[message_index - 1],
        response: this.messages[message_index],
        rating: rating,
      };
      Communication.webservice("triggerEvent", {
        cmid: _this.$store.getters.getCMID,
        action: "rate_response_" + rating == "up" ? "positive" : "negative",
        value: JSON.stringify({ index: message_index }),
      });
    },
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

.chat-ui {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-messages {
  flex: 1 1 0;
  min-height: 0;
  overflow-y: auto;
  padding-right: 4px;
}

#chat .chat-textarea {
  min-height: 40px;
  max-height: 300px;
  overflow-y: auto;
  width: 100%;
  resize: none;
  font-size: 1.1em;
  padding: 2px;
  margin-right: 2px;
}

#chat .chat-input {
  flex-shrink: 0;
  margin-top: 2px;
  padding-top: 10px;
}

#chat .chat-message {
  display: block;
  /*padding: 8px 10px;*/
  font-size: 1.1em;
  padding: 1rem;
  border-radius: 5px;
  margin-bottom: 0.75rem;
  word-break: break-word;
}

.user-bot {
  background-color: #fff;
}

.user-human {
  background-color: #d9edf7;
  border-color: 0 solid #d9edf7;
}

.message-actions {
  margin-top: 10px;
  min-height: 20px;
}

.message-actions * {
  display: inline;
  margin-right: 10px;
  font-size: 1.1em;
  color: #7d7575;
  border-radius: 4px;
  padding: 5px;
}

.message-actions *:hover {
  background-color: #dadde4;
}

.message-bot:hover .message-actions * {
  display: inline;
}
</style>
