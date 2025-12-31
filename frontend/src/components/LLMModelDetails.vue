<template>
    <div>
        This component is still under development
    </div>
</template>

<script lang="ts">
import Vue from "vue";
import { mapGetters } from 'vuex'

export default Vue.extend({
    name: "LLMModelDetails",
    data() {
        return {
            modelDetails: [],
            modelDescriptions:
            {
                "llama3": {
                    "language": "Multilingual",
                    "use_case": "General-purpose tasks, including reasoning, summarization, and code",
                    "speed": "70",
                    "accuracy": "9",
                    "strengths": "Improved reasoning, multilingual understanding, better safety alignment",
                    "limitations": "Large memory footprint; slower on CPU-only systems",
                    "context_length": "8192",
                    "model_size": "8B",
                    "alignment_level": "High",
                    "open_source": "Yes, Meta license (non-commercial)",
                    "huggingface": "https://huggingface.co/meta-llama/Meta-Llama-3-8B"
                },
                "phi4": {
                    "language": "English only",
                    "use_case": "Education, lightweight assistants, instructional content",
                    "speed": "130",
                    "accuracy": "7",
                    "strengths": "Compact, high efficiency on limited hardware",
                    "limitations": "Weaker performance on complex reasoning; English only",
                    "context_length": "4096",
                    "model_size": "3.8B",
                    "alignment_level": "Medium",
                    "open_source": "Yes, MIT license",
                    "huggingface": "https://huggingface.co/microsoft/phi-2"
                }
                "mistral": {
                    "language": "Multilingual",
                    "use_case": "Coding, Q&A, summarization",
                    "speed": "80",
                    "accuracy": "9",
                    "strengths": "Fast, highly efficient, good for edge/local devices",
                    "limitations": "Smaller context length than competitors",
                    "context_length": "8192",
                    "model_size": "7B",
                    "alignment_level": "Low",
                    "open_source": "Yes, Apache 2.0",
                    "huggingface": "https://huggingface.co/mistralai/Mistral-7B-v0.1"
                },
                "mixtral": {
                    "language": "Multilingual",
                    "use_case": "High-performance text generation, summarization, reasoning",
                    "speed": "100",
                    "accuracy": "9",
                    "strengths": "Mixture-of-Experts for high throughput",
                    "limitations": "Very large, more GPU-intensive",
                    "context_length": "32768",
                    "model_size": "12.9B (active parameters)",
                    "alignment_level": "Medium",
                    "open_source": "Yes, Apache 2.0",
                    "huggingface": "https://huggingface.co/mistralai/Mixtral-8x7B-Instruct-v0.1"
                },
                "deepseek": {
                    "language": "English only",
                    "use_case": "Scientific tasks, code generation, math",
                    "speed": "60",
                    "accuracy": "8",
                    "strengths": "Strong math & code skills",
                    "limitations": "Limited multilingual support",
                    "context_length": "4096",
                    "model_size": "7B",
                    "alignment_level": "Medium",
                    "open_source": "Yes, MIT license",
                    "huggingface": "https://huggingface.co/deepseek-ai/deepseek-llm-7b-base"
                },

                "gemma": {
                    "language": "English only",
                    "use_case": "Conversational tasks, chatbot development",
                    "speed": "90",
                    "accuracy": "7",
                    "strengths": "Fast and light, optimized for Google TPU/GPU",
                    "limitations": "Limited multilingual support",
                    "context_length": "8192",
                    "model_size": "7B",
                    "alignment_level": "Medium",
                    "open_source": "Yes, Apache 2.0",
                    "huggingface": "https://huggingface.co/google/gemma-7b"
                }
            }

        };
    },
    mounted: function () { },
    methods: {
        listModels: async function () {
            const base = new URL(this.$store.getters.getPluginSettings.hostname);
            const url = new URL("./api/tags", base);
            const response = await fetch(url);
            const data = await response.json();
            return data.models;
        },
        getModelDetails: async function (modelName) {
            const base = new URL(this.$store.getters.getPluginSettings.hostname);
            const url = new URL("./api/show", base);
            const response = await fetch(url.href, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name: modelName })
            });

            const data = await response.json();
            return data;
        },
        loadModelDetails: async function () {
            const models = await this.listModels();
            const detailedModels = [];
            let details = null;
            for (const model of models) {
                details = await this.getModelDetails(model.name); // or model.model
                //@ts-ignore 
                detailedModels.push(details);
            }
            console.log(detailedModels);
        }
    }
});