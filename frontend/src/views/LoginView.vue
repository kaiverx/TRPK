<template>
  <section class="card card--narrow">
    <h1>Вход в систему</h1>
    <form @submit.prevent="submit">
      <label class="field">
        <span>Логин</span>
        <input v-model="login" data-test="login" autocomplete="username" />
      </label>
      <label class="field">
        <span>Пароль</span>
        <input v-model="password" type="password" data-test="password" autocomplete="current-password" />
      </label>
      <p v-if="error" class="alert alert--error" data-test="error">{{ error }}</p>
      <button class="btn" type="submit" data-test="submit">Войти</button>
    </form>
  </section>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { api, saveSession } from "../api.js";

const router = useRouter();
const login = ref("");
const password = ref("");
const error = ref("");

async function submit() {
  error.value = "";
  try {
    const data = await api.login(login.value, password.value);
    saveSession(data);
    router.push(data.role === "manager" ? "/manager/proposals" : data.role === "journalist" ? "/journalist/propose" : "/guide");
  } catch (e) {
    error.value = e.message;
  }
}
</script>
