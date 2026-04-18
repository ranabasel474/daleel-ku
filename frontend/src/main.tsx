import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";

//Start the app in the root element
createRoot(document.getElementById("root")!).render(<App />);
