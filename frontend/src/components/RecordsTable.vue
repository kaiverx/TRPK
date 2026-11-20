<template>
  <section class="card">
    <div class="card__head">
      <div>
        <h1>{{ isCategory ? "Категории" : "Территории" }}</h1>
        <p class="muted">{{ hint }}</p>
      </div>
      <button class="btn" data-test="add" @click="openAdd">{{ isCategory ? "Добавить категорию" : "Добавить территорию" }}</button>
    </div>

    <p v-if="message" class="alert alert--ok" data-test="message">{{ message }}</p>
    <p v-if="error" class="alert alert--error" data-test="error">{{ error }}</p>

    <table class="table" :data-test="isCategory ? 'categories-table' : 'territories-table'">
      <thead>
        <tr>
          <th>Наименование</th>
          <th v-if="isCategory">Описание</th>
          <th>Состояние</th>
          <th>Дата изменения</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in records" :key="r.id" :class="{ 'row--blocked': r.is_blocked }">
          <td>{{ r.name }}</td>
          <td v-if="isCategory" class="muted">{{ r.description || "–" }}</td>
          <td>
            <span class="tag" :class="r.is_blocked ? 'tag--blocked' : 'tag--active'" data-test="state">
              {{ r.is_blocked ? "заблокирована" : "действует" }}
            </span>
          </td>
          <td>{{ formatDate(r.updated_at) }}</td>
          <td class="right nowrap">
            <button v-if="!r.is_blocked" class="btn btn--small btn--ghost" data-test="edit" @click="openEdit(r)">Изменить</button>
            <button class="btn btn--small btn--ghost" data-test="block" @click="toggleBlock(r)">
              {{ r.is_blocked ? "Снять блокировку" : "Заблокировать" }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </section>

  <StructureForm
    v-if="form"
    :kind="kind"
    :mode="form.mode"
    :initial="form.record"
    :note="form.mode === 'edit' ? editNote : ''"
    :submit="form.submit"
    @saved="onSaved"
    @cancel="form = null"
  />
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { api } from "../api.js";
import StructureForm from "./StructureForm.vue";

const props = defineProps({ kind: { type: String, required: true } });

const isCategory = computed(() => props.kind === "category");
const word = computed(() => (isCategory.value ? "Категория" : "Территория"));
const hint = computed(() =>
  isCategory.value
    ? "Темы, к которым журналист относит новость. Список упорядочен по алфавиту. Заблокированная категория не выдаётся журналисту для выбора, но остаётся у опубликованных новостей."
    : "Места, к которым относятся новости; вид места не ограничивается. Список упорядочен по алфавиту. Заблокированная территория не выдаётся журналисту для выбора, но остаётся у опубликованных новостей."
);
const editNote =
  "Изменяйте запись, только если она ещё не указана в опубликованных новостях. Если запись уже использована, заблокируйте её и добавьте новую.";

const records = ref([]);
const form = ref(null);
const message = ref("");
const error = ref("");

const load = () => (isCategory.value ? api.getCategories(true) : api.getTerritories(true));
const add = (data) => (isCategory.value ? api.addCategory(data) : api.addTerritory(data));
const update = (id, data) => (isCategory.value ? api.updateCategory(id, data) : api.updateTerritory(id, data));
const block = (id, b) => (isCategory.value ? api.blockCategory(id, b) : api.blockTerritory(id, b));

function formatDate(value) {
  return value ? new Date(value).toLocaleDateString("ru-RU") : "";
}

async function fetchRecords() {
  records.value = await load();
}

function openAdd() {
  message.value = error.value = "";
  form.value = { mode: "add", record: {}, submit: add };
}

function openEdit(record) {
  message.value = error.value = "";
  form.value = { mode: "edit", record, submit: (data) => update(record.id, data) };
}

async function toggleBlock(record) {
  message.value = error.value = "";
  try {
    const result = await block(record.id, !record.is_blocked);
    message.value = `${word.value} «${result.name}» ${result.is_blocked ? "заблокирована" : "снова действует"}`;
    fetchRecords();
  } catch (e) {
    error.value = e.message;
  }
}

function onSaved(record) {
  message.value = `${word.value} «${record.name}» сохранена`;
  form.value = null;
  fetchRecords();
}

onMounted(fetchRecords);
</script>
