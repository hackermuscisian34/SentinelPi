import React, { useState } from "react";
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Ionicons } from "@expo/vector-icons";
import { savePiIp } from "../state/secureStore";
import { theme } from "../ui/theme";

export default function PiConfigScreen({ navigation }: any) {
    const [piIp, setPiIp] = useState("");
    const [hostname, setHostname] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const onContinue = async () => {
        setError("");
        setLoading(true);

        if (!piIp.trim()) {
            setError("Please enter Raspberry Pi IP address.");
            setLoading(false);
            return;
        }

        if (!hostname.trim()) {
            setError("Please enter a hostname for identification.");
            setLoading(false);
            return;
        }

        try {
            // Verify connection and hostname
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s timeout

            const resp = await fetch(`http://${piIp.trim()}:8000/health`, {
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (!resp.ok) {
                setError("Could not connect to Pi Server.");
                setLoading(false);
                return;
            }

            const data = await resp.json();

            // STRICT VERIFICATION: Server MUST return a hostname
            if (!data.hostname) {
                setError("Pi Server did not report a hostname. Please update the Pi Server.");
                setLoading(false);
                return;
            }

            if (data.hostname.toLowerCase() !== hostname.trim().toLowerCase()) {
                setError(`Hostname mismatch. Pi reports: ${data.hostname}`);
                setLoading(false);
                return;
            }

            // Store both IP and hostname (we can extend secureStore if needed)
            await savePiIp(piIp.trim());

            setLoading(false);
            navigation.replace("Main");
        } catch (err) {
            console.error(err);
            setError("Connection failed. Check IP and network.");
            setLoading(false);
        }
    };

    return (
        <LinearGradient colors={theme.gradients.main} style={styles.container}>
            <LinearGradient colors={theme.gradients.glass} style={styles.card}>
                <View style={styles.iconHeader}>
                    <Ionicons name="server-outline" size={48} color={theme.colors.primary} />
                </View>
                <Text style={styles.title}>Connect Server</Text>
                <Text style={styles.subtitle}>Link your SentinelPi device</Text>

                <View style={styles.inputGroup}>
                    <Text style={styles.label}>Raspberry Pi IP Address</Text>
                    <View style={styles.inputContainer}>
                        <Ionicons name="wifi-outline" size={20} color={theme.colors.muted} style={styles.inputIcon} />
                        <TextInput
                            placeholder="e.g., 192.168.1.100"
                            placeholderTextColor={theme.colors.muted}
                            style={styles.input}
                            value={piIp}
                            onChangeText={setPiIp}
                            autoCapitalize="none"
                            keyboardType="decimal-pad"
                        />
                    </View>
                </View>

                <View style={styles.inputGroup}>
                    <Text style={styles.label}>Hostname</Text>
                    <View style={styles.inputContainer}>
                        <Ionicons name="id-card-outline" size={20} color={theme.colors.muted} style={styles.inputIcon} />
                        <TextInput
                            placeholder="e.g., apt.local"
                            placeholderTextColor={theme.colors.muted}
                            style={styles.input}
                            value={hostname}
                            onChangeText={setHostname}
                            autoCapitalize="none"
                        />
                    </View>
                </View>

                {error ? (
                    <View style={styles.errorContainer}>
                        <Ionicons name="alert-circle" size={16} color={theme.colors.danger} />
                        <Text style={styles.error}>{error}</Text>
                    </View>
                ) : null}

                <TouchableOpacity style={styles.buttonWrapper} onPress={onContinue} disabled={loading}>
                    <LinearGradient colors={theme.gradients.primary} style={styles.button} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}>
                        {loading ? (
                            <ActivityIndicator color="#000" />
                        ) : (
                            <Text style={styles.buttonText}>Connect & Continue</Text>
                        )}
                    </LinearGradient>
                </TouchableOpacity>

                <Text style={styles.hint}>
                    Run 'hostname -I' on your Pi to find the IP address.
                </Text>
            </LinearGradient>
        </LinearGradient>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, justifyContent: "center", alignItems: "center", padding: 20 },
    card: { width: "100%", maxWidth: 400, padding: 32, borderRadius: 24, borderWidth: 1, borderColor: "rgba(255,255,255,0.05)", alignItems: "center" },
    iconHeader: { width: 80, height: 80, borderRadius: 40, backgroundColor: "rgba(0, 255, 127, 0.1)", justifyContent: "center", alignItems: "center", marginBottom: 24 },
    title: { fontSize: 24, fontWeight: "bold", color: theme.colors.text, marginBottom: 8 },
    subtitle: { fontSize: 14, color: theme.colors.textSecondary, marginBottom: 32 },
    inputGroup: { width: "100%", marginBottom: 20 },
    label: { fontSize: 12, fontWeight: "600", color: theme.colors.textSecondary, marginBottom: 8, marginLeft: 4 },
    inputContainer: { flexDirection: "row", alignItems: "center", backgroundColor: "rgba(0,0,0,0.3)", borderRadius: 12, borderWidth: 1, borderColor: "rgba(255,255,255,0.1)" },
    inputIcon: { marginLeft: 16 },
    input: { flex: 1, padding: 16, color: theme.colors.text, fontSize: 16 },
    errorContainer: { flexDirection: "row", alignItems: "center", marginBottom: 16, backgroundColor: "rgba(255, 51, 102, 0.1)", padding: 12, borderRadius: 8, width: "100%" },
    error: { color: theme.colors.danger, marginLeft: 8, fontSize: 13, flex: 1 },
    buttonWrapper: { width: "100%", marginTop: 8, borderRadius: 16, overflow: "hidden", elevation: 4 },
    button: { padding: 18, alignItems: "center", justifyContent: "center" },
    buttonText: { color: "#000", fontWeight: "bold", fontSize: 16 },
    hint: { fontSize: 12, color: theme.colors.muted, marginTop: 24, textAlign: "center", fontStyle: "italic" }
});
