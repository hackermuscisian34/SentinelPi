import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createStackNavigator } from "@react-navigation/stack";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import LoginScreen from "./src/screens/LoginScreen";
import DashboardScreen from "./src/screens/DashboardScreen";
import PairingScreen from "./src/screens/PairingScreen";
import DevicesScreen from "./src/screens/DevicesScreen";
import AlertsScreen from "./src/screens/AlertsScreen";
import DeviceControlScreen from "./src/screens/DeviceControlScreen";

const Stack = createStackNavigator();
const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <NavigationContainer>
        <Stack.Navigator screenOptions={{ headerShown: true }}>
          <Stack.Screen name="Login" component={LoginScreen} />
          <Stack.Screen name="Dashboard" component={DashboardScreen} />
          <Stack.Screen name="Pairing" component={PairingScreen} />
          <Stack.Screen name="Devices" component={DevicesScreen} />
          <Stack.Screen name="Alerts" component={AlertsScreen} />
          <Stack.Screen name="DeviceControl" component={DeviceControlScreen} />
        </Stack.Navigator>
      </NavigationContainer>
    </QueryClientProvider>
  );
}
