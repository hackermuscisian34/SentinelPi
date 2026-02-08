import React, { useState } from "react";
import { View, Text, TextInput, TouchableOpacity, StyleSheet } from "react-native";
import { theme } from "../ui/theme";
import { getPiIp, getToken } from "../state/secureStore";
import { createPiClient } from "../api/pi";

export default function PairingScreen() {
  const [deviceName, setDeviceName] = useState("");
  const [code, setCode] = useState("");
  const [expires, setExpires] = useState("");
  const [error, setError] = useState("");

  const generate = async () => {
    setError("");
    try {
      const token = await getToken();
      const piIp = await getPiIp();
      if (!token || !piIp) {
        setError("Missing login session or Pi IP.");
        return;
      }
      const client = createPiClient(piIp, token);
      const resp = await client.post("/pairing", { device_name: deviceName || "Windows Agent" });
      setCode(resp.data.pairing_code);
      setExpires(resp.data.expires_at);
    } catch {
      setError("Failed to generate pairing code.");
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Pairing Code</Text>
      <TextInput placeholder="Device name" style={styles.input} value={deviceName} onChangeText={setDeviceName} />
      <TouchableOpacity style={styles.button} onPress={generate}>
        <Text style={styles.buttonText}>Generate</Text>
      </TouchableOpacity>
      {code ? (
        <View style={styles.card}>
          <Text style={styles.code}>{code}</Text>
          <Text style={styles.small}>Expires: {expires}</Text>
        </View>
      ) : null}
      {error ? <Text style={styles.error}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: theme.colors.background },
  title: { fontSize: 20, fontWeight: "700", marginBottom: 10, color: theme.colors.text },
  input: { backgroundColor: "#f0f7f1", padding: 12, borderRadius: 10, marginBottom: 12 },
  button: { backgroundColor: theme.colors.primary, padding: 12, borderRadius: 10, alignItems: "center" },
  buttonText: { color: "#fff", fontWeight: "700" },
  card: { backgroundColor: theme.colors.surface, marginTop: 16, padding: 16, borderRadius: 12 },
  code: { fontSize: 26, fontWeight: "800", color: theme.colors.primary },
  small: { color: theme.colors.muted },
  error: { color: theme.colors.danger, marginTop: 10 }
});
