
import React from "react";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { Ionicons } from "@expo/vector-icons";
import DashboardScreen from "../screens/DashboardScreen";
import DevicesScreen from "../screens/DevicesScreen";
import AlertsScreen from "../screens/AlertsScreen";
import SettingsScreen from "../screens/SettingsScreen";
import { theme } from "../ui/theme";

const Tab = createBottomTabNavigator();

export default function MainTabNavigator() {
    return (
        <Tab.Navigator
            screenOptions={({ route }) => ({
                headerShown: false,
                tabBarStyle: {
                    backgroundColor: theme.colors.surface,
                    borderTopColor: theme.colors.muted,
                    height: 60,
                    paddingBottom: 8,
                    paddingTop: 8,
                },
                tabBarActiveTintColor: theme.colors.primary,
                tabBarInactiveTintColor: theme.colors.textSecondary,
                tabBarIcon: ({ focused, color, size }) => {
                    let iconName: any;

                    if (route.name === "Dashboard") {
                        iconName = focused ? "home" : "home-outline";
                    } else if (route.name === "Devices") {
                        iconName = focused ? "hardware-chip" : "hardware-chip-outline";
                    } else if (route.name === "Alerts") {
                        iconName = focused ? "notifications" : "notifications-outline";
                    } else if (route.name === "Settings") {
                        iconName = focused ? "settings" : "settings-outline";
                    }

                    return <Ionicons name={iconName} size={size} color={color} />;
                },
            })}
        >
            <Tab.Screen name="Dashboard" component={DashboardScreen} />
            <Tab.Screen name="Devices" component={DevicesScreen} />
            <Tab.Screen name="Alerts" component={AlertsScreen} />
            <Tab.Screen name="Settings" component={SettingsScreen} />
        </Tab.Navigator>
    );
}
