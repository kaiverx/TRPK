<template>
  <div class="modal" role="dialog" aria-modal="true">
    <form class="modal__window" data-test="structure-form" @submit.prevent="save">
      <h2>{{ title }}</h2>

      <p v-if="note" class="muted" data-test="form-note">{{ note }}</p>

      <label class="field">
        <span>Наименование {{ kind === "category" ? "категории" : "территории" }} * (до 40 символов)</span>
        <input v-model="form.name" data-test="field-name" maxlength="40" />
      </label>

      <label v-if="kind === 'category'" class="field">
        <span>Описание категории (до 150 символов)</span>
        <textarea v-model="form.description" data-test="field-description" rows="3" maxlength="150"></textarea>
      </label>


      <p v-if="error" class="alert alert--error" data-test="form-error">{{ error }}</p>

      <div class="modal__actions">
        <button type="button" class="btn btn--ghost" data-test="cancel" @click="$emit('cancel')">Отмена</button>
        <button type="submit" class="btn" data-test="save" :disabled="saving">Сохранить</button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from "vue";

const props = defineProps({
  kind: { type: String, required: true },      // "category" или "territory"
  mode: { type: String, required: true },      // "add", "accept" (добавление по предложению) или "edit"
  initial: { type: Object, default: () => ({}) },
  submit: { type: Function, required: true },  // функция отправки данных на сервер
  note: { type: String, default: "" },         // пояснение над полями формы
});
const emit = defineEmits(["saved", "cancel"]);

const form = reactive({
  name: props.initial.name || "",
  description: props.initial.description || "",
});
const error = ref("");
const saving = ref(false);

const title = computed(() => {
  const what = props.kind === "category" ? "категории" : "территории";
  if (props.mode === "edit") return `Изменение ${what}`;
  if (props.mode === "fix") return `Исправление написания ${what}`;
  return `Добавление ${what}`;
});

// Проверка формы до отправки на сервер: те же правила, что и на сервере.
function validateForm() {
  const name = form.name.trim().replace(/\s+/g, " ");
  if (name.length < 2) return "Наименование должно содержать не менее 2 символов";
  if (name.length > 40) return "Наименование должно содержать не более 40 символов";
  return "";
}

function buildData() {
  const name = form.name.trim().replace(/\s+/g, " ");
  return props.kind === "category"
    ? { name, description: form.description.trim() }
    : { name };
}

async function save() {
  error.value = validateForm();
  if (error.value) return;
  saving.value = true;
  try {
    const result = await props.submit(buildData());
    emit("saved", result);
  } catch (e) {
    error.value = e.message;
  } finally {
    saving.value = false;
  }
}
</script>
