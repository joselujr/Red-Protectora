// URL base del backend. En Vercel frontend y API comparten dominio, asi que puede quedar vacia
// y las llamadas salen relativas (/api/...). En local se define VITE_BACKEND_URL en el .env.
export const backendUrl = (import.meta.env.VITE_BACKEND_URL || "").replace(/\/+$/, "");
