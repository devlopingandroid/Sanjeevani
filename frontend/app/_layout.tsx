/**
 * Root Stack Layout
 * 
 * Configures global providers, navigation stack, and modals.
 */
import React, { useEffect } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import * as SplashScreen from 'expo-splash-screen';
import { HealthDataProvider } from '../src/context/HealthDataContext';
import { colors } from '../src/theme';

export { ErrorBoundary } from 'expo-router';

// Prevent splash screen from auto-hiding before initialization
SplashScreen.preventAutoHideAsync().catch(() => {});

export default function RootLayout() {
  useEffect(() => {
    SplashScreen.hideAsync().catch(() => {});
  }, []);

  return (
    <SafeAreaProvider>
      <HealthDataProvider>
        <StatusBar style="dark" />
        <Stack
          screenOptions={{
            headerStyle: { backgroundColor: colors.surface },
            headerTintColor: colors.textPrimary,
            headerTitleStyle: { fontWeight: '600' },
            headerShadowVisible: false,
            contentStyle: { backgroundColor: colors.background },
          }}
        >
          <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
          <Stack.Screen
            name="stress-details"
            options={{
              presentation: 'modal',
              title: 'Estimated Stress Analysis',
              headerBackTitle: 'Close',
            }}
          />
          <Stack.Screen
            name="device-details"
            options={{
              presentation: 'modal',
              title: 'Sanjeevni Wearable',
              headerBackTitle: 'Back',
            }}
          />
          <Stack.Screen
            name="nutrition"
            options={{
              title: 'Food & Nutrition',
              headerBackTitle: 'Back',
            }}
          />
          <Stack.Screen
            name="yoga-breathing"
            options={{
              title: 'Breathing & Yoga',
              headerBackTitle: 'Back',
            }}
          />
          <Stack.Screen
            name="support"
            options={{
              title: 'Professional Support',
              headerBackTitle: 'Back',
            }}
          />
        </Stack>
      </HealthDataProvider>
    </SafeAreaProvider>
  );
}
