import React, { useState, useCallback, useEffect } from "react";
import { View, Text, StyleSheet, ScrollView, Dimensions, TouchableOpacity, Alert } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { LinearGradient } from "expo-linear-gradient";
import { ProgressChart } from "react-native-chart-kit";
import { Ionicons } from "@expo/vector-icons";
import { theme } from "../ui/theme";
import { getToken, getUserEmail, getPiIp } from "../state/secureStore";
import { supabaseGet } from "../api/supabaseRest";
import { supabase } from "../api/supabase"; // Assuming supabase client is exported from here

const screenWidth = Dimensions.get("window").width;

export default function DashboardScreen({ navigation }: any) {
    const [stats, setStats] = useState({
        devices: 0,
        alerts: 0,
        status: "Secure",
        cpu: 0,
        ram: 0,
        disk: 0
    });
    const [userEmail, setUserEmail] = useState("Admin");
    const [piIp, setPiIp] = useState("");
    const [chartData, setChartData] = useState({
        labels: ["CPU", "RAM"],
        data: [0, 0]
    });
    const [scanModalVisible, setScanModalVisible] = useState(false);

    // Scan Progress State
    const [isScanning, setIsScanning] = useState(false);
    const [elapsedTime, setElapsedTime] = useState(0);
    const [scanStatus, setScanStatus] = useState("Idle");
    const [customPaths, setCustomPaths] = useState<any[]>([]);
    const [networkModalVisible, setNetworkModalVisible] = useState(false);
    const [adapters, setAdapters] = useState<any[]>([]);
    const [networkLoading, setNetworkLoading] = useState(false);
    const [blockingAdapter, setBlockingAdapter] = useState<string | null>(null);
    const [wifiNetworks, setWifiNetworks] = useState<any[]>([]);

    // Use Ref to access current state in event listener without re-binding
    const isScanningRef = React.useRef(isScanning);
    const elapsedTimeRef = React.useRef(elapsedTime);

    // Helpers
    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
    };

    /** Call /command/sync and return the result. Throws on network/server error. */
    const sendSyncCommand = async (cmd: string, args: any = {}) => {
        const token = await getToken();
        if (!token) throw new Error("Not authenticated.");
        if (!piIp) throw new Error("Pi IP not found. Please reconnect.");
        const dList = await supabaseGet("devices?select=device_id&order=last_seen.desc&limit=1", token);
        if (!dList || dList.length === 0) throw new Error("No target device connected.");
        const deviceId = dList[0].device_id;
        const resp = await fetch(`http://${piIp}:8000/command/sync`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
            body: JSON.stringify({ device_id: deviceId, command: cmd, args })
        });
        if (!resp.ok) {
            const body = await resp.text().catch(() => "");
            throw new Error(`Command failed: ${resp.status} – ${body}`);
        }
        return resp.json();
    };

    const fetchNetworks = async () => {
        setNetworkLoading(true);
        setAdapters([]);
        setWifiNetworks([]);
        try {
            const [adapterResult, wifiResult] = await Promise.all([
                sendSyncCommand("list_networks"),
                sendSyncCommand("list_wifi"),
            ]);
            setAdapters(Array.isArray(adapterResult?.adapters) ? adapterResult.adapters : []);
            setWifiNetworks(Array.isArray(wifiResult?.networks) ? wifiResult.networks : []);
        } catch (e: any) {
            Alert.alert("Error", e?.message || "Failed to fetch network info.");
        } finally {
            setNetworkLoading(false);
        }
    };

    const startScan = (target: string, durationSeconds: number) => {
        // If target is a full path (contains backslash or Slash), pass it as 'path' 
        // Otherwise pass it as 'target' (quick options)
        const isFullPath = target.includes("\\") || target.includes("/");

        const payload = isFullPath ? { command: "trigger_scan", path: target } : { target };

        sendCommand("trigger_scan", payload);

        setScanModalVisible(false);
        setIsScanning(true);
        setElapsedTime(0);
        setScanStatus("Scanning...");
    };

    // Fetch Custom Paths for Modal
    useEffect(() => {
        if (scanModalVisible) {
            const fetchPaths = async () => {
                const token = await getToken();
                if (!token) return;
                const data = await supabaseGet("device_paths?select=*&order=label.asc", token);
                if (data) setCustomPaths(data);
            };
            fetchPaths();
            // Subscribe to updates for paths too?
            // Simple refresh is fine for now
        }
    }, [scanModalVisible]);

    useEffect(() => {
        isScanningRef.current = isScanning;
        elapsedTimeRef.current = elapsedTime;
    }, [isScanning, elapsedTime]);

    // Listen for Alerts to Stop Scan
    useFocusEffect(
        useCallback(() => {
            let channel: any;
            const initRealtime = async () => {
                const token = await getToken();
                if (!token) return;

                supabase.realtime.setAuth(token);
                channel = supabase
                    .channel("dashboard_alerts")
                    .on(
                        "postgres_changes",
                        { event: "INSERT", schema: "public", table: "alerts" },
                        (payload: any) => {
                            // Stop scanning if we are scanning
                            if (isScanningRef.current) {
                                setIsScanning(false);
                                setScanStatus("Completed");
                                Alert.alert("Scan Completed", "Scan finished. Check Alerts for details.");
                            }
                        }
                    )
                    .subscribe();
            };

            initRealtime();
            return () => {
                if (channel) supabase.removeChannel(channel);
            };
        }, [])
    );
    // Better approach: Use a ref for isScanning? Or just keep listener active always and check state inside.
    // But React state inside closure is tricky. simpler: just check specific alert relevant to scan?
    // For simplicity: If ANY alert comes in, assume scan finished (since scan produces alerts).

    useFocusEffect(
        useCallback(() => {
            let interval: any;
            if (isScanning) {
                interval = setInterval(() => {
                    setElapsedTime(prev => prev + 1);
                }, 1000);
            }
            return () => clearInterval(interval);
        }, [isScanning])
    );

    useFocusEffect(
        useCallback(() => {
            loadStats();
            const interval = setInterval(loadStats, 5000);
            return () => clearInterval(interval);
        }, [])
    );

    const loadStats = async () => {
        try {
            const token = await getToken();
            const email = await getUserEmail();
            const ip = await getPiIp();

            if (email) setUserEmail(email);
            if (ip) setPiIp(ip);
            if (!token) return;

            // 1. Get Single Targeted Device (Most recently active)
            const dList = await supabaseGet("devices?select=*&order=last_seen.desc&limit=1", token);
            const device = dList && dList.length > 0 ? dList[0] : null;

            // 2. Get Alerts Count
            const aList = await supabaseGet("alerts?select=id", token);
            setStats(prev => ({ ...prev, devices: device ? 1 : 0, alerts: aList?.length || 0 }));

            if (device) {
                // 3. Get Latest Telemetry for THIS device
                try {
                    const tele = await supabaseGet(
                        `telemetry_summaries?select=summary&device_id=eq.${device.device_id}&order=timestamp.desc&limit=1`,
                        token
                    );

                    if (tele && tele.length > 0) {
                        const summary = tele[0].summary;
                        if (summary) {
                            const cpu = (summary.cpu?.percent || 0) / 100;
                            const mem = (summary.memory?.percent || 0) / 100;
                            setChartData({
                                labels: ["CPU", "RAM"],
                                data: [cpu, mem]
                            });
                        }
                    }
                } catch {
                    // telemetry_summaries may not have data yet — silently ignore
                }
            } else {
                setChartData({ labels: ["CPU", "RAM"], data: [0, 0] });
            }
        } catch (e) {
            console.log(e);
        }
    };

    const chartConfig = {
        backgroundGradientFrom: "#101025",
        backgroundGradientTo: "#101025",
        backgroundGradientFromOpacity: 0.5,
        backgroundGradientToOpacity: 0.5,
        color: (opacity = 1) => `rgba(0, 255, 127, ${opacity})`, // Neon Green
        labelColor: (opacity = 1) => `rgba(255, 255, 255, ${opacity})`,
        strokeWidth: 2,
        barPercentage: 0.5,
        useShadowColorFromDataset: false,
        propsForLabels: {
            fontSize: 12,
            fontWeight: "bold"
        }
    };

    const sendCommand = async (cmd: string, args: any = {}) => {
        try {
            const token = await getToken();
            if (!token) return;

            if (!piIp) {
                alert("Pi IP not found. Please reconnect.");
                return;
            }

            // Get current device
            const dList = await supabaseGet("devices?select=device_id&order=last_seen.desc&limit=1", token);
            if (!dList || dList.length === 0) {
                alert("No target device connected.");
                return;
            }
            const deviceId = dList[0].device_id;

            if (cmd === "remove_device") {
                const resp = await fetch(`http://${piIp}:8000/devices/${deviceId}`, {
                    method: "DELETE",
                    headers: { "Authorization": `Bearer ${token}` }
                });
                if (resp.ok) {
                    alert("Device removed.");
                    loadStats(); // Refresh
                } else {
                    alert("Failed to remove device.");
                }
                return;
            }

            const resp = await fetch(`http://${piIp}:8000/command`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    device_id: deviceId,
                    command: cmd,
                    args: args
                })
            });

            if (resp.ok) {
                alert(`Command '${cmd}' sent successfully.`);
            } else {
                alert("Failed to send command.");
            }
        } catch (e) {
            console.error(e);
            alert("Error sending command.");
        }
    };

    const ActionButton = ({ icon, label, color, onPress }: any) => (
        <TouchableOpacity style={styles.actionBtn} onPress={onPress}>
            <LinearGradient colors={["#ffffff0d", "#ffffff05"]} style={styles.actionGradient}>
                <Ionicons name={icon} size={24} color={color} />
                <Text style={[styles.actionLabel, { color: color }]}>{label}</Text>
            </LinearGradient>
        </TouchableOpacity>
    );


    return (
        <>
            <LinearGradient colors={theme.gradients.main} style={styles.container}>
                <ScrollView contentContainerStyle={styles.scrollContent}>
                    <View style={styles.header}>
                        <View>
                            <Text style={styles.greeting}>Welcome Back,</Text>
                            <Text style={styles.username}>{userEmail}</Text>
                        </View>
                        <TouchableOpacity style={styles.profileButton}>
                            <Ionicons name="person-circle-outline" size={40} color={theme.colors.primary} />
                        </TouchableOpacity>
                    </View>

                    {/* System Health Section targeting the SINGLE device */}
                    <View style={styles.chartContainer}>
                        <LinearGradient colors={theme.gradients.glass} style={styles.glassCard}>
                            <View style={styles.chartHeader}>
                                <View>
                                    <Text style={styles.chartTitle}>Target PC Health</Text>
                                    <Text style={styles.chartSub}>{stats.devices > 0 ? "Connected" : "No Device Detected"}</Text>
                                </View>
                                <View style={[styles.liveIndicator, { backgroundColor: stats.devices > 0 ? "rgba(0, 255, 127, 0.1)" : "rgba(255, 51, 102, 0.1)" }]}>
                                    <View style={[styles.dot, { backgroundColor: stats.devices > 0 ? theme.colors.primary : theme.colors.danger }]} />
                                    <Text style={[styles.liveText, { color: stats.devices > 0 ? theme.colors.primary : theme.colors.danger }]}>
                                        {stats.devices > 0 ? "ONLINE" : "OFFLINE"}
                                    </Text>
                                </View>
                            </View>
                            <ProgressChart
                                data={chartData}
                                width={screenWidth - 64}
                                height={220}
                                strokeWidth={16}
                                radius={32}
                                chartConfig={chartConfig}
                                hideLegend={false}
                                style={{ borderRadius: 16 }}
                            />
                        </LinearGradient>
                    </View>

                    {/* Control Panel */}
                    <Text style={styles.sectionTitle}>Control Panel</Text>
                    <View style={styles.controlGrid}>
                        <ActionButton icon="scan-outline" label="Scan" color={theme.colors.primary} onPress={() => setScanModalVisible(true)} />
                        <ActionButton icon="medkit-outline" label="Quarantine" color={theme.colors.warning} onPress={() => sendCommand("quarantine")} />
                        <ActionButton icon="wifi-outline" label="Network" color={theme.colors.info} onPress={() => { setNetworkModalVisible(true); fetchNetworks(); }} />
                        <ActionButton icon="close-circle-outline" label="Block All" color={theme.colors.danger} onPress={() => sendCommand("isolate_network")} />
                    </View>

                    {stats.devices > 0 && (
                        <TouchableOpacity style={styles.removeBtn} onPress={() => sendCommand("remove_device")}>
                            <Text style={styles.removeText}>Remove Target Device</Text>
                        </TouchableOpacity>
                    )}

                    <View style={[styles.grid, { marginTop: 32 }]}>
                        <TouchableOpacity style={styles.cardWrapper} onPress={() => navigation.navigate("Devices")}>
                            <LinearGradient colors={theme.gradients.card} style={styles.card}>
                                <View style={styles.iconContainer}>
                                    <Ionicons name="desktop-outline" size={28} color={theme.colors.secondary} />
                                </View>
                                <Text style={styles.cardValue}>{stats.devices > 0 ? "1" : "0"}</Text>
                                <Text style={styles.cardLabel}>Target Details</Text>
                            </LinearGradient>
                        </TouchableOpacity>

                        <TouchableOpacity style={styles.cardWrapper} onPress={() => navigation.navigate("Alerts")}>
                            <LinearGradient colors={["#2a1015", "#101025"]} style={styles.card}>
                                <View style={[styles.iconContainer, { backgroundColor: "rgba(255, 51, 102, 0.2)" }]}>
                                    <Ionicons name="warning" size={28} color={theme.colors.danger} />
                                </View>
                                <Text style={[styles.cardValue, { color: theme.colors.danger }]}>{stats.alerts}</Text>
                                <Text style={styles.cardLabel}>Recent Alerts</Text>
                            </LinearGradient>
                        </TouchableOpacity>
                    </View>

                    {/* Circular Scan Progress */}
                    {isScanning && (
                        <View style={styles.progressContainer}>
                            <LinearGradient colors={theme.gradients.glass} style={styles.timerCard}>
                                <Text style={styles.timerTitle}>Scan in Progress...</Text>
                                <View style={{ position: 'relative', alignItems: 'center', justifyContent: 'center' }}>
                                    <ProgressChart
                                        data={{
                                            labels: ["Running"],
                                            data: [0.5]
                                        }}
                                        width={200}
                                        height={200}
                                        strokeWidth={16}
                                        radius={80}
                                        chartConfig={{
                                            backgroundGradientFrom: "#1e1e1e",
                                            backgroundGradientTo: "#1e1e1e",
                                            backgroundGradientFromOpacity: 0,
                                            backgroundGradientToOpacity: 0,
                                            color: (opacity = 1) => `rgba(0, 229, 255, ${opacity})`,
                                            strokeWidth: 2,
                                        }}
                                        hideLegend={true}
                                    />
                                    <View style={{ position: 'absolute', alignItems: 'center' }}>
                                        <Text style={styles.progressTime}>{formatTime(elapsedTime)}</Text>
                                        <Text style={styles.progressLabel}>Scanning</Text>
                                    </View>
                                </View>

                                <TouchableOpacity onPress={() => setIsScanning(false)} style={styles.dismissBtn}>
                                    <Text style={styles.dismissText}>Stop Timer</Text>
                                </TouchableOpacity>
                            </LinearGradient>
                        </View>
                    )}

                    <View style={styles.actionSection}>
                        {stats.devices === 0 && (
                            <TouchableOpacity onPress={() => navigation.navigate("Pairing")}>
                                <LinearGradient colors={theme.gradients.primary} style={styles.actionButton} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}>
                                    <Ionicons name="add-circle-outline" size={24} color="#000" style={{ marginRight: 8 }} />
                                    <Text style={styles.actionButtonText}>Connect Target PC</Text>
                                </LinearGradient>
                            </TouchableOpacity>
                        )}
                    </View>
                </ScrollView>

                {/* Scan Options Modal */}
                {scanModalVisible && (
                    <View style={[StyleSheet.absoluteFill, styles.modalOverlay]}>
                        <View style={styles.modalContainer}>
                            <LinearGradient colors={[theme.colors.surface, theme.colors.background]} style={styles.modalContent}>
                                <View style={styles.modalHeader}>
                                    <Text style={styles.modalHeaderTitle}>Select Scan Target</Text>
                                    <TouchableOpacity onPress={() => setScanModalVisible(false)} style={styles.closeButton}>
                                        <Ionicons name="close" size={24} color={theme.colors.text} />
                                    </TouchableOpacity>
                                </View>

                                <TouchableOpacity style={styles.optionButton} onPress={() => {
                                    startScan("user_profile", 300);
                                }}>
                                    <Ionicons name="person-circle-outline" size={32} color={theme.colors.primary} />
                                    <View style={{ marginLeft: 16 }}>
                                        <Text style={styles.optionTitle}>User Profile (Recommended)</Text>
                                        <Text style={styles.optionDesc}>Quickly scan likely infection vectors (~/Downloads, ~/Desktop)</Text>
                                        <Text style={styles.estTime}>~ 3-5 mins</Text>
                                    </View>
                                </TouchableOpacity>

                                <TouchableOpacity style={styles.optionButton} onPress={() => {
                                    startScan("full_pc", 1800);
                                }}>
                                    <Ionicons name="laptop-outline" size={32} color={theme.colors.secondary} />
                                    <View style={{ marginLeft: 16 }}>
                                        <Text style={styles.optionTitle}>Full PC Scan</Text>
                                        <Text style={styles.optionDesc}>Deep scan of all drives. Can take a long time.</Text>
                                        <Text style={styles.estTime}>~ 30-60+ mins</Text>
                                    </View>
                                </TouchableOpacity>

                                <TouchableOpacity style={styles.optionButton} onPress={() => {
                                    startScan("downloads", 60);
                                }}>
                                    <Ionicons name="download-outline" size={32} color={theme.colors.info} />
                                    <View style={{ marginLeft: 16 }}>
                                        <Text style={styles.optionTitle}>Downloads Only</Text>
                                        <Text style={styles.optionDesc}>Check only the Downloads folder.</Text>
                                        <Text style={styles.estTime}>~ 1 min</Text>
                                    </View>
                                </TouchableOpacity>

                                <View style={{ marginTop: 20, marginBottom: 10, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <Text style={styles.sectionTitle}>Detected System Paths</Text>
                                    <TouchableOpacity onPress={() => sendCommand("discover_paths", {})}>
                                        <Ionicons name="refresh-circle" size={24} color={theme.colors.primary} />
                                    </TouchableOpacity>
                                </View>

                                {/* Dynamic System Paths */}
                                {customPaths.map((path, index) => (
                                    <TouchableOpacity key={index} style={styles.pathButton} onPress={() => {
                                        startScan(path.path, 300);
                                        Alert.alert("Scanning Custom Path", `Scanning ${path.label || path.path}. Time may vary.`);
                                    }}>
                                        <Ionicons name="folder-open-outline" size={24} color={theme.colors.textSecondary} />
                                        <View style={{ marginLeft: 12, flex: 1 }}>
                                            <Text style={styles.pathTitle} numberOfLines={1}>{path.label || path.path}</Text>
                                            <Text style={styles.pathSub} numberOfLines={1}>{path.path}</Text>
                                        </View>
                                        <Ionicons name="scan-circle-outline" size={24} color={theme.colors.primary} />
                                    </TouchableOpacity>
                                ))}

                                {customPaths.length === 0 && (
                                    <Text style={{ color: theme.colors.textSecondary, textAlign: 'center', marginVertical: 10 }}>
                                        Tap refresh to discover scan targets...
                                    </Text>
                                )}

                            </LinearGradient>
                        </View>
                    </View>
                )}
            </LinearGradient>

            {/* Network Manager Modal */}
            {networkModalVisible && (
                <View style={[StyleSheet.absoluteFill, styles.modalOverlay]}>
                    <View style={styles.modalContainer}>
                        <LinearGradient colors={[theme.colors.surface, theme.colors.background]} style={styles.modalContent}>
                            <View style={styles.modalHeader}>
                                <Text style={styles.modalHeaderTitle}>🌐 Network Manager</Text>
                                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                                    <TouchableOpacity onPress={fetchNetworks}>
                                        <Ionicons name="refresh" size={22} color={theme.colors.primary} />
                                    </TouchableOpacity>
                                    <TouchableOpacity onPress={() => setNetworkModalVisible(false)} style={styles.closeButton}>
                                        <Ionicons name="close" size={24} color={theme.colors.text} />
                                    </TouchableOpacity>
                                </View>
                            </View>

                            {networkLoading && (
                                <Text style={{ color: theme.colors.primary, textAlign: 'center', marginVertical: 20 }}>
                                    Fetching network info...
                                </Text>
                            )}

                            {/* ── Adapters section ─────────────────────── */}
                            <Text style={[styles.sectionTitle, { marginBottom: 10 }]}>🔌 Network Adapters</Text>
                            <Text style={{ color: theme.colors.textSecondary, marginBottom: 12, fontSize: 13 }}>
                                Block or unblock individual adapters on the target PC.
                            </Text>

                            {!networkLoading && adapters.length === 0 && (
                                <Text style={{ color: theme.colors.textSecondary, textAlign: 'center', marginVertical: 8 }}>
                                    No adapters found. Tap refresh.
                                </Text>
                            )}

                            {adapters.map((adapter, idx) => {
                                const isUp = adapter.status === 'Up';
                                const isBlocking = blockingAdapter === adapter.name;
                                return (
                                    <View key={idx} style={styles.adapterRow}>
                                        <View style={{ flex: 1 }}>
                                            <Text style={styles.adapterName} numberOfLines={1}>{adapter.name}</Text>
                                            <Text style={styles.adapterDesc} numberOfLines={1}>{adapter.description}</Text>
                                        </View>
                                        <View style={[styles.statusChip, { backgroundColor: isUp ? 'rgba(0,255,127,0.15)' : 'rgba(255,51,102,0.15)' }]}>
                                            <View style={[styles.statusDot, { backgroundColor: isUp ? theme.colors.primary : theme.colors.danger }]} />
                                            <Text style={[styles.statusText, { color: isUp ? theme.colors.primary : theme.colors.danger }]}>
                                                {adapter.status}
                                            </Text>
                                        </View>
                                        <TouchableOpacity
                                            disabled={isBlocking}
                                            style={[styles.adapterBtn, { backgroundColor: isUp ? 'rgba(255,51,102,0.2)' : 'rgba(0,255,127,0.2)' }]}
                                            onPress={async () => {
                                                setBlockingAdapter(adapter.name);
                                                try {
                                                    const action = isUp ? "block_network" : "unblock_network";
                                                    const res = await sendSyncCommand(action, { name: adapter.name });
                                                    if (res?.status === "ok") {
                                                        setAdapters(prev => prev.map(a =>
                                                            a.name === adapter.name ? { ...a, status: isUp ? 'Disabled' : 'Up' } : a
                                                        ));
                                                        await fetchNetworks();
                                                    } else {
                                                        Alert.alert("Failed", res?.message || "Could not change adapter state.");
                                                    }
                                                } catch (e: any) {
                                                    Alert.alert("Error", e?.message || "Command failed.");
                                                } finally {
                                                    setBlockingAdapter(null);
                                                }
                                            }}
                                        >
                                            <Text style={{ color: isUp ? theme.colors.danger : theme.colors.primary, fontWeight: 'bold', fontSize: 12 }}>
                                                {isBlocking ? '...' : isUp ? 'Block' : 'Unblock'}
                                            </Text>
                                        </TouchableOpacity>
                                    </View>
                                );
                            })}

                            {/* ── WiFi SSIDs section ───────────────────── */}
                            <Text style={[styles.sectionTitle, { marginTop: 20, marginBottom: 10 }]}>📶 Visible WiFi Networks</Text>

                            {!networkLoading && wifiNetworks.length === 0 && (
                                <Text style={{ color: theme.colors.textSecondary, textAlign: 'center', marginVertical: 8 }}>
                                    No WiFi networks found. Tap refresh.
                                </Text>
                            )}

                            {wifiNetworks.map((net, idx) => {
                                const sig = parseInt(net.signal) || 0;
                                const sigIcon = sig >= 75 ? "wifi" : sig >= 40 ? "wifi-outline" : "wifi-outline";
                                const isSecure = net.auth && net.auth !== "Open";
                                return (
                                    <View key={idx} style={[styles.adapterRow, { paddingVertical: 10 }]}>
                                        <Ionicons name={sigIcon as any} size={20} color={theme.colors.primary} style={{ marginRight: 10 }} />
                                        <View style={{ flex: 1 }}>
                                            <Text style={styles.adapterName} numberOfLines={1}>{net.ssid || '(Hidden Network)'}</Text>
                                            <Text style={styles.adapterDesc}>{net.auth || 'Unknown'} · {net.signal}</Text>
                                        </View>
                                        <Ionicons
                                            name={isSecure ? "lock-closed" : "lock-open-outline"}
                                            size={16}
                                            color={isSecure ? theme.colors.textSecondary : theme.colors.danger}
                                        />
                                    </View>
                                );
                            })}

                        </LinearGradient>
                    </View>
                </View>
            )}
        </>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1 },
    scrollContent: { padding: 24, paddingTop: 60 },
    header: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 32 },
    greeting: { fontSize: 16, color: theme.colors.textSecondary, marginBottom: 4 },
    username: { fontSize: 28, fontWeight: "bold", color: theme.colors.text, textShadowColor: "rgba(0, 255, 127, 0.3)", textShadowOffset: { width: 0, height: 0 }, textShadowRadius: 10 },
    profileButton: { padding: 4 },
    chartContainer: { marginBottom: 32 },
    glassCard: { borderRadius: 24, padding: 20, borderWidth: 1, borderColor: "rgba(255,255,255,0.05)" },
    chartHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 16 },
    chartTitle: { fontSize: 18, fontWeight: "600", color: theme.colors.text },
    chartSub: { fontSize: 12, color: theme.colors.textSecondary },
    liveIndicator: { flexDirection: "row", alignItems: "center", paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12 },
    dot: { width: 6, height: 6, borderRadius: 3, marginRight: 6 },
    liveText: { fontSize: 10, fontWeight: "bold" },
    sectionTitle: { fontSize: 18, fontWeight: "bold", color: theme.colors.text, marginBottom: 16 },
    controlGrid: { flexDirection: "row", flexWrap: "wrap", justifyContent: "space-between" },
    actionBtn: { width: "31%", marginBottom: 16, borderRadius: 12, overflow: "hidden" },
    actionGradient: { padding: 16, alignItems: "center", justifyContent: "center", height: 100 },
    actionLabel: { marginTop: 8, fontSize: 12, fontWeight: "600", textAlign: "center" },
    removeBtn: { backgroundColor: "rgba(255, 51, 102, 0.1)", padding: 16, borderRadius: 12, alignItems: "center", marginBottom: 24, borderWidth: 1, borderColor: theme.colors.danger },
    removeText: { color: theme.colors.danger, fontWeight: "bold" },
    grid: { flexDirection: "row", justifyContent: "space-between", marginBottom: 32 },
    cardWrapper: { width: "48%", borderRadius: 20, overflow: "hidden" },
    card: { padding: 20, alignItems: "flex-start", borderRadius: 20, height: 160, borderWidth: 1, borderColor: "rgba(255,255,255,0.05)" },
    iconContainer: { width: 48, height: 48, borderRadius: 14, backgroundColor: "rgba(0, 229, 255, 0.1)", justifyContent: "center", alignItems: "center", marginBottom: 16 },
    cardValue: { fontSize: 32, fontWeight: "bold", color: theme.colors.text, marginBottom: 4 },
    cardLabel: { fontSize: 13, color: theme.colors.textSecondary },
    actionSection: { marginBottom: 40 },
    actionButton: { flexDirection: "row", padding: 18, borderRadius: 16, alignItems: "center", justifyContent: "center", shadowColor: theme.colors.primary, shadowOpacity: 0.3, shadowRadius: 10, elevation: 5 },
    actionButtonText: { color: "#000", fontWeight: "bold", fontSize: 16 },

    // Modal Styles
    modalOverlay: { backgroundColor: "rgba(0,0,0,0.8)", justifyContent: "center", padding: 20 },
    modalContainer: { width: "100%", borderRadius: 20, overflow: "hidden" },
    modalContent: { padding: 24 },
    modalHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 24 },
    modalHeaderTitle: { fontSize: 20, fontWeight: "bold", color: theme.colors.text },
    closeButton: { padding: 4 },
    optionButton: { flexDirection: "row", alignItems: "center", backgroundColor: "rgba(255,255,255,0.05)", padding: 16, borderRadius: 12, marginBottom: 12, borderWidth: 1, borderColor: "rgba(255,255,255,0.1)" },
    optionTitle: { fontSize: 16, fontWeight: "bold", color: theme.colors.text },
    optionDesc: { fontSize: 12, color: theme.colors.textSecondary, marginTop: 2 },
    estTime: { fontSize: 11, color: theme.colors.primary, fontWeight: 'bold', marginTop: 4, opacity: 0.8 },

    // Progress Styles
    progressContainer: { marginTop: 24, marginBottom: 24, alignItems: 'center', justifyContent: 'center', width: '100%' },
    timerCard: { padding: 24, borderRadius: 24, borderWidth: 1, borderColor: "rgba(0, 229, 255, 0.2)", alignItems: 'center', width: '100%' },
    timerTitle: { fontSize: 18, fontWeight: "bold", color: theme.colors.text, marginBottom: 16, textTransform: "uppercase", letterSpacing: 1 },
    progressTime: { fontSize: 32, fontWeight: 'bold', color: theme.colors.text, textShadowColor: "rgba(0, 229, 255, 0.5)", textShadowRadius: 10 },
    progressLabel: { fontSize: 12, color: theme.colors.textSecondary, marginTop: 4, textTransform: "uppercase" },
    dismissBtn: { marginTop: 24, paddingVertical: 12, paddingHorizontal: 32, backgroundColor: "rgba(255,255,255,0.1)", borderRadius: 12 },
    dismissText: { color: theme.colors.text, fontWeight: "bold" },

    // Path List
    pathButton: { flexDirection: 'row', alignItems: 'center', padding: 12, backgroundColor: "rgba(0,0,0,0.2)", borderRadius: 8, marginBottom: 8, borderWidth: 1, borderColor: "rgba(255,255,255,0.05)" },
    pathTitle: { color: theme.colors.text, fontWeight: 'bold', fontSize: 14 },
    pathSub: { color: theme.colors.textSecondary, fontSize: 11 },

    // Network Adapter styles
    adapterRow: { flexDirection: 'row', alignItems: 'center', backgroundColor: "rgba(255,255,255,0.04)", padding: 12, borderRadius: 10, marginBottom: 10, borderWidth: 1, borderColor: "rgba(255,255,255,0.07)" },
    adapterName: { color: theme.colors.text, fontWeight: '700', fontSize: 14 },
    adapterDesc: { color: theme.colors.textSecondary, fontSize: 11, marginTop: 2 },
    statusChip: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 10, marginLeft: 8 },
    statusDot: { width: 6, height: 6, borderRadius: 3, marginRight: 4 },
    statusText: { fontSize: 10, fontWeight: 'bold' },
    adapterBtn: { marginLeft: 8, paddingVertical: 6, paddingHorizontal: 12, borderRadius: 8 },
});

