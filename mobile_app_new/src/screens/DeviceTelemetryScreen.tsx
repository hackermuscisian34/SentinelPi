
import React, { useState, useEffect } from "react";
import { View, Text, StyleSheet, Dimensions, ScrollView } from "react-native";
import { LineChart } from "react-native-chart-kit";
import { theme } from "../ui/theme";
import { getToken } from "../state/secureStore";
import { supabaseGet } from "../api/supabaseRest";

const screenWidth = Dimensions.get("window").width;

export default function DeviceTelemetryScreen({ route }: any) {
    const { device } = route.params;
    const [cpuData, setCpuData] = useState<number[]>([0]);
    const [memData, setMemData] = useState<number[]>([0]);
    const [timestamps, setTimestamps] = useState<string[]>(["Now"]);

    useEffect(() => {
        loadTelemetry();
        const interval = setInterval(loadTelemetry, 10000); // Poll every 10s
        return () => clearInterval(interval);
    }, []);

    const loadTelemetry = async () => {
        try {
            const token = await getToken();
            if (!token) return;

            // Fetch last 10 telemetry records
            const data = await supabaseGet(
                `telemetry_summaries?select=summary,timestamp&device_id=eq.${device.device_id}&order=timestamp.desc&limit=10`,
                token
            );

            if (data && data.length > 0) {
                // Reverse to show oldest to newest
                const records = data.reverse();

                const cpu = records.map((r: any) => r.summary?.cpu?.percent || 0);
                const mem = records.map((r: any) => r.summary?.memory?.percent || 0);
                const times = records.map((r: any) => {
                    const d = new Date(r.timestamp);
                    return `${d.getHours()}:${d.getMinutes().toString().padStart(2, '0')}`;
                });

                setCpuData(cpu);
                setMemData(mem);
                setTimestamps(times);
            }
        } catch (e) {
            console.error("Failed to load telemetry", e);
        }
    };

    const chartConfig = {
        backgroundGradientFrom: theme.colors.surface,
        backgroundGradientTo: theme.colors.surface,
        decimalPlaces: 0,
        color: (opacity = 1) => `rgba(0, 255, 127, ${opacity})`, // Neon Green
        labelColor: (opacity = 1) => `rgba(230, 237, 243, ${opacity})`, // Text Color
        style: {
            borderRadius: 16
        },
        propsForDots: {
            r: "4",
            strokeWidth: "2",
            stroke: theme.colors.primary
        }
    };

    return (
        <ScrollView style={styles.container}>
            <Text style={styles.header}>Real-time Performance</Text>
            <Text style={styles.subHeader}>{device.device_hostname}</Text>

            <View style={styles.chartContainer}>
                <Text style={styles.chartTitle}>CPU Usage (%)</Text>
                <LineChart
                    data={{
                        labels: timestamps,
                        datasets: [{ data: cpuData }]
                    }}
                    width={screenWidth - 40}
                    height={220}
                    chartConfig={chartConfig}
                    bezier
                    style={styles.chart}
                />
            </View>

            <View style={styles.chartContainer}>
                <Text style={styles.chartTitle}>Memory Usage (%)</Text>
                <LineChart
                    data={{
                        labels: timestamps,
                        datasets: [{ data: memData }]
                    }}
                    width={screenWidth - 40}
                    height={220}
                    chartConfig={{
                        ...chartConfig,
                        color: (opacity = 1) => `rgba(255, 85, 85, ${opacity})`, // Red for RAM
                    }}
                    bezier
                    style={styles.chart}
                />
            </View>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, padding: 20, backgroundColor: theme.colors.background },
    header: { fontSize: 22, fontWeight: "bold", color: theme.colors.text, marginBottom: 5 },
    subHeader: { fontSize: 16, color: theme.colors.textSecondary, marginBottom: 20 },
    chartContainer: {
        marginBottom: 30,
        backgroundColor: theme.colors.surface,
        borderRadius: 16,
        padding: 10,
        elevation: 3
    },
    chartTitle: {
        color: theme.colors.text,
        fontSize: 16,
        fontWeight: "600",
        marginBottom: 10,
        marginLeft: 10
    },
    chart: {
        marginVertical: 8,
        borderRadius: 16
    }
});
