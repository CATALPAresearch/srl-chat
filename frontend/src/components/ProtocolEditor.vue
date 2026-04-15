<template>
  <div class="protocol-editor">
    <h2>Interview Protocol Editor</h2>

    <!-- Protocol List -->
    <div class="protocol-list-section">
      <div class="section-header">
        <h4>Protocols</h4>
        <div>
          <button class="btn btn-primary btn-sm mr-2" @click="showCreateModal = true">+ New Protocol</button>
          <label class="btn btn-secondary btn-sm">
            Import JSON
            <input type="file" accept=".json" style="display:none" @change="importProtocol" />
          </label>
        </div>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>Protocol Name</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in protocols" :key="p.name">
            <td>{{ p.name }}</td>
            <td>
              <button class="btn btn-sm btn-info mr-1" @click="loadProtocol(p.name)">Edit</button>
              <button class="btn btn-sm btn-success mr-1" @click="exportProtocol(p.name)">Export</button>
              <button class="btn btn-sm btn-danger" @click="deleteProtocol(p.name)" :disabled="p.name === 'interview_default'">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Protocol Editor -->
    <div v-if="selectedProtocol" class="editor-section">
      <div class="section-header">
        <h4>Editing: {{ selectedProtocolName }}</h4>
        <button class="btn btn-success btn-sm" @click="saveProtocol">Save Changes</button>
      </div>

      <div v-for="(langData, lang) in selectedProtocol" :key="lang" class="lang-section">
        <h5>Language: {{ lang.toUpperCase() }}</h5>

        <!-- Contexts -->
        <div class="subsection">
          <h6>Contexts</h6>
          <div v-for="(ctx, idx) in langData.contexts" :key="idx" class="context-row">
            <input class="form-control form-control-sm" v-model="langData.contexts[idx]" />
            <button class="btn btn-sm btn-danger ml-1" @click="removeContext(langData, idx)">×</button>
          </div>
          <button class="btn btn-sm btn-secondary mt-1" @click="addContext(langData)">+ Add Context</button>
        </div>

        <!-- Categories & Strategies -->
        <div class="subsection">
          <h6>Categories & Strategies</h6>
          <div v-for="(cat, catIdx) in langData.categories" :key="cat.id" class="category-card">
            <div class="category-header">
              <input class="form-control form-control-sm category-name" v-model="cat.name" placeholder="Category name" />
              <button class="btn btn-sm btn-danger ml-1" @click="removeCategory(langData, catIdx)">Delete Category</button>
            </div>
            <textarea class="form-control form-control-sm mt-1" v-model="cat.description" rows="2" placeholder="Category description"></textarea>

            <!-- Strategies -->
            <div class="strategies-list">
              <div v-for="(strat, sIdx) in cat.strategies" :key="strat.id" class="strategy-row">
                <input class="form-control form-control-sm" v-model="strat.name" placeholder="Strategy name" />
                <textarea class="form-control form-control-sm mt-1" v-model="strat.description" rows="2" placeholder="Strategy description"></textarea>
                <button class="btn btn-sm btn-danger mt-1" @click="removeStrategy(cat, sIdx)">Remove Strategy</button>
              </div>
              <button class="btn btn-sm btn-secondary mt-1" @click="addStrategy(cat)">+ Add Strategy</button>
            </div>
          </div>
          <button class="btn btn-sm btn-primary mt-2" @click="addCategory(langData)">+ Add Category</button>
        </div>
      </div>
    </div>

    <!-- Create Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal-box">
        <h4>Create New Protocol</h4>
        <label>Protocol Name</label>
        <input class="form-control" v-model="newProtocolName" placeholder="e.g. interview_custom" />
        <div class="mt-3">
          <button class="btn btn-primary mr-2" @click="createProtocol">Create</button>
          <button class="btn btn-secondary" @click="showCreateModal = false">Cancel</button>
        </div>
      </div>
    </div>

    <!-- Status message -->
    <div v-if="statusMsg" class="alert mt-3" :class="statusType === 'error' ? 'alert-danger' : 'alert-success'">
      {{ statusMsg }}
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "ProtocolEditor",
  data() {
    return {
      protocols: [],
      selectedProtocol: null,
      selectedProtocolName: null,
      showCreateModal: false,
      newProtocolName: "",
      statusMsg: "",
      statusType: "success",
      host: "http://localhost:5000",
    };
  },
  async mounted() {
    await this.loadProtocolList();
  },
  methods: {
    async loadProtocolList() {
      try {
        const res = await axios.get(`${this.host}/protocols`);
        this.protocols = res.data;
      } catch (e) {
        this.showStatus("Failed to load protocols: " + e.message, "error");
      }
    },
    async loadProtocol(name) {
      try {
        const res = await axios.get(`${this.host}/protocols/${name}`);
        this.selectedProtocol = res.data;
        this.selectedProtocolName = name;
      } catch (e) {
        this.showStatus("Failed to load protocol: " + e.message, "error");
      }
    },
    async saveProtocol() {
      try {
        await axios.put(`${this.host}/protocols/${this.selectedProtocolName}`, this.selectedProtocol);
        this.showStatus("Protocol saved successfully!", "success");
      } catch (e) {
        this.showStatus("Failed to save: " + e.message, "error");
      }
    },
    async createProtocol() {
      if (!this.newProtocolName) return;
      const emptyProtocol = {
        en: { contexts: [], categories: [] },
        de: { contexts: [], categories: [] }
      };
      try {
        await axios.post(`${this.host}/protocols`, {
          name: this.newProtocolName,
          protocol: emptyProtocol
        });
        this.showCreateModal = false;
        this.newProtocolName = "";
        await this.loadProtocolList();
        this.showStatus("Protocol created!", "success");
      } catch (e) {
        this.showStatus("Failed to create: " + e.message, "error");
      }
    },
    async deleteProtocol(name) {
      if (!confirm(`Delete protocol "${name}"?`)) return;
      try {
        await axios.delete(`${this.host}/protocols/${name}`);
        this.selectedProtocol = null;
        this.selectedProtocolName = null;
        await this.loadProtocolList();
        this.showStatus("Protocol deleted!", "success");
      } catch (e) {
        this.showStatus("Failed to delete: " + e.message, "error");
      }
    },
    exportProtocol(name) {
      window.open(`${this.host}/protocols/${name}/export`, "_blank");
    },
    async importProtocol(event) {
      const file = event.target.files[0];
      if (!file) return;
      const formData = new FormData();
      formData.append("file", file);
      try {
        await axios.post(`${this.host}/protocols/import`, formData, {
          headers: { "Content-Type": "multipart/form-data" }
        });
        await this.loadProtocolList();
        this.showStatus("Protocol imported!", "success");
      } catch (e) {
        this.showStatus("Failed to import: " + e.message, "error");
      }
    },
    addContext(langData) {
      langData.contexts.push("");
    },
    removeContext(langData, idx) {
      langData.contexts.splice(idx, 1);
    },
    addCategory(langData) {
      const id = String(langData.categories.length + 1).padStart(3, "0");
      langData.categories.push({ id, name: "", description: "", strategies: [] });
    },
    removeCategory(langData, idx) {
      langData.categories.splice(idx, 1);
    },
    addStrategy(cat) {
      const id = `${cat.id}-${String(cat.strategies.length + 1).padStart(3, "0")}`;
      cat.strategies.push({ id, name: "", description: "" });
    },
    removeStrategy(cat, idx) {
      cat.strategies.splice(idx, 1);
    },
    showStatus(msg, type) {
      this.statusMsg = msg;
      this.statusType = type;
      setTimeout(() => { this.statusMsg = ""; }, 4000);
    },
  },
};
</script>

<style scoped>
.protocol-editor { padding: 20px; overflow-y: auto; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.protocol-list-section { margin-bottom: 32px; }
.data-table { width: 100%; border-collapse: collapse; margin-bottom: 16px; }
.data-table th, .data-table td { border: 1px solid #dee2e6; padding: 8px 12px; text-align: left; }
.data-table th { background: #f8f9fa; }
.editor-section { background: #fafafa; border: 1px solid #eee; border-radius: 8px; padding: 20px; }
.lang-section { margin-bottom: 24px; }
.subsection { margin-bottom: 16px; padding: 12px; background: white; border: 1px solid #eee; border-radius: 6px; }
.context-row { display: flex; align-items: center; margin-bottom: 6px; }
.category-card { background: #f0f4ff; border: 1px solid #c5d0e6; border-radius: 6px; padding: 12px; margin-bottom: 12px; }
.category-header { display: flex; align-items: center; }
.category-name { flex: 1; }
.strategies-list { margin-top: 10px; padding-left: 12px; border-left: 3px solid #007bff; }
.strategy-row { background: white; border: 1px solid #dee2e6; border-radius: 4px; padding: 8px; margin-bottom: 8px; }
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 9999; }
.modal-box { background: white; border-radius: 8px; padding: 24px; width: 400px; }
.mr-1 { margin-right: 4px; }
.mr-2 { margin-right: 8px; }
.ml-1 { margin-left: 4px; }
.mt-1 { margin-top: 6px; }
.mt-2 { margin-top: 10px; }
.mt-3 { margin-top: 16px; }
</style>
