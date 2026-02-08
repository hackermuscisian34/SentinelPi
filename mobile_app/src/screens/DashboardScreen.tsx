import React from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import { theme } from "../ui/theme";

export default function DashboardScreen({ navigation }: any) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Security Dashboard</Text>
      <TouchableOpacity style={styles.card} onPress={() => navigation.navigate("Pairing")}> 
        <Text style={styles.cardTitle}>Generate Pairing Code</Text>
      </TouchableOpacity>
      <TouchableOpacity style={styles.card} onPress={() => navigation.navigate("Devices")}> 
        <Text style={styles.cardTitle}>Devices</Text>
      </TouchableOpacity>
      <TouchableOpacity style={styles.card} onPress={() => navigation.navigate("Alerts")}> 
        <Text style={styles.cardTitle}>Alerts</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.background, padding: 20 },
  title: { fontSize: 22, fontWeight: "700", color: theme.colors.text, marginBottom: 12 },
  card: { backgroundColor: theme.colors.surface, padding: 18, borderRadius: 12, marginBottom: 12 },
  cardTitle: { fontWeight: "600", color: theme.colors.text }
});
