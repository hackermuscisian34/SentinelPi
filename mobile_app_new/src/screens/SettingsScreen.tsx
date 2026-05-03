
import React from "react";
import { View, Text, TouchableOpacity, StyleSheet, Alert } from "react-native";
import { theme } from "../ui/theme";
import { clearAll } from "../state/secureStore";

export default function SettingsScreen({ navigation }: any) {

    const handleLogout = async () => {
        Alert.alert("Logout", "Are you sure requesting to logout?", [
            { text: "Cancel", style: "cancel" },
            {
                text: "Logout",
                style: "destructive",
                onPress: async () => {
                    await clearAll();
                    navigation.replace("Login");
                }
            }
        ]);
    };

    return (
        <View style={styles.container}>
            <Text style={styles.header}>Settings</Text>

            <View style={styles.section}>
                <Text style={styles.sectionTitle}>Account</Text>
                <TouchableOpacity style={styles.row}>
                    <Text style={styles.rowText}>Profile</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.row}>
                    <Text style={styles.rowText}>Notifications</Text>
                </TouchableOpacity>
            </View>

            <View style={styles.section}>
                <Text style={styles.sectionTitle}>App Info</Text>
                <View style={styles.row}>
                    <Text style={styles.rowText}>Version</Text>
                    <Text style={styles.rowValue}>1.0.0</Text>
                </View>
            </View>

            <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
                <Text style={styles.logoutText}>Logout</Text>
            </TouchableOpacity>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, padding: 20, backgroundColor: theme.colors.background, paddingTop: 60 },
    header: { fontSize: 32, fontWeight: "bold", color: theme.colors.text, marginBottom: 30 },
    section: { marginBottom: 30 },
    sectionTitle: { fontSize: 14, color: theme.colors.textSecondary, marginBottom: 10, textTransform: "uppercase", letterSpacing: 1 },
    row: {
        flexDirection: "row",
        justifyContent: "space-between",
        alignItems: "center",
        backgroundColor: theme.colors.surface,
        padding: 16,
        borderRadius: 12,
        marginBottom: 8
    },
    rowText: { color: theme.colors.text, fontSize: 16 },
    rowValue: { color: theme.colors.textSecondary, fontSize: 16 },
    logoutButton: {
        backgroundColor: "rgba(176, 0, 32, 0.2)",
        padding: 16,
        borderRadius: 12,
        alignItems: "center",
        borderWidth: 1,
        borderColor: theme.colors.danger,
        marginTop: 20
    },
    logoutText: { color: theme.colors.danger, fontWeight: "bold", fontSize: 16 }
});
