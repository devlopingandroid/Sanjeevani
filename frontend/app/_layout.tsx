/**
 * Root Stack Layout
 * 
 * Configures global providers (AuthProvider, HealthDataProvider),
 * navigation stack, route guarding, and modals.
 */
import React, { useEffect } from 'react';
import { Stack, useRouter, useSegments } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import * as SplashScreen from 'expo-splash-screen';
import { AuthProvider, useAuth } from '../src/context/AuthContext';
import { HealthDataProvider } from '../src/context/HealthDataContext';
import { colors } from '../src/theme';

export { ErrorBoundary } from 'expo-router';

// Prevent splash screen from auto-hiding before initialization
SplashScreen.preventAutoHideAsync().catch(() => {});

function RootNavigationGuard() {
  const { isAuthenticated, isLoading } = useAuth();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;

    const inAuthGroup = segments[0] === '(auth)';

    if (!isAuthenticated && !inAuthGroup) {
      // Redirect unauthenticated user to login screen
      router.replace('/(auth)/login');
    } else if (isAuthenticated && inAuthGroup) {
      // Redirect authenticated user into main tabs
      router.replace('/(tabs)');
    }
  }, [isAuthenticated, isLoading, segments]);

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: colors.surface },
        headerTintColor: colors.textPrimary,
        headerTitleStyle: { fontWeight: '600' },
        headerShadowVisible: false,
        contentStyle: { backgroundColor: colors.background },
      }}
    >
      <Stack.Screen name="(auth)" options={{ headerShown: false }} />
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen
        name="records"
        options={{
          title: 'My Wellness Record',
          headerBackTitle: 'Back',
        }}
      />
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
  );
}

export default function RootLayout() {
  useEffect(() => {
    SplashScreen.hideAsync().catch(() => {});
  }, []);

  return (
    <SafeAreaProvider>
      <AuthProvider>
        <HealthDataProvider>
          <StatusBar style="dark" />
          <RootNavigationGuard />
        </HealthDataProvider>
      </AuthProvider>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    backgroundColor: colors.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
