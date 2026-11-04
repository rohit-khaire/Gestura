import { axiosInstance } from "./axios";

// Creates a guest user on the server and returns { id, name, token }
export async function createGuest(name) {
  const { data } = await axiosInstance.post("/chat/guest", { name });
  return data;
}
