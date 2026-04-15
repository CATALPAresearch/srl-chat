<template>
  <div class="landing-page">
    <LandingTeacher v-if="role === 'teacher'" />
    <LandingStudent v-else />
  </div>
</template>

<script>
import Vue from "vue";
import LandingStudent from "./LandingStudent.vue";
import LandingTeacher from "./LandingTeacher.vue";

export default Vue.extend({
  name: "LandingPage",
  components: { LandingStudent, LandingTeacher },
  computed: {
    role() {
      return this.$store.getters.getRole;
    },
  },
});
</script>

<style scoped>
.landing-page {
  width: 100%;
  height: 100%;
  overflow: auto;
}
</style>
