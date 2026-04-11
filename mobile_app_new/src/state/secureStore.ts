import * as SecureStore from "expo-secure-store";

const TOKEN_KEY = "sentinelpi_token";
const PI_IP_KEY = "sentinelpi_pi_ip";

export async function saveToken(token: string) {
    await SecureStore.setItemAsync(TOKEN_KEY, token);
}

export async function getToken(): Promise<string | null> {
    return await SecureStore.getItemAsync(TOKEN_KEY);
}

export async function savePiIp(ip: string) {
    await SecureStore.setItemAsync(PI_IP_KEY, ip);
}

export async function getPiIp(): Promise<string | null> {
    return await SecureStore.getItemAsync(PI_IP_KEY);
}

export async function clearAll() {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    await SecureStore.deleteItemAsync(PI_IP_KEY);
    await SecureStore.deleteItemAsync(USER_EMAIL_KEY);
}

const USER_EMAIL_KEY = "sentinelpi_user_email";

export async function saveUserEmail(email: string) {
    await SecureStore.setItemAsync(USER_EMAIL_KEY, email);
}

export async function getUserEmail(): Promise<string | null> {
    return await SecureStore.getItemAsync(USER_EMAIL_KEY);
}
