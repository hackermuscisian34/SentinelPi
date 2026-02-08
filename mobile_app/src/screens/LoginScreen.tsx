import React, { useState } from "react";
import { View, Text, TextInput, TouchableOpacity, StyleSheet } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { supabase } from "../api/supabase";
import { saveToken, savePiIp } from "../state/secureStore";
import { theme } from "../ui/theme";

export default function LoginScreen({ navigation }: any) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [piIp, setPiIp] = useState("");
  const [error, setError] = useState("");

  const onLogin = async () => {
    setError("");
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (error || !data.session) {
        setError("Login failed. Check credentials.");
        return;
      }
      await saveToken(data.session.access_token);
      await savePiIp(piIp.trim());
      navigation.replace("Dashboard");
    } catch {
      setError("Login failed. Try again.");
    }
  };

  return (
    <LinearGradient colors={[theme.colors.primaryLight, theme.colors.background]} style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.title}>SentinelPi-EDR SOC</Text>
        <TextInput placeholder="Supabase email" style={styles.input} value={email} onChangeText={setEmail} />
        <TextInput placeholder="Password" style={styles.input} value={password} onChangeText={setPassword} secureTextEntry />
        <TextInput placeholder="Raspberry Pi IP" style={styles.input} value={piIp} onChangeText={setPiIp} />
        {error ? <Text style={styles.error}>{error}</Text> : null}
        <TouchableOpacity style={styles.button} onPress={onLogin}>
          <Text style={styles.buttonText}>Login</Text>
        </TouchableOpacity>
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", alignItems: "center" },
  card: { backgroundColor: theme.colors.surface, padding: 24, borderRadius: 16, width: "85%" },
  title: { fontSize: 20, fontWeight: "700", color: theme.colors.text, marginBottom: 12 },
  input: { backgroundColor: "#f0f7f1", padding: 12, borderRadius: 10, marginBottom: 10 },
  button: { backgroundColor: theme.colors.primary, padding: 12, borderRadius: 10, alignItems: "center" },
  buttonText: { color: "#fff", fontWeight: "700" },
  error: { color: theme.colors.danger, marginBottom: 8 }
});
