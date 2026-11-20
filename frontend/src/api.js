// Обращение к серверной части (backend) по HTTP.
// Все запросы проходят через функцию request(), которая добавляет
// токен пользователя и превращает ответ сервера в понятную ошибку.

import { reactive } from "vue";

// Данные вошедшего пользователя хранятся в памяти браузера на время сеанса.
export const session = reactive({
  token: sessionStorage.getItem("token") || "",
  fullName: sessionStorage.getItem("fullName") || "",
  role: sessionStorage.getItem("role") || "",
});

export function saveSession(data) {
  session.token = data.token;
  session.fullName = data.full_name;
  session.role = data.role;
  sessionStorage.setItem("token", data.token);
  sessionStorage.setItem("fullName", data.full_name);
  sessionStorage.setItem("role", data.role);
}

export function clearSession() {
  session.token = "";
  session.fullName = "";
  session.role = "";
  sessionStorage.clear();
}

async function request(method, url, body) {
  const headers = { "Content-Type": "application/json" };
  if (session.token) headers.Authorization = `Bearer ${session.token}`;
  const response = await fetch(url, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Не удалось выполнить действие. Повторите попытку");
  }
  return data;
}

export const api = {
  login: (login, password) => request("POST", "/api/auth/login/", { login, password }),

  // all = true – полный список вместе с заблокированными (страницы менеджера)
  getCategories: (all = false) => request("GET", `/api/categories/${all ? "?all=true" : ""}`),
  addCategory: (data) => request("POST", "/api/categories/", data),
  updateCategory: (id, data) => request("PATCH", `/api/categories/${id}/`, data),
  blockCategory: (id, blocked) => request("POST", `/api/categories/${id}/${blocked ? "block" : "unblock"}/`),

  getTerritories: (all = false) => request("GET", `/api/territories/${all ? "?all=true" : ""}`),
  addTerritory: (data) => request("POST", "/api/territories/", data),
  updateTerritory: (id, data) => request("PATCH", `/api/territories/${id}/`, data),
  blockTerritory: (id, blocked) => request("POST", `/api/territories/${id}/${blocked ? "block" : "unblock"}/`),

  getProposals: () => request("GET", "/api/proposals/"),
  createProposal: (data) => request("POST", "/api/proposals/", data),
  reportSpelling: (data) => request("POST", "/api/proposals/spelling/", data),
  acceptProposal: (id, data) => request("POST", `/api/proposals/${id}/accept/`, data),
};
