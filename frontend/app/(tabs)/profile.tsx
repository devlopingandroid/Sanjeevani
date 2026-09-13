/**
 * Profile Screen
 * 
 * User profile, health preferences, connected device controls,
 * and data privacy settings.
 */
import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useHealthData } from '../../src/context/HealthDataContext';
import { colors, spacing, typography, radii, shadows } from '../../src/theme';
import { SanjeevniCard } from '../../src/components/common/SanjeevniCard';
import { SectionHeader } from '../../src/components/common/SectionHeader';

export default function ProfileScreen() {
  const router = useRouter();
  const { activeDeviceId, summary } = useHealthData();

  const settingsItems = [
    {
      title: 'Connected Wearable',
      subtitle: activeDeviceId ? `Active: ${activeDeviceId}` : 'No device configured',
      icon: 'watch-outline' as const,
      action: () => router.push('/device-details'),
    },
    {
      title: 'Estimated Stress Thresholds',
      subtitle: 'Autonomic nervous system calibration',
      icon: 'pulse-outline' as const,
      action: () => router.push('/stress-details'),
    },
    {
      title: 'Food & Nutrition Preferences',
      subtitle: 'Dietary goals and hydration targets',
      icon: 'nutrition-outline' as const,
      action: () => router.push('/nutrition'),
    },
    {
      title: 'Data & Privacy Controls',
      subtitle: 'Local encryption & Supabase cloud sync',
      icon: 'shield-checkmark-outline' as const,
      action: () => {},
    },
    {
      title: 'Support & Professional Consultation',
      subtitle: 'Connect with wellness experts',
      icon: 'headset-outline' as const,
      action: () => router.push('/support'),
    },
  ];

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.screenTitle}>My Profile</Text>
        <Text style={styles.screenSubtitle}>Personalized wellness settings & security</Text>

        {/* User Card */}
        <SanjeevniCard style={styles.userCard}>
          <View style={styles.avatarCircle}>
            <Text style={styles.avatarText}>SJ</Text>
          </View>
          <View style={styles.userInfo}>
            <Text style={styles.userName}>Sanjeevni User</Text>
            <Text style={styles.userEmail}>Local Profile (Not signed in)</Text>
            <View style={styles.statusPill}>
              <View style={[styles.greenDot, !activeDeviceId && styles.grayDot]} />
              <Text style={styles.statusText}>
                {activeDeviceId ? 'Wearable Paired' : 'No Wearable'}
              </Text>
            </View>
          </View>
        </SanjeevniCard>

        {/* Settings Sections */}
        <SectionHeader title="Settings & Management" subtitle="Configure wearable and telemetry" />

        <SanjeevniCard style={styles.menuCard}>
          {settingsItems.map((item, idx) => (
            <TouchableOpacity
              key={idx}
              activeOpacity={0.7}
              onPress={item.action}
              style={[
                styles.menuItem,
                idx < settingsItems.length - 1 && styles.menuItemBorder,
              ]}
            >
              <View style={styles.menuIconCircle}>
                <Ionicons name={item.icon} size={20} color={colors.primary} />
              </View>
              <View style={styles.menuTextContainer}>
                <Text style={styles.menuTitle}>{item.title}</Text>
                <Text style={styles.menuSubtitle}>{item.subtitle}</Text>
              </View>
              <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
            </TouchableOpacity>
          ))}
        </SanjeevniCard>

        {/* Clinical Disclaimer Card */}
        <View style={styles.disclaimerCard}>
          <Ionicons name="information-circle-outline" size={18} color={colors.textMuted} />
          <Text style={styles.disclaimerText}>
            SANJEEVNI is an autonomic wellness monitoring platform. Estimations of stress,
            heart rate, and electrodermal responses are intended for general wellness and
            are NOT a clinical diagnosis or medical device substitute.
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollContent: {
    paddingHorizontal: spacing.gutter,
    paddingBottom: spacing.xxl,
  },
  screenTitle: {
    fontSize: typography.size.xxl,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
    marginTop: spacing.sm,
  },
  screenSubtitle: {
    fontSize: typography.size.xs,
    color: colors.textMuted,
    marginBottom: spacing.base,
  },
  userCard: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.lg,
  },
  avatarCircle: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  avatarText: {
    color: colors.textOnPrimary,
    fontSize: typography.size.xl,
    fontWeight: typography.weight.bold,
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontSize: typography.size.lg,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  userEmail: {
    fontSize: typography.size.xs,
    color: colors.textMuted,
    marginTop: 2,
  },
  statusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primaryTint,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radii.pill,
    alignSelf: 'flex-start',
    marginTop: 6,
  },
  greenDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.statusConnected,
    marginRight: 6,
  },
  grayDot: {
    backgroundColor: colors.statusNoData,
  },
  statusText: {
    fontSize: 10,
    fontWeight: typography.weight.semibold,
    color: colors.primaryDark,
  },
  menuCard: {
    padding: 0,
    overflow: 'hidden',
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.base,
  },
  menuItemBorder: {
    borderBottomWidth: 1,
    borderBottomColor: colors.borderSubtle,
  },
  menuIconCircle: {
    width: 36,
    height: 36,
    borderRadius: radii.sm,
    backgroundColor: colors.primaryTint,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  menuTextContainer: {
    flex: 1,
  },
  menuTitle: {
    fontSize: typography.size.sm,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  menuSubtitle: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 2,
  },
  disclaimerCard: {
    flexDirection: 'row',
    backgroundColor: colors.surfaceMuted,
    borderRadius: radii.card,
    padding: spacing.md,
    marginTop: spacing.xl,
    alignItems: 'flex-start',
  },
  disclaimerText: {
    flex: 1,
    fontSize: 11,
    color: colors.textMuted,
    marginLeft: spacing.sm,
    lineHeight: 16,
  },
});
