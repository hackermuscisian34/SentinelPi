import axios from "axios";

export function createPiClient(piIp: string, token: string) {
    return axios.create({
        baseURL: `http://${piIp}:8000`,
        timeout: 10000,
        headers: { Authorization: `Bearer ${token}` },
    });
}
