import React from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { theme } from "../ui/theme";
import { getToken, getPiIp } from "../state/secureStore";
import { createPiClient } from "../api/pi";

export default function DeviceControlScreen({ route }: any) {
  const { device } = route.params;

  const send = async (command: string, args: any = {}) => {
    const token = await getToken();
    const piIp = await getPiIp();
    if (!token || !piIp) return;
    const client = createPiClient(piIp, token);
    await client.post("/command", { device_id: device.device_id, command, args });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>{device.device_hostname}</Text>
      <TouchableOpacity style={styles.button} onPress={() => send("trigger_scan")}> 
        <Text style={styles.buttonText}>Run Scan</Text>
      </TouchableOpacity>
      <TouchableOpacity style={styles.button} onPress={() => send("kill_process", { pid: 1234 })}> 
        <Text style={styles.buttonText}>Kill Process</Text>
      </TouchableOpacity>
      <TouchableOpacity style={styles.button} onPress={() => send("isolate_network")}> 
        <Text style={styles.buttonText}>Isolate Network</Text>
      </TouchableOpacity>
      <TouchableOpacity style={styles.button} onPress={() => send("restore_network")}> 
        <Text style={styles.buttonText}>Restore Network</Text>
      </TouchableOpacity>
      <TouchableOpacity style={styles.buttonDanger} onPress={() => send("shutdown")}> 
        <Text style={styles.buttonText}>Shutdown</Text>
      </TouchableOpacity>
      <TouchableOpacity style={styles.buttonDanger} onPress={() => send("restart")}> 
        <Text style={styles.buttonText}>Restart</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: theme.colors.background },
  title: { fontSize: 20, fontWeight: "700", marginBottom: 10, color: theme.colors.text },
  button: { backgroundColor: theme.colors.primary, padding: 12, borderRadius: 10, marginBottom: 10, alignItems: "center" },
  buttonDanger: { backgroundColor: theme.colors.danger, padding: 12, borderRadius: 10, marginBottom: 10, alignItems: "center" },
  buttonText: { color: "#fff", fontWeight: "700" }
});
