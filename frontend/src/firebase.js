import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

// Your web app's Firebase configuration
// For development, these can be placeholders if running locally without a real project yet.
// In production, these should be populated via VITE_ env variables.
const firebaseConfig = {
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "",
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "",
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "",
    storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "",
    messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "",
    appId: import.meta.env.VITE_FIREBASE_APP_ID || "",
};

// Initialize Firebase gracefully
let app;
let auth;

try {
    if (firebaseConfig.apiKey && firebaseConfig.apiKey !== "") {
        app = initializeApp(firebaseConfig);
        auth = getAuth(app);
    } else {
        console.warn("Firebase Config Missing: defaulting to mock mode (auth will fail)");
    }
} catch (error) {
    console.error("Firebase Initialization Failed:", error);
}

export { auth };
