<template>
  <section class="card card--narrow">
    <h1>Предложить категорию или территорию</h1>
    <p class="muted">
      Блок «Предложить» входит в форму новостного материала (модуль «Подготовка новости»).
      Здесь он показан для проверки работы модуля. Если нужной категории или территории
      нет в списке, журналист вводит её наименование, система сразу сравнивает его
      с действующими записями (без учёта регистра букв, лишних пробелов и «ё»/«е»)
      и выводит ответ.
    </p>
    <form @submit.prevent="submit">
      <label class="field">
        <span>Что предложить</span>
        <select v-model="kind" data-test="kind">
          <option value="category">Категорию</option>
          <option value="territory">Территорию</option>
        </select>
      </label>
      <label class="field">
        <span>Наименование (до 40 символов)</span>
        <input v-model="name" data-test="name" maxlength="40" />
      </label>
      <p v-if="message" class="alert" :class="isError ? 'alert--error' : 'alert--ok'" data-test="message">{{ message }}</p>

      <!-- Третья ветвь: запись есть, но написана иначе -->
      <div v-if="other" class="actions" data-test="other-spelling">
        <button type="button" class="btn btn--ghost" data-test="choose-existing" @click="chooseExisting">
          Выбрать «{{ other.name }}»
        </button>
        <button type="button" class="btn btn--ghost" data-test="report-spelling" @click="reportSpelling">
          Сообщить: правильно «{{ entered }}»
        </button>
      </div>

      <button class="btn" type="submit" data-test="submit">Отправить предложение</button>
    </form>
  </section>
</template>

<script setup>
import { ref } from "vue";
import { api } from "../api.js";

const kind = ref("category");
const name = ref("");
const entered = ref("");
const message = ref("");
const isError = ref(false);
const other = ref(null);   // существующая запись в другом написании

function show(result) {
  message.value = result.message;
  isError.value = !result.saved;
  if (result.saved) name.value = "";
}

async function submit() {
  message.value = "";
  isError.value = false;
  other.value = null;
  entered.value = name.value.trim().replace(/\s+/g, " ");
  try {
    const result = await api.createProposal({ kind: kind.value, name: name.value });
    // Ответ системы журналисту: «уже есть», «есть в другом написании»,
    // «уже ожидает решения» или «отправлено менеджеру»
    show(result);
    if (result.result === "other_spelling") other.value = result.record;
  } catch (e) {
    isError.value = true;
    message.value = e.message;
  }
}

function chooseExisting() {
  // В форме новостного материала здесь выбирается существующая запись
  message.value = `Выбрано: «${other.value.name}»`;
  isError.value = false;
  other.value = null;
  name.value = "";
}

async function reportSpelling() {
  try {
    const result = await api.reportSpelling({ kind: kind.value, record_id: other.value.id, name: entered.value });
    show(result);
    other.value = null;
  } catch (e) {
    isError.value = true;
    message.value = e.message;
  }
}
</script>
