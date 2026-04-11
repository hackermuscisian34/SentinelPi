import React, { useState, useCallback } from "react";
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { LinearGradient } from "expo-linear-gradient";
import { Ionicons } from "@expo/vector-icons";
import { theme } from "../ui/theme";
import { getToken } from "../state/secureStore";
import { supabaseGet } from "../api/supabaseRest";
import { formatDistanceToNow } from "date-fns";

export default function DevicesScreen({ navigation }: any) {
    const [device, setDevice] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const load = async () => {
        setLoading(true);
        setError("");
        try {
            const token = await getToken();
            if (!token) throw new Error("Missing token");
            // Get single most recent device
            const data = await supabaseGet("devices?select=*&order=last_seen.desc&limit=1", token);
            if (data && data.length > 0) {
                setDevice(data[0]);
            } else {
                setDevice(null);
            }
        } catch {
            setError("Failed to load device info.");
        } finally {
            setLoading(false);
        }
    };

    useFocusEffect(
        useCallback(() => {
            load();
        }, [])
    );

    const DetailRow = ({ icon, label, value, color }: any) => (
        <View style={styles.detailRow}>
            <View style={[styles.iconBox, { backgroundColor: color ? `${color}20` : "rgba(255,255,255,0.05)" }]}>
                <Ionicons name={icon} size={20} color={color || theme.colors.textSecondary} />
            </View>
            <View style={styles.detailText}>
                <Text style={styles.detailLabel}>{label}</Text>
                <Text style={styles.detailValue}>{value || "N/A"}</Text>
            </View>
        </View>
    );

    return (
        <LinearGradient colors={theme.gradients.main} style={styles.container}>
            <ScrollView contentContainerStyle={styles.scrollContent}>
                <Text style={styles.pageTitle}>Target Device</Text>

                {loading ? (
                    <ActivityIndicator size="large" color={theme.colors.primary} style={{ marginTop: 40 }} />
                ) : error ? (
                    <Text style={styles.error}>{error}</Text>
                ) : device ? (
                    <>
                        <LinearGradient colors={theme.gradients.glass} style={styles.mainCard}>
                            <View style={styles.header}>
                                <View style={styles.headerIcon}>
                                    <Ionicons name="desktop" size={40} color={theme.colors.secondary} />
                                </View>
                                <View>
                                    <Text style={styles.hostname}>{device.device_hostname}</Text>
                                    <View style={[styles.statusBadge, { backgroundColor: device.status === "online" ? "rgba(0, 255, 127, 0.2)" : "rgba(255, 51, 102, 0.2)" }]}>
                                        <View style={[styles.dot, { backgroundColor: device.status === "online" ? theme.colors.success : theme.colors.danger }]} />
                                        <Text style={[styles.statusText, { color: device.status === "online" ? theme.colors.success : theme.colors.danger }]}>
                                            {device.status?.toUpperCase() || "UNKNOWN"}
                                        </Text>
                                    </View>
                                </View>
                            </View>

                            <View style={styles.divider} />

                            <DetailRow icon="finger-print" label="Device ID" value={device.device_id} />
                            <DetailRow icon="wifi" label="IP Address" value={device.ip_address} color={theme.colors.info} />
                            <DetailRow icon="git-network" label="MAC Address" value={device.mac_address} />
                            <DetailRow icon="server-outline" label="Agent Version" value={device.agent_version} color={theme.colors.warning} />
                            <DetailRow
                                icon="time-outline"
                                label="Last Seen"
                                value={device.last_seen ? formatDistanceToNow(new Date(device.last_seen), { addSuffix: true }) : "Never"}
                            />
                        </LinearGradient>
                    </>
                ) : (
                    <View style={styles.emptyState}>
                        <Ionicons name="desktop-outline" size={64} color={theme.colors.muted} />
                        <Text style={styles.emptyText}>No device connected.</Text>
                        <Text style={styles.emptySub}>Go to Dashboard to enroll a device.</Text>
                    </View>
                )}
            </ScrollView>
        </LinearGradient>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1 },
    scrollContent: { padding: 20, paddingTop: 60 },
    pageTitle: { fontSize: 24, fontWeight: "bold", marginBottom: 24, color: theme.colors.text },
    mainCard: { borderRadius: 24, padding: 24, borderWidth: 1, borderColor: "rgba(255,255,255,0.05)" },
    header: { flexDirection: "row", alignItems: "center", marginBottom: 24 },
    headerIcon: { width: 64, height: 64, borderRadius: 20, backgroundColor: "rgba(0, 229, 255, 0.1)", justifyContent: "center", alignItems: "center", marginRight: 16 },
    hostname: { fontSize: 22, fontWeight: "bold", color: theme.colors.text, marginBottom: 8 },
    statusBadge: { flexDirection: "row", alignItems: "center", alignSelf: "flex-start", paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
    dot: { width: 6, height: 6, borderRadius: 3, marginRight: 6 },
    statusText: { fontSize: 11, fontWeight: "bold" },
    divider: { height: 1, backgroundColor: "rgba(255,255,255,0.05)", marginBottom: 24 },
    detailRow: { flexDirection: "row", alignItems: "center", marginBottom: 20 },
    iconBox: { width: 40, height: 40, borderRadius: 12, justifyContent: "center", alignItems: "center", marginRight: 16 },
    detailText: { flex: 1 },
    detailLabel: { fontSize: 12, color: theme.colors.textSecondary, marginBottom: 2 },
    detailValue: { fontSize: 15, color: theme.colors.text, fontWeight: "500" },
    error: { color: theme.colors.danger, textAlign: "center", marginTop: 20 },
    emptyState: { alignItems: "center", marginTop: 60 },
    emptyText: { color: theme.colors.text, fontSize: 18, fontWeight: "bold", marginTop: 16 },
    emptySub: { color: theme.colors.textSecondary, marginTop: 8 }
});
