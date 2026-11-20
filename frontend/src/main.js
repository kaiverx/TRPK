import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";

import App from "./App.vue";
import { session } from "./api.js";
import LoginView from "./views/LoginView.vue";
import ProposalsView from "./views/ProposalsView.vue";
import CategoriesView from "./views/CategoriesView.vue";
import TerritoriesView from "./views/TerritoriesView.vue";
import ProposeView from "./views/ProposeView.vue";
import GuideView from "./views/GuideView.vue";
import "./style.css";

const routes = [
  { path: "/", redirect: "/login" },
  { path: "/login", component: LoginView },
  { path: "/manager/proposals", component: ProposalsView, meta: { role: "manager" } },
  { path: "/manager/categories", component: CategoriesView, meta: { role: "manager" } },
  { path: "/manager/territories", component: TerritoriesView, meta: { role: "manager" } },
  { path: "/journalist/propose", component: ProposeView, meta: { role: "journalist" } },
  { path: "/guide", component: GuideView },
];

const router = createRouter({ history: createWebHistory(), routes });

// Страницы менеджера и журналиста открываются только после входа с нужной ролью.
router.beforeEach((to) => {
  if (to.meta.role && session.role !== to.meta.role) return "/login";
  return true;
});

createApp(App).use(router).mount("#app");
