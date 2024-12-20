import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "bootstrap/dist/css/bootstrap.min.css";
import "./styles/custom.css";

const container = document.getElementById("root");
const root = createRoot(container!); // The '!' is a non-null assertion operator
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
