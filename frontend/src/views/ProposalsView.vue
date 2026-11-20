<template>
  <section class="card">
    <div class="card__head">
      <div>
        <h1>Предложения журналистов</h1>
        <p class="muted">Предложения в состоянии «новое» в порядке поступления: старые сверху, новые внизу.
          «Добавить» – такой записи нет, проверьте наименование и добавьте запись.
          «Исправить написание» – существующая запись записана с ошибкой: она будет заблокирована
          (опубликованные новости останутся с ней), а запись в правильном написании – добавлена.</p>
      </div>
    </div>

    <p v-if="message" class="alert alert--ok" data-test="message">{{ message }}</p>
    <p v-if="loadError" class="alert alert--error">{{ loadError }}</p>

    <table v-if="proposals.length" class="table" data-test="proposals-table">
      <thead>
        <tr><th>Что предложено</th><th>Цель</th><th>Наименование</th><th>Кто предложил</th><th>Дата</th><th></th></tr>
      </thead>
      <tbody>
        <tr v-for="p in proposals" :key="p.id">
          <td><span class="tag" :class="p.kind">{{ p.kind === "category" ? "Категория" : "Территория" }}</span></td>
          <td>
            <span v-if="p.purpose === 'fix'" class="tag tag--fix">Исправить написание</span>
            <span v-else class="tag">Добавить</span>
          </td>
          <td>
            <template v-if="p.purpose === 'fix'">«{{ p.record_name }}» → «{{ p.name }}»</template>
            <template v-else>{{ p.name }}</template>
          </td>
          <td>{{ p.proposed_by_name }}</td>
          <td>{{ formatDate(p.created_at) }}</td>
          <td class="right"><button class="btn btn--small" data-test="accept" @click="openAccept(p)">{{ p.purpose === "fix" ? "Исправить" : "Добавить" }}</button></td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="!loading" class="empty" data-test="empty">Новых предложений нет</p>
  </section>

  <StructureForm
    v-if="selected"
    :kind="selected.kind"
    :mode="selected.purpose === 'fix' ? 'fix' : 'accept'"
    :initial="{ name: selected.name }"
    :note="selected.purpose === 'fix' ? `Запись «${selected.record_name}» будет заблокирована, вместо неё будет добавлена запись с наименованием из формы.` : ''"
    :submit="(data) => api.acceptProposal(selected.id, data)"
    @saved="onSaved"
    @cancel="selected = null"
  />
</template>

<script setup>
import { onMounted, ref } from "vue";
import { api } from "../api.js";
import StructureForm from "../components/StructureForm.vue";

const proposals = ref([]);
const selected = ref(null);
const loading = ref(true);
const loadError = ref("");
const message = ref("");

function formatDate(value) {
  return value ? new Date(value).toLocaleDateString("ru-RU") : "";
}

async function fetchProposals() {
  loading.value = true;
  try {
    proposals.value = await api.getProposals();
  } catch (e) {
    loadError.value = e.message;
  } finally {
    loading.value = false;
  }
}

function openAccept(proposal) {
  message.value = "";
  selected.value = proposal;
}

function onSaved(record) {
  const what = selected.value.kind === "category" ? "Категория" : "Территория";
  message.value = selected.value.purpose === "fix"
    ? `Написание исправлено: «${selected.value.record_name}» заблокирована, «${record.name}» добавлена`
    : `${what} «${record.name}» добавлена`;
  selected.value = null;
  fetchProposals();
}

onMounted(fetchProposals);
</script>
