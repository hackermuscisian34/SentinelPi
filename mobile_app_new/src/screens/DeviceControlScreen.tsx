import React from "react";
import { View, Text, TouchableOpacity, StyleSheet, Alert } from "react-native";
import { theme } from "../ui/theme";
import { getToken, getPiIp } from "../state/secureStore";
import { createPiClient } from "../api/pi";
import { supabaseDelete } from "../api/supabaseRest";

export default function DeviceControlScreen({ route, navigation }: any) {
    const { device } = route.params;

    const send = async (command: string, args: any = {}) => {
        const token = await getToken();
        const piIp = await getPiIp();
        if (!token || !piIp) return;
        const client = createPiClient(piIp, token);
        await client.post("/command", { device_id: device.device_id, command, args });
    };

    const removeDevice = async () => {
        Alert.alert(
            "Remove Device",
            "Are you sure you want to remove this device? This cannot be undone.",
            [
                { text: "Cancel", style: "cancel" },
                {
                    text: "Remove",
                    style: "destructive",
                    onPress: async () => {
                        try {
                            const token = await getToken();
                            if (!token) return;
                            await supabaseDelete(`devices?device_id=eq.${device.device_id}`, token);
                            navigation.goBack();
                        } catch (e) {
                            Alert.alert("Error", "Failed to remove device.");
                        }
                    }
                }
            ]
        );
    };

    return (
        <View style={styles.container}>
            <Text style={styles.title}>{device.device_hostname}</Text>
            <TouchableOpacity style={styles.button} onPress={() => send("trigger_scan", { target: "full_pc" })}>
                <Text style={styles.buttonText}>Run Scan (Full PC)</Text>
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

            <View style={styles.divider} />

            <TouchableOpacity style={styles.buttonDanger} onPress={removeDevice}>
                <Text style={styles.buttonText}>Remove Device</Text>
            </TouchableOpacity>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, padding: 20, backgroundColor: theme.colors.background },
    title: { fontSize: 20, fontWeight: "700", marginBottom: 10, color: theme.colors.text },
    button: { backgroundColor: theme.colors.primary, padding: 12, borderRadius: 10, marginBottom: 10, alignItems: "center" },
    buttonDanger: { backgroundColor: theme.colors.danger, padding: 12, borderRadius: 10, marginBottom: 10, alignItems: "center" },
    buttonText: { color: "#fff", fontWeight: "700" },
    divider: { height: 20 }
});
