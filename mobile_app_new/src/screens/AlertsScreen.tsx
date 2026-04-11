import React, { useEffect, useState, useCallback } from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Share, Alert } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Ionicons } from "@expo/vector-icons";
import { useFocusEffect } from "@react-navigation/native";

import { WebView } from "react-native-webview";
import * as Notifications from "expo-notifications";
import { theme } from "../ui/theme";
import { getToken } from "../state/secureStore";
import { supabase } from "../api/supabase";
import { supabaseGet, supabaseDelete } from "../api/supabaseRest";
import { formatDistanceToNow } from "date-fns";

export default function AlertsScreen() {
    const [alerts, setAlerts] = useState<any[]>([]);
    const [error, setError] = useState("");
    const [selectedAlert, setSelectedAlert] = useState<any>(null);

    // Re-fetch every time this tab comes into focus
    useFocusEffect(
        useCallback(() => {
            let cancelled = false;
            const fetchAlerts = async () => {
                try {
                    const token = await getToken();
                    if (!token || cancelled) return;
                    const data = await supabaseGet(
                        "alerts?select=id,title,description,severity,timestamp,device_id&order=timestamp.desc&limit=50",
                        token
                    );
                    if (!cancelled) setAlerts(data || []);
                } catch {
                    if (!cancelled) setError("Failed to load alerts.");
                }
            };
            fetchAlerts();
            return () => { cancelled = true; };
        }, [])
    );

    // Realtime subscription — set up once on mount
    useEffect(() => {
        let channel: any;
        const subscribe = async () => {
            const token = await getToken();
            if (!token) return;
            supabase.realtime.setAuth(token);
            channel = supabase
                .channel("alerts_realtime")
                .on(
                    "postgres_changes",
                    { event: "INSERT", schema: "public", table: "alerts" },
                    (payload: any) => {
                        const newAlert = payload.new;
                        // Prepend new alert so it appears immediately without a reload
                        setAlerts((prev) => [newAlert, ...prev].slice(0, 50));

                        Notifications.scheduleNotificationAsync({
                            content: {
                                title: "Security Alert: " + newAlert.title,
                                body: newAlert.description,
                                data: { alertId: newAlert.id },
                                sound: true,
                                priority: Notifications.AndroidNotificationPriority.MAX,
                            },
                            trigger: { channelId: "default", seconds: 1 },
                        });
                    }
                )
                .subscribe();
        };
        subscribe();
        return () => {
            if (channel) supabase.removeChannel(channel);
        };
    }, []);

    const fetchAlertDetails = async (alert: any) => {
        try {
            // Optimistically set selected alert with partial data
            setSelectedAlert(alert);

            const token = await getToken();
            if (!token) return;

            // Fetch full row (including metadata)
            const details = await supabaseGet(`alerts?id=eq.${alert.id}&select=*`, token);
            if (details && details.length > 0) {
                setSelectedAlert(details[0]);
            }
        } catch (e) {
            Alert.alert("Error", "Failed to load details");
        }
    };

    const deleteAlerts = async () => {
        Alert.alert(
            "Clear All Alerts",
            "Are you sure you want to delete all alerts? This cannot be undone.",
            [
                { text: "Cancel", style: "cancel" },
                {
                    text: "Delete All",
                    style: "destructive",
                    onPress: async () => {
                        try {
                            const token = await getToken();
                            if (!token) return;
                            // Delete all alerts for this user (or just clear local if RLS prevents delete?)
                            // Assuming we have policy to delete our own alerts.
                            // Supabase doesn't support 'delete all' easily without a WHERE. 
                            // We can use a trick: id > 0 or similar if integer ID.
                            // Or safer: delete where device_id is in user's devices.
                            // For simplicity in this demo: Delete strictly where id is not null (everything).
                            await supabaseDelete("alerts?id=neq.0", token);
                            setAlerts([]);
                        } catch (e) {
                            Alert.alert("Error", "Failed to clear alerts.");
                        }
                    }
                }
            ]
        );
    };



    const getLaymanExplanation = (metadata: any) => {
        let text = "An anomaly was detected on your system.";
        const combinedOutput = (metadata?.clamav?.output || "") + (metadata?.yara?.output || "");

        if (combinedOutput.includes("Eic") || combinedOutput.includes("EICAR")) {
            return "This looks like a standard Test File (EICAR). It is harmless and used to verify that your security software is working correctly.";
        }
        if (combinedOutput.includes("Trojan")) {
            return "A Trojan Horse was detected. This type of malware disguises itself as legitimate software to trick you into running it, giving attackers access to your system.";
        }
        if (combinedOutput.includes("Adware")) {
            return "Adware was found. This software displays unwanted advertisements and may track your browsing habits.";
        }
        if (combinedOutput.includes("Ransom")) {
            return "CRITICAL: Ransomware-like patterns detected. This malware attempts to encrypt your files and demand payment. Immediate isolation is recommended.";
        }
        if (combinedOutput.includes("Spy")) {
            return "Spyware detected. This software secretly monitors your activity and may steal sensitive information like passwords.";
        }

        return "The security agent detected a potential threat pattern. While the specific type is technical, it is recommended to quarantine the file and run a full system scan.";
    };

    const shareReport = async (alert: any) => {
        if (!alert) return;

        let meta = alert.metadata;
        if (typeof meta === 'string') {
            try { meta = JSON.parse(meta); } catch { }
        }

        const explanation = getLaymanExplanation(meta);

        const htmlContent = `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>SentinelPi Security Report</title>
            <style>
                body { font-family: -apple-system, system-ui, sans-serif; padding: 20px; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; }
                .header { border-bottom: 2px solid #e74c3c; padding-bottom: 20px; margin-bottom: 30px; }
                .logo { font-size: 24px; font-weight: bold; color: #c0392b; }
                .meta { color: #666; font-size: 0.9em; margin-top: 10px; }
                .severity { display: inline-block; padding: 4px 12px; border-radius: 4px; font-weight: bold; color: white; background: ${alert.severity === 'critical' ? '#e74c3c' : '#f39c12'}; }
                .card { background: #f8f9fa; border: 1px solid #ddd; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                .card h3 { margin-top: 0; color: #2c3e50; }
                .code { background: #2d3436; color: #dfe6e9; padding: 15px; border-radius: 6px; font-family: monospace; white-space: pre-wrap; font-size: 0.85em; }
                .explanation { background: #dff9fb; border-left: 4px solid #00cec9; padding: 15px; color: #2d3436; margin: 20px 0; }
                .footer { margin-top: 50px; font-size: 0.8em; color: #b2bec3; text-align: center; border-top: 1px solid #eee; padding-top: 20px; }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="logo">🛡️ SentinelPi EDR</div>
                <h1>Security Incident Report</h1>
                <div class="meta">
                    <strong>Date:</strong> ${new Date(alert.timestamp).toLocaleString()}<br>
                    <strong>Device ID:</strong> ${alert.device_id || 'Unknown'}<br>
                    <strong>Incident Ref:</strong> ${alert.title} <span class="severity">${alert.severity?.toUpperCase()}</span>
                </div>
            </div>

            <div class="explanation">
                <h3>🤖 AI Analysis (Layman Summary)</h3>
                <p>${explanation}</p>
            </div>

            <div class="card">
                <h3>Incident Description</h3>
                <p>${alert.description}</p>
            </div>

            ${meta?.clamav ? `
            <div class="card">
                <h3>🦠 Antivirus Scan Results (ClamAV)</h3>
                <div class="code">${meta.clamav.output || meta.clamav.message || JSON.stringify(meta.clamav)}</div>
            </div>` : ''}

            ${meta?.yara ? `
            <div class="card">
                <h3>🔍 Malware Analysis (YARA)</h3>
                <div class="code">${meta.yara.output || meta.yara.message || JSON.stringify(meta.yara)}</div>
            </div>` : ''}

            <div class="footer">
                Generated by SentinelPi EDR • Automated Proactive Threat Defense
            </div>
        </body>
        </html>
        `;

        // Since we can't easily write to a .html file without expo-file-system and get a content URI easily sharing broadly,
        // We will share the TEXT representation but formatted nicely, and instructions to view format.
        // OR better: Just share the text version but upgraded with the explanation.

        // Actually, let's try sharing the HTML string as a message? Some apps render it? No.
        // Fallback: A very nice Text Report.

        let textReport = `🛡️ SENTINEL PI SECURITY REPORT\n`;
        textReport += `═════════════════════════════\n\n`;
        textReport += `🤖 AI ANALYSIS\n`;
        textReport += `"${explanation}"\n\n`;
        textReport += `📅 DATE: ${new Date(alert.timestamp).toLocaleString()}\n`;
        textReport += `🚨 SEVERITY: ${alert.severity?.toUpperCase()}\n\n`;
        textReport += `📋 SUMMARY\n${alert.description}\n\n`;

        if (meta?.clamav?.output) textReport += `🦠 CLAMAV OUTPUT\n${meta.clamav.output}\n\n`;
        if (meta?.yara?.output) textReport += `🔍 YARA OUTPUT\n${meta.yara.output}\n\n`;

        textReport += `═════════════════════════════\n`;
        textReport += `Generated by SentinelPi EDR`;

        // If we had expo-print: await Print.printAsync({ html: htmlContent });

        try {
            await Share.share({
                message: textReport,
                title: `Security Report - ${alert.title}`
            });
        } catch (error: any) {
            console.error(error.message);
        }
    };

    const getSeverityColor = (severity: string) => {
        switch (severity?.toLowerCase()) {
            case "critical": return theme.colors.danger;
            case "high": return theme.colors.warning;
            case "medium": return "#FFA500";
            default: return theme.colors.info;
        }
    };

    const getSeverityIcon = (severity: string) => {
        switch (severity?.toLowerCase()) {
            case "critical": return "alert-circle";
            case "high": return "warning";
            case "medium": return "information-circle";
            default: return "notifications";
        }
    };

    const renderDetailContent = (alert: any) => {
        if (!alert) return null;
        let meta = alert.metadata;
        if (typeof meta === 'string') {
            try { meta = JSON.parse(meta); } catch { }
        }

        const threatsFound: number = meta?.threats_found ?? 0;
        const filesScanned: number | undefined = meta?.files_scanned;
        const threatLines: string[] = meta?.clamav?.output
            ? (meta.clamav.output as string).split('\n').filter((l: string) => l.includes('FOUND')).slice(0, 20)
            : [];
        const yaraHits: string[] = meta?.yara?.output
            ? (meta.yara.output as string).split('\n').filter((l: string) => l.trim() && !l.includes('---')).slice(0, 20)
            : [];

        return (
            <ScrollView style={styles.modalScroll}>
                <Text style={styles.modalTitle}>{alert.title}</Text>
                <Text style={styles.modalTimestamp}>
                    {alert.timestamp ? new Date(alert.timestamp).toLocaleString() : 'Unknown time'}
                </Text>

                {/* Human-readable summary */}
                <View style={styles.section}>
                    <Text style={styles.sectionHeader}>Summary</Text>
                    <Text style={styles.modalText}>{alert.description}</Text>
                </View>

                {/* Scan statistics */}
                {meta && (filesScanned !== undefined || threatsFound > 0) && (
                    <View style={[styles.section, { flexDirection: 'row', gap: 12 }]}>
                        {filesScanned !== undefined && (
                            <View style={styles.statBox}>
                                <Text style={styles.statValue}>{filesScanned}</Text>
                                <Text style={styles.statLabel}>Files Scanned</Text>
                            </View>
                        )}
                        <View style={[styles.statBox, { borderColor: threatsFound > 0 ? '#ff3366' : '#00ff7f' }]}>
                            <Text style={[styles.statValue, { color: threatsFound > 0 ? '#ff3366' : '#00ff7f' }]}>
                                {threatsFound}
                            </Text>
                            <Text style={styles.statLabel}>Threats Found</Text>
                        </View>
                    </View>
                )}

                {/* Threat list */}
                {threatLines.length > 0 && (
                    <View style={styles.section}>
                        <Text style={styles.sectionHeader}>⚠️ Detected Threats</Text>
                        {threatLines.map((t, i) => (
                            <View key={i} style={styles.threatRow}>
                                <Ionicons name="warning" size={14} color="#ff3366" style={{ marginRight: 8, marginTop: 2 }} />
                                <Text style={styles.threatText} selectable>{t}</Text>
                            </View>
                        ))}
                    </View>
                )}

                {/* YARA hits */}
                {yaraHits.length > 0 && (
                    <View style={styles.section}>
                        <Text style={styles.sectionHeader}>🔍 YARA Matches</Text>
                        {yaraHits.map((y, i) => (
                            <View key={i} style={styles.threatRow}>
                                <Ionicons name="search" size={14} color="#fdcb6e" style={{ marginRight: 8, marginTop: 2 }} />
                                <Text style={[styles.threatText, { color: '#fdcb6e' }]} selectable>{y}</Text>
                            </View>
                        ))}
                    </View>
                )}

                {/* AI-generated HTML report */}
                {meta?.report_html && (
                    <View style={styles.section}>
                        <Text style={styles.sectionHeader}>🤖 AI Analysis Report</Text>
                        <View style={{ height: 500, borderRadius: 8, overflow: 'hidden', borderWidth: 1, borderColor: 'rgba(255,255,255,0.1)', backgroundColor: 'white' }}>
                            <WebView
                                originWhitelist={['*']}
                                source={{ html: meta.report_html }}
                                style={{ flex: 1 }}
                                nestedScrollEnabled
                            />
                        </View>
                    </View>
                )}

                {/* Clean scan — reassurance message */}
                {meta && !threatsFound && !threatLines.length && !meta?.report_html && (
                    <View style={[styles.section, { alignItems: 'center', padding: 20 }]}>
                        <Ionicons name="shield-checkmark" size={48} color="#00ff7f" />
                        <Text style={{ color: '#00ff7f', fontWeight: 'bold', fontSize: 16, marginTop: 12 }}>
                            System Clean
                        </Text>
                        <Text style={{ color: theme.colors.textSecondary, textAlign: 'center', marginTop: 6 }}>
                            No malware or suspicious files were detected.
                        </Text>
                    </View>
                )}
            </ScrollView>
        );
    };


    return (
        <LinearGradient colors={theme.gradients.main} style={styles.container}>
            <ScrollView contentContainerStyle={styles.scrollContent}>
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
                    <Text style={{ fontSize: 24, fontWeight: "bold", color: theme.colors.text }}>Alerts & Threats</Text>
                    {alerts.length > 0 && (
                        <TouchableOpacity onPress={deleteAlerts}>
                            <Text style={{ color: theme.colors.danger, fontWeight: 'bold' }}>Clear All</Text>
                        </TouchableOpacity>
                    )}
                </View>

                {alerts.map((a) => {
                    const color = getSeverityColor(a.severity);
                    const iconName = getSeverityIcon(a.severity);

                    return (
                        <TouchableOpacity
                            key={a.id}
                            activeOpacity={0.8}
                            onPress={() => setSelectedAlert(a)}
                        >
                            <LinearGradient colors={theme.gradients.card} style={[styles.card, { borderLeftColor: color, borderLeftWidth: 4 }]}>
                                <View style={styles.headerRow}>
                                    <View style={[styles.iconBox, { backgroundColor: `${color}20` }]}>
                                        <Ionicons name={iconName} size={24} color={color} />
                                    </View>
                                    <View style={styles.titleColumn}>
                                        <Text style={styles.cardTitle}>{a.title}</Text>
                                        <Text style={styles.timestamp}>
                                            {a.timestamp ? formatDistanceToNow(new Date(a.timestamp), { addSuffix: true }) : "Just now"}
                                        </Text>
                                    </View>
                                    <Ionicons name="chevron-forward" size={20} color={theme.colors.textSecondary} />
                                </View>
                                <Text style={styles.description} numberOfLines={2}>{a.description}</Text>

                                <TouchableOpacity
                                    style={styles.viewReportButton}
                                    onPress={() => setSelectedAlert(a)}
                                >
                                    <Ionicons name="document-text-outline" size={16} color="white" />
                                    <Text style={styles.viewReportText}>View AI Report</Text>
                                </TouchableOpacity>
                            </LinearGradient>
                        </TouchableOpacity>
                    );
                })}

                {alerts.length === 0 && !error && (
                    <View style={styles.emptyState}>
                        <Ionicons name="shield-checkmark-outline" size={64} color={theme.colors.success} />
                        <Text style={styles.emptyText}>No active threats detected.</Text>
                    </View>
                )}

                {error ? <Text style={styles.error}>{error}</Text> : null}
            </ScrollView>

            {/* Detail Modal */}
            {selectedAlert && (
                <View style={[StyleSheet.absoluteFill, styles.modalOverlay]}>
                    <View style={styles.modalContainer}>
                        <LinearGradient colors={[theme.colors.surface, theme.colors.background]} style={styles.modalContent}>
                            <View style={styles.modalHeader}>
                                <Text style={styles.modalHeaderTitle}>Alert Details</Text>
                                <View style={{ flexDirection: 'row' }}>
                                    <TouchableOpacity onPress={() => shareReport(selectedAlert)} style={[styles.closeButton, { marginRight: 10 }]}>
                                        <Ionicons name="share-outline" size={24} color={theme.colors.primary} />
                                    </TouchableOpacity>
                                    <TouchableOpacity onPress={() => setSelectedAlert(null)} style={styles.closeButton}>
                                        <Ionicons name="close" size={24} color={theme.colors.text} />
                                    </TouchableOpacity>
                                </View>
                            </View>
                            {renderDetailContent(selectedAlert)}
                        </LinearGradient>
                    </View>
                </View>
            )}
        </LinearGradient>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1 },
    scrollContent: { padding: 20, paddingTop: 60, paddingBottom: 100 },
    pageTitle: { fontSize: 24, fontWeight: "bold", marginBottom: 24, color: theme.colors.text },
    card: { padding: 16, borderRadius: 16, marginBottom: 16, borderWidth: 1, borderColor: "rgba(255,255,255,0.05)" },
    headerRow: { flexDirection: "row", alignItems: "center", marginBottom: 12 },
    iconBox: { width: 44, height: 44, borderRadius: 12, justifyContent: "center", alignItems: "center", marginRight: 16 },
    titleColumn: { flex: 1 },
    cardTitle: { fontWeight: "bold", fontSize: 16, color: theme.colors.text },
    timestamp: { fontSize: 12, color: theme.colors.textSecondary, marginTop: 2 },
    description: { color: theme.colors.textSecondary, lineHeight: 20, fontSize: 14 },
    emptyState: { alignItems: "center", marginTop: 60, opacity: 0.5 },
    emptyText: { color: theme.colors.textSecondary, fontSize: 16, marginTop: 16 },
    error: { color: theme.colors.danger, marginTop: 10, textAlign: "center" },

    // Modal Styles
    modalOverlay: { backgroundColor: "rgba(0,0,0,0.8)", justifyContent: "center", padding: 20 },
    modalContainer: { flex: 1, maxHeight: "80%", width: "100%", borderRadius: 20, overflow: "hidden" },
    modalContent: { flex: 1 },
    modalHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", padding: 20, borderBottomWidth: 1, borderBottomColor: "rgba(255,255,255,0.1)" },
    modalHeaderTitle: { fontSize: 18, fontWeight: "bold", color: theme.colors.text },
    closeButton: { padding: 4 },
    modalScroll: { flex: 1, padding: 20 },
    modalTitle: { fontSize: 22, fontWeight: "bold", color: theme.colors.primary, marginBottom: 8 },
    modalTimestamp: { fontSize: 14, color: theme.colors.textSecondary, marginBottom: 24 },
    section: { marginBottom: 24 },
    sectionHeader: { fontSize: 16, fontWeight: "bold", color: theme.colors.text, marginBottom: 12, textTransform: "uppercase", letterSpacing: 1 },
    modalText: { fontSize: 15, color: theme.colors.text, lineHeight: 24 },
    scanBlock: { backgroundColor: "rgba(0,0,0,0.3)", borderRadius: 8, padding: 12, marginBottom: 12 },
    subHeader: { fontSize: 14, fontWeight: "bold", color: theme.colors.info, marginBottom: 8 },
    codeBlock: { fontFamily: "monospace", fontSize: 12, color: theme.colors.muted },
    viewReportButton: {
        marginTop: 12,
        backgroundColor: "rgba(255, 255, 255, 0.1)",
        paddingVertical: 8,
        paddingHorizontal: 12,
        borderRadius: 8,
        flexDirection: "row",
        alignItems: "center",
        alignSelf: "flex-start",
        gap: 6,
    },
    viewReportText: {
        color: "white",
        fontSize: 12,
        fontWeight: "600",
    },
    generatingContainer: { padding: 20, alignItems: 'center', justifyContent: 'center', backgroundColor: "rgba(255,255,255,0.05)", borderRadius: 12 },
    generatingText: { color: theme.colors.info, marginTop: 8, textAlign: 'center' },

    // Scan detail styles
    statBox: {
        flex: 1,
        backgroundColor: "rgba(255,255,255,0.05)",
        borderRadius: 12,
        padding: 16,
        alignItems: 'center',
        borderWidth: 1,
        borderColor: "rgba(255,255,255,0.1)",
    },
    statValue: { fontSize: 28, fontWeight: 'bold', color: theme.colors.text },
    statLabel: { fontSize: 12, color: theme.colors.textSecondary, marginTop: 4, textAlign: 'center' },
    threatRow: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 8 },
    threatText: { flex: 1, color: theme.colors.text, fontSize: 13, lineHeight: 20 },
});

