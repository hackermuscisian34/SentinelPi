import React, { useState } from "react";
import { View, Text, TextInput, TouchableOpacity, StyleSheet } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { supabase } from "../api/supabase";
import { saveToken, saveUserEmail } from "../state/secureStore";
import { theme } from "../ui/theme";

export default function LoginScreen({ navigation }: any) {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");

    const onLogin = async () => {
        setError("");
        try {
            const { data, error } = await supabase.auth.signInWithPassword({
                email,
                password,
            });
            if (error) {
                setError(error.message || "Login failed. Check credentials.");
                return;
            }
            if (!data.session) {
                setError("Login failed. No session returned.");
                return;
            }
            if (data.user?.email) {
                await saveUserEmail(data.user.email);
            }
            await saveToken(data.session.access_token);
            navigation.replace("PiConfig");
        } catch (err: any) {
            setError(err?.message || "Login failed. Try again.");
            console.error("Login error:", err);
        }
    };

    return (
        <LinearGradient colors={[theme.colors.primaryLight, theme.colors.background]} style={styles.container}>
            <View style={styles.card}>
                <Text style={styles.title}>SentinelPi-EDR SOC</Text>
                <Text style={styles.subtitle}>Login</Text>
                <TextInput
                    placeholder="Email"
                    style={styles.input}
                    value={email}
                    onChangeText={setEmail}
                    autoCapitalize="none"
                    keyboardType="email-address"
                />
                <TextInput
                    placeholder="Password"
                    style={styles.input}
                    value={password}
                    onChangeText={setPassword}
                    secureTextEntry
                />
                {error ? <Text style={styles.error}>{error}</Text> : null}
                <TouchableOpacity style={styles.button} onPress={onLogin}>
                    <Text style={styles.buttonText}>Login</Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={() => navigation.navigate("Signup")}>
                    <Text style={styles.link}>Don't have an account? Sign up</Text>
                </TouchableOpacity>
            </View>
        </LinearGradient>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, justifyContent: "center", alignItems: "center" },
    card: { backgroundColor: theme.colors.surface, padding: 24, borderRadius: 16, width: "85%" },
    title: { fontSize: 22, fontWeight: "700", color: theme.colors.text, marginBottom: 4, textAlign: "center" },
    subtitle: { fontSize: 16, fontWeight: "600", color: theme.colors.muted, marginBottom: 16, textAlign: "center" },
    input: { backgroundColor: "#f0f7f1", padding: 12, borderRadius: 10, marginBottom: 10 },
    button: { backgroundColor: theme.colors.primary, padding: 12, borderRadius: 10, alignItems: "center", marginTop: 8 },
    buttonText: { color: "#fff", fontWeight: "700" },
    error: { color: theme.colors.danger, marginBottom: 8 },
    link: { color: theme.colors.primary, textAlign: "center", marginTop: 12, fontWeight: "600" }
});
