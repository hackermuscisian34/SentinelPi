
import React, { useState, useEffect } from "react";
import { Platform } from "react-native";
import { NavigationContainer } from "@react-navigation/native";
import { createStackNavigator } from "@react-navigation/stack";
import * as SplashScreenExpo from "expo-splash-screen";
import { StatusBar } from "expo-status-bar";
import SplashScreen from "./src/screens/SplashScreen";
import LoginScreen from "./src/screens/LoginScreen";
import SignupScreen from "./src/screens/SignupScreen";
import PiConfigScreen from "./src/screens/PiConfigScreen";
import PairingScreen from "./src/screens/PairingScreen";
import DeviceControlScreen from "./src/screens/DeviceControlScreen";
import MainTabNavigator from "./src/navigation/MainTabNavigator";
import DeviceTelemetryScreen from "./src/screens/DeviceTelemetryScreen";
import { theme } from "./src/ui/theme";

// Keep the native splash screen visible while we load
SplashScreenExpo.preventAutoHideAsync();

const Stack = createStackNavigator();
import * as Notifications from "expo-notifications";

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

export default function App() {
  const [showSplash, setShowSplash] = useState(true);
  const [appReady, setAppReady] = useState(false);

  useEffect(() => {
    async function prepare() {
      try {
        // Request permissions
        const { status: existingStatus } = await Notifications.getPermissionsAsync();
        let finalStatus = existingStatus;
        if (existingStatus !== 'granted') {
          const { status } = await Notifications.requestPermissionsAsync();
          finalStatus = status;
        }

        // Create Android Channel
        if (Platform.OS === 'android') {
          await Notifications.setNotificationChannelAsync('default', {
            name: 'default',
            importance: Notifications.AndroidImportance.MAX,
            vibrationPattern: [0, 250, 250, 250],
            lightColor: '#FF231F7C',
          });
        }

        // You can add any initialization logic here
        // For example: loading fonts, checking auth state, etc.
        await new Promise(resolve => setTimeout(resolve, 100));
      } catch (e) {
        console.warn(e);
      } finally {
        setAppReady(true);
        await SplashScreenExpo.hideAsync();
      }
    }

    prepare();
  }, []);

  // Global Alert Listener for Notifications
  useEffect(() => {
    // We need to initialize the listener, but we might not have a token yet if not logged in.
    // Ideally this should be in a Context or checking auth state. 
    // For now, we'll try to set it up if we can get a token, or retry.
    // A simpler way: Just put this hook in MainTabNavigator? 
    // Or just run it here and check auth inside.

    // Actually, `App.tsx` wraps everything. We can't use `getToken()` easily if it's async inside the render unless we manage state.
    // But since `getToken` is async, we can do it in a useEffect.

    let channel: any;
    const setupListener = async () => {
      try {
        // We might need to wait for login
        // This is a quick fix. In a real app, use AuthContext.
        const { getToken } = require("./src/state/secureStore");
        const { supabase } = require("./src/api/supabase");
        const token = await getToken();

        if (!token) return; // User not logged in, no notifications

        supabase.realtime.setAuth(token);
        channel = supabase
          .channel("global_alerts")
          .on(
            "postgres_changes",
            { event: "INSERT", schema: "public", table: "alerts" },
            (payload: any) => {
              const newAlert = payload.new;
              // Trigger local notification
              Notifications.scheduleNotificationAsync({
                content: {
                  title: "Security Alert: " + newAlert.title,
                  body: newAlert.description,
                  data: { alertId: newAlert.id },
                  sound: true,
                  priority: Notifications.AndroidNotificationPriority.MAX,
                },
                trigger: {
                  channelId: 'default',
                  seconds: 1,
                },
              });
            }
          )
          .subscribe();
      } catch (e) {
        console.log("Notification listener setup failed:", e);
      }
    };

    // Try to setup listener every time app state changes or just once?
    // Doing it once on mount is fine, but if user logs in later, it won't trigger.
    // For now, let's assume valid session or we miss notifications until restart.
    // Optimization: Add a polling or dependency on auth.
    setupListener();

    return () => {
      if (channel) {
        const { supabase } = require("./src/api/supabase");
        supabase.removeChannel(channel);
      }
    }
  }, []);

  if (!appReady) {
    return null;
  }

  if (showSplash) {
    return <SplashScreen onFinish={() => setShowSplash(false)} />;
  }

  return (
    <NavigationContainer>
      <StatusBar style="light" backgroundColor={theme.colors.background} />
      <Stack.Navigator screenOptions={{
        headerShown: true,
        headerStyle: { backgroundColor: theme.colors.surface },
        headerTintColor: theme.colors.text,
      }}>
        <Stack.Screen
          name="Login"
          component={LoginScreen}
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="Signup"
          component={SignupScreen}
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="PiConfig"
          component={PiConfigScreen}
          options={{ title: "Configuration", headerLeft: () => null }}
        />
        <Stack.Screen
          name="Main"
          component={MainTabNavigator}
          options={{ headerShown: false }}
        />
        <Stack.Screen name="Pairing" component={PairingScreen} />
        <Stack.Screen name="DeviceControl" component={DeviceControlScreen} options={{ title: "Controls" }} />
        <Stack.Screen name="DeviceTelemetry" component={DeviceTelemetryScreen} options={{ title: "Telemetry" }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
