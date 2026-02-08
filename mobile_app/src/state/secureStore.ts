import * as Keychain from "react-native-keychain";

const TOKEN_KEY = "sentinelpi_token";
const PI_IP_KEY = "sentinelpi_pi_ip";

export async function saveToken(token: string) {
  await Keychain.setGenericPassword(TOKEN_KEY, token, { service: TOKEN_KEY });
}

export async function getToken(): Promise<string | null> {
  const creds = await Keychain.getGenericPassword({ service: TOKEN_KEY });
  return creds ? creds.password : null;
}

export async function savePiIp(ip: string) {
  await Keychain.setGenericPassword(PI_IP_KEY, ip, { service: PI_IP_KEY });
}

export async function getPiIp(): Promise<string | null> {
  const creds = await Keychain.getGenericPassword({ service: PI_IP_KEY });
  return creds ? creds.password : null;
}

export async function clearAll() {
  await Keychain.resetGenericPassword({ service: TOKEN_KEY });
  await Keychain.resetGenericPassword({ service: PI_IP_KEY });
}
