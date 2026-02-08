import React, { useEffect, useState } from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { theme } from "../ui/theme";
import { getToken } from "../state/secureStore";
import { supabaseGet } from "../api/supabaseRest";

export default function DevicesScreen({ navigation }: any) {
  const [devices, setDevices] = useState<any[]>([]);
  const [error, setError] = useState("");

  const load = async () => {
    setError("");
    try {
      const token = await getToken();
      if (!token) throw new Error("Missing token");
      const data = await supabaseGet("devices?select=*&order=created_at.desc", token);
      setDevices(data);
    } catch {
      setError("Failed to load devices.");
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Devices</Text>
      {devices.map((d) => (
        <TouchableOpacity key={d.device_id} style={styles.card} onPress={() => navigation.navigate("DeviceControl", { device: d })}>
          <Text style={styles.cardTitle}>{d.device_hostname}</Text>
          <Text style={styles.cardSub}>{d.status || "unknown"}</Text>
        </TouchableOpacity>
      ))}
      {error ? <Text style={styles.error}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: theme.colors.background },
  title: { fontSize: 20, fontWeight: "700", marginBottom: 10, color: theme.colors.text },
  card: { backgroundColor: theme.colors.surface, padding: 16, borderRadius: 12, marginBottom: 10 },
  cardTitle: { fontWeight: "700", color: theme.colors.text },
  cardSub: { color: theme.colors.muted },
  error: { color: theme.colors.danger, marginTop: 10 }
});
