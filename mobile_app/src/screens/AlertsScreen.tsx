import React, { useEffect, useState } from "react";
import { View, Text, StyleSheet } from "react-native";
import { theme } from "../ui/theme";
import { getToken } from "../state/secureStore";
import { supabase } from "../api/supabase";
import { supabaseGet } from "../api/supabaseRest";

export default function AlertsScreen() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let channel: any;
    const init = async () => {
      try {
        const token = await getToken();
        if (!token) throw new Error("Missing token");
        const data = await supabaseGet("alerts?select=*&order=timestamp.desc&limit=50", token);
        setAlerts(data);

        supabase.realtime.setAuth(token);
        channel = supabase
          .channel("alerts")
          .on(
            "postgres_changes",
            { event: "INSERT", schema: "public", table: "alerts" },
            (payload: any) => {
              setAlerts((prev) => [payload.new, ...prev].slice(0, 50));
            }
          )
          .subscribe();
      } catch {
        setError("Failed to load alerts.");
      }
    };
    init();
    return () => {
      if (channel) supabase.removeChannel(channel);
    };
  }, []);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Alerts</Text>
      {alerts.map((a) => (
        <View key={a.id} style={styles.card}>
          <Text style={styles.cardTitle}>{a.title}</Text>
          <Text style={styles.cardSub}>{a.severity}</Text>
          <Text style={styles.cardSub}>{a.description}</Text>
        </View>
      ))}
      {error ? <Text style={styles.error}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: theme.colors.background },
  title: { fontSize: 20, fontWeight: "700", marginBottom: 10, color: theme.colors.text },
  card: { backgroundColor: theme.colors.surface, padding: 14, borderRadius: 10, marginBottom: 8 },
  cardTitle: { fontWeight: "700", color: theme.colors.text },
  cardSub: { color: theme.colors.muted },
  error: { color: theme.colors.danger, marginTop: 10 }
});
