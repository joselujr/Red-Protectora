import { backendUrl } from "./backendUrl.js";

export const getShelterTypes = async () => {
    const response = await fetch(`${backendUrl}/api/shelter-types`);

    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || data.message || "No se han podido cargar los tipos");
    }

    return data.items;
};