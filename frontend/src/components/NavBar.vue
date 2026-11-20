<template>
  <header class="nav">
    <div class="nav__brand">Новостной портал Приангарья</div>
    <nav class="nav__links">
      <template v-if="session.role === 'manager'">
        <RouterLink to="/manager/proposals" data-test="nav-proposals">Предложения</RouterLink>
        <RouterLink to="/manager/categories" data-test="nav-categories">Категории</RouterLink>
        <RouterLink to="/manager/territories" data-test="nav-territories">Территории</RouterLink>
      </template>
      <RouterLink v-if="session.role === 'journalist'" to="/journalist/propose">Предложить</RouterLink>
      <RouterLink to="/guide" data-test="nav-guide">Руководство</RouterLink>
    </nav>
    <div class="nav__user">
      <template v-if="session.token">
        <span class="nav__name">{{ session.fullName }}</span>
        <button class="btn btn--ghost" data-test="logout" @click="logout">Выйти</button>
      </template>
      <RouterLink v-else to="/login" class="btn btn--ghost">Войти</RouterLink>
    </div>
  </header>
</template>

<script setup>
import { useRouter } from "vue-router";
import { clearSession, session } from "../api.js";

const router = useRouter();

function logout() {
  clearSession();
  router.push("/login");
}
</script>
