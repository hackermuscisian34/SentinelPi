import React, { useEffect, useRef } from "react";
import { View, Text, StyleSheet, Animated } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { theme } from "../ui/theme";

export default function SplashScreen({ onFinish }: { onFinish: () => void }) {
    const fadeAnim = useRef(new Animated.Value(0)).current;
    const scaleAnim = useRef(new Animated.Value(0.3)).current;

    useEffect(() => {
        // Animate in
        Animated.parallel([
            Animated.timing(fadeAnim, {
                toValue: 1,
                duration: 800,
                useNativeDriver: true,
            }),
            Animated.spring(scaleAnim, {
                toValue: 1,
                tension: 50,
                friction: 7,
                useNativeDriver: true,
            }),
        ]).start();

        // Auto-dismiss after 2.5 seconds
        const timer = setTimeout(() => {
            Animated.timing(fadeAnim, {
                toValue: 0,
                duration: 500,
                useNativeDriver: true,
            }).start(() => {
                onFinish();
            });
        }, 2500);

        return () => clearTimeout(timer);
    }, []);

    return (
        <LinearGradient
            colors={[theme.colors.primaryLight, theme.colors.background]}
            style={styles.container}
        >
            <Animated.View
                style={[
                    styles.content,
                    {
                        opacity: fadeAnim,
                        transform: [{ scale: scaleAnim }],
                    },
                ]}
            >
                {/* Shield Icon */}
                <View style={styles.shieldContainer}>
                    <View style={styles.shield}>
                        <Text style={styles.shieldIcon}>🛡️</Text>
                    </View>
                </View>

                {/* App Name */}
                <Text style={styles.appName}>SentinelPi</Text>
                <Text style={styles.edr}>EDR</Text>

                {/* Tagline */}
                <Text style={styles.tagline}>Endpoint Detection & Response</Text>
            </Animated.View>

            {/* Bottom branding */}
            <Animated.View style={[styles.footer, { opacity: fadeAnim }]}>
                <Text style={styles.footerText}>Powered by Raspberry Pi</Text>
            </Animated.View>
        </LinearGradient>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: "center",
        alignItems: "center",
    },
    content: {
        alignItems: "center",
    },
    shieldContainer: {
        marginBottom: 24,
    },
    shield: {
        width: 120,
        height: 120,
        borderRadius: 60,
        backgroundColor: theme.colors.primary,
        justifyContent: "center",
        alignItems: "center",
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 8,
        elevation: 8,
    },
    shieldIcon: {
        fontSize: 60,
    },
    appName: {
        fontSize: 42,
        fontWeight: "800",
        color: theme.colors.text,
        marginBottom: 4,
        letterSpacing: -1,
    },
    edr: {
        fontSize: 24,
        fontWeight: "600",
        color: theme.colors.muted,
        letterSpacing: 4,
        marginBottom: 32,
    },
    tagline: {
        fontSize: 14,
        color: theme.colors.muted,
        fontWeight: "500",
        letterSpacing: 0.5,
    },
    footer: {
        position: "absolute",
        bottom: 40,
    },
    footerText: {
        fontSize: 12,
        color: theme.colors.muted,
        fontWeight: "500",
    },
});
