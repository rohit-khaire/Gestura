import axios from "axios";

const BASE_URL =
  import.meta.env.MODE === "development"
    ? "http://localhost:5000/api"
    : "https://sign-detection-m4sm.onrender.com/api";

export const axiosInstance = axios.create({ baseURL: BASE_URL });
