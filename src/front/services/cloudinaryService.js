import { getToken } from "./authServices.js";
import { backendUrl } from "./backendUrl.js";

// Subida en tres pasos: el archivo va directo del navegador a Cloudinary (no pasa por la API,
// que en Vercel no admite peticiones de mas de 4,5 MB).
//   1. pedimos al backend una firma para ese archivo (valida tipo, tamaño y permisos)
//   2. subimos el archivo a Cloudinary con esa firma
//   3. confirmamos al backend, que lo comprueba en Cloudinary y lo registra
// `endpoint` es la ruta de la API sin el sufijo, p.ej. /api/shelter/animals/<id>/media
export const uploadSignedMedia = async (endpoint, file, extra = {}) => {
  if (!file) {
    throw new Error("Selecciona un archivo.");
  }

  const signatureResponse = await fetch(`${backendUrl}${endpoint}/upload-signature`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getToken()}`,
    },
    body: JSON.stringify({ content_type: file.type, size: file.size }),
  });
  const firma = await signatureResponse.json().catch(() => ({}));
  if (!signatureResponse.ok) {
    throw new Error(firma.error || firma.message || "No se ha podido preparar la subida");
  }

  const formData = new FormData();
  Object.entries(firma.params).forEach(([clave, valor]) => formData.append(clave, valor));
  formData.append("file", file);

  const uploadResponse = await fetch(firma.upload_url, { method: "POST", body: formData });
  if (!uploadResponse.ok) {
    const data = await uploadResponse.json().catch(() => ({}));
    throw new Error(data?.error?.message || "No se ha podido subir el archivo a Cloudinary");
  }

  const confirmResponse = await fetch(`${backendUrl}${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getToken()}`,
    },
    body: JSON.stringify({ media_id: firma.media_id, resource_type: firma.resource_type, ...extra }),
  });
  const data = await confirmResponse.json().catch(() => ({}));
  if (!confirmResponse.ok) {
    const error = new Error(data.error || data.message || "No se ha podido guardar el archivo");
    error.status = confirmResponse.status;
    throw error;
  }

  return data;
};
