import React, { useState } from "react";
import { View, Text, TextInput, TouchableOpacity, StyleSheet } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { supabase } from "../api/supabase";
import { saveToken } from "../state/secureStore";
import { theme } from "../ui/theme";

export default function SignupScreen({ navigation }: any) {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [error, setError] = useState("");

    const onSignup = async () => {
        setError("");

        if (password !== confirmPassword) {
            setError("Passwords do not match.");
            return;
        }

        if (password.length < 6) {
            setError("Password must be at least 6 characters.");
            return;
        }

        try {
            const { data, error } = await supabase.auth.signUp({
                email,
                password,
            });

            if (error) {
                setError(error.message || "Signup failed.");
                return;
            }

            if (data.session) {
                // Email confirmation disabled — session returned immediately
                await saveToken(data.session.access_token);
                navigation.replace("PiConfig");
            } else {
                // Email confirmation required — guide user to check email then login
                setError("✅ Account created! Check your email to confirm, then log in.");
                setTimeout(() => navigation.replace("Login"), 4000);
            }
        } catch {
            setError("Signup failed. Try again.");
        }
    };

    return (
        <LinearGradient colors={[theme.colors.primaryLight, theme.colors.background]} style={styles.container}>
            <View style={styles.card}>
                <Text style={styles.title}>SentinelPi-EDR SOC</Text>
                <Text style={styles.subtitle}>Create Account</Text>
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
                <TextInput
                    placeholder="Confirm Password"
                    style={styles.input}
                    value={confirmPassword}
                    onChangeText={setConfirmPassword}
                    secureTextEntry
                />
                {error ? <Text style={styles.error}>{error}</Text> : null}
                <TouchableOpacity style={styles.button} onPress={onSignup}>
                    <Text style={styles.buttonText}>Sign Up</Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={() => navigation.navigate("Login")}>
                    <Text style={styles.link}>Already have an account? Login</Text>
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
