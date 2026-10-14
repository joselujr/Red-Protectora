import React from 'react'
import ReactDOM from 'react-dom/client'
import './bootstrap.css'  // Global styles for your application
import './index.css'  // Global styles for your application
import { RouterProvider } from "react-router-dom";  // Import RouterProvider to use the router
import { router } from "./routes/routes.jsx";  // Import the router configuration
import { StoreProvider } from './hooks/useGlobalReducer';  // Import the StoreProvider for global state management
import { BackendURL } from './components/BackendURL';

const Main = () => {

    // en desarrollo el backend corre en otro puerto y hace falta VITE_BACKEND_URL;
    // en produccion (Vercel) la API esta en el mismo dominio y puede ir vacia
    if (import.meta.env.DEV && !import.meta.env.VITE_BACKEND_URL) return (
        <React.StrictMode>
            <BackendURL />
        </React.StrictMode>
    );
    return (
        <React.StrictMode>
            {/* Provide global state to all components */}
            <StoreProvider>
                {/* Set up routing for the application */}
                <RouterProvider router={router}>
                </RouterProvider>
            </StoreProvider>
        </React.StrictMode>
    );
}

// Render the Main component into the root DOM element.
ReactDOM.createRoot(document.getElementById('root')).render(<Main />)
