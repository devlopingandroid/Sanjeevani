/**
 * Profile Screen
 * 
 * User profile, health preferences, connected device controls,
 * data privacy settings, and active session sign-out.
 * 
 * Information Architecture:
 * - My Profile Header & Status (Bound dynamically to verified Supabase user)
 * - Health (Health Preferences, My Wellness Record)
 * - Device (Sanjeevni Wearable)
 * - Privacy & Data (Privacy Controls, Data & Reports)
 * - Settings (Notifications, System Settings)
 * - Sign Out (Destroys local JWT and resets session)
 */
import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, Image } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../src/context/AuthContext';
import { useHealthData } from '../../src/context/HealthDataContext';
import { colors, spacing, typography, radii, shadows } from '../../src/theme';
import { SanjeevniCard } from '../../src/components/common/SanjeevniCard';
import { SectionHeader } from '../../src/components/common/SectionHeader';
import { resolveAvatarUrl, getUserInitials } from '../../src/utils/avatar';

export default function ProfileScreen() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const { activeDeviceId } = useHealthData();

  const handleLogout = () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out of Sanjeevni?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Sign Out',
          style: 'destructive',
          onPress: async () => {
            await logout();
            router.replace('/(auth)/login');
          },
        },
      ]
    );
  };

  const healthItems = [
    {
      title: 'My Wellness Record',
      subtitle: 'Biometric profile & verified telemetry history',
      icon: 'document-text-outline' as const,
      action: () => router.push('/records'),
      highlight: true,
    },
    {
      title: 'Health Preferences',
      subtitle: 'Autonomic nervous system calibration & thresholds',
      icon: 'pulse-outline' as const,
      action: () => router.push('/stress-details'),
    },
    {
      title: 'Nutrition & Hydration',
      subtitle: 'Dietary goals and daily hydration targets',
      icon: 'nutrition-outline' as const,
      action: () => router.push('/nutrition'),
    },
  ];

  const deviceItems = [
    {
      title: 'Sanjeevni Wearable',
      subtitle: activeDeviceId ? `Active Device: ${activeDeviceId}` : 'Waiting for device connection',
      icon: 'watch-outline' as const,
      action: () => router.push('/device-details'),
    },
  ];

  const privacyItems = [
    {
      title: 'Privacy & Security',
      subtitle: 'End-to-end telemetry encryption controls',
      icon: 'shield-checkmark-outline' as const,
      action: () => {},
    },
    {
      title: 'Data & Reports',
      subtitle: 'Export raw sensor logs & cloud sync status',
      icon: 'cloud-upload-outline' as const,
      action: () => router.push('/records'),
    },
  ];

  const settingItems = [
    {
      title: 'Notifications & Alerts',
      subtitle: 'Real-time autonomic stress alerts',
      icon: 'notifications-outline' as const,
      action: () => {},
    },
    {
      title: 'Application Settings',
      subtitle: 'Display theme, haptics, and sensor polling rate',
      icon: 'settings-outline' as const,
      action: () => {},
    },
  ];

  const userInitials = getUserInitials(user?.full_name, user?.email);
  const avatarUrl = resolveAvatarUrl(user?.profile_image_url);

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.screenTitle}>My Profile</Text>
        <Text style={styles.screenSubtitle}>Personalized wellness settings & records</Text>

        {/* Dynamic Authenticated User Card */}
        <SanjeevniCard style={styles.userCard}>
          <TouchableOpacity
            activeOpacity={0.8}
            onPress={() => router.push('/edit-profile')}
            style={styles.avatarWrapper}
          >
            {avatarUrl ? (
              <Image source={{ uri: avatarUrl }} style={styles.avatarImage} resizeMode="cover" />
            ) : (
              <View style={styles.avatarCircle}>
                <Text style={styles.avatarText}>{userInitials}</Text>
              </View>
            )}
            <View style={styles.cameraBadge}>
              <Ionicons name="camera" size={13} color={colors.textOnPrimary} />
            </View>
          </TouchableOpacity>

          <Text style={styles.userName}>{user?.full_name || user?.email || 'Authenticated User'}</Text>
          <Text style={styles.userEmail}>{user?.email}</Text>

          <View style={styles.statusPill}>
            <View style={[styles.greenDot, !activeDeviceId && styles.grayDot]} />
            <Text style={styles.statusText}>
              {activeDeviceId ? 'Wearable Paired' : 'No Wearable'}
            </Text>
          </View>

          <TouchableOpacity
            activeOpacity={0.8}
            onPress={() => router.push('/edit-profile')}
            style={styles.editProfileBtn}
          >
            <Ionicons name="create-outline" size={16} color={colors.primaryDark} />
            <Text style={styles.editProfileBtnText}>Edit My Profile</Text>
            <Ionicons name="chevron-forward" size={14} color={colors.primaryDark} />
          </TouchableOpacity>
        </SanjeevniCard>

        {/* Health Section - Featuring My Wellness Record */}
        <SectionHeader title="Health" subtitle="Biometrics & empirical wellness records" />
        <SanjeevniCard style={styles.menuCard}>
          {healthItems.map((item, idx) => (
            <TouchableOpacity
              key={idx}
              activeOpacity={0.7}
              onPress={item.action}
              style={[
                styles.menuItem,
                idx < healthItems.length - 1 && styles.menuItemBorder,
                item.highlight && styles.highlightRow,
              ]}
            >
              <View style={[styles.menuIconCircle, item.highlight && styles.highlightIconCircle]}>
                <Ionicons
                  name={item.icon}
                  size={20}
                  color={item.highlight ? colors.primaryDark : colors.primary}
                />
              </View>
              <View style={styles.menuTextContainer}>
                <Text style={[styles.menuTitle, item.highlight && styles.highlightTitle]}>
                  {item.title}
                </Text>
                <Text style={styles.menuSubtitle}>{item.subtitle}</Text>
              </View>
              <Ionicons
                name="chevron-forward"
                size={18}
                color={item.highlight ? colors.primary : colors.textMuted}
              />
            </TouchableOpacity>
          ))}
        </SanjeevniCard>

        {/* Device Section */}
        <SectionHeader title="Device" subtitle="Paired ESP32 biosensors & hardware diagnostics" />
        <SanjeevniCard style={styles.menuCard}>
          {deviceItems.map((item, idx) => (
            <TouchableOpacity
              key={idx}
              activeOpacity={0.7}
              onPress={item.action}
              style={[
                styles.menuItem,
                idx < deviceItems.length - 1 && styles.menuItemBorder,
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

        {/* Privacy & Data Section */}
        <SectionHeader title="Privacy & Data" subtitle="Data sovereignty and telemetry logs" />
        <SanjeevniCard style={styles.menuCard}>
          {privacyItems.map((item, idx) => (
            <TouchableOpacity
              key={idx}
              activeOpacity={0.7}
              onPress={item.action}
              style={[
                styles.menuItem,
                idx < privacyItems.length - 1 && styles.menuItemBorder,
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

        {/* Settings Section */}
        <SectionHeader title="Settings" subtitle="System and notification preferences" />
        <SanjeevniCard style={styles.menuCard}>
          {settingItems.map((item, idx) => (
            <TouchableOpacity
              key={idx}
              activeOpacity={0.7}
              onPress={item.action}
              style={[
                styles.menuItem,
                idx < settingItems.length - 1 && styles.menuItemBorder,
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

        {/* Sign Out Action Button */}
        <TouchableOpacity
          activeOpacity={0.8}
          onPress={handleLogout}
          style={styles.logoutBtn}
        >
          <Ionicons name="log-out-outline" size={20} color="#EF4444" />
          <Text style={styles.logoutBtnText}>Sign Out of Sanjeevni</Text>
        </TouchableOpacity>

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
    alignItems: 'center',
    paddingVertical: spacing.xl,
    paddingHorizontal: spacing.lg,
    marginBottom: spacing.base,
  },
  avatarWrapper: {
    position: 'relative',
    width: 88,
    height: 88,
    borderRadius: 44,
    marginBottom: spacing.md,
    borderWidth: 2.5,
    borderColor: colors.primaryTint,
    alignItems: 'center',
    justifyContent: 'center',
    ...shadows.card,
  },
  avatarImage: {
    width: 82,
    height: 82,
    borderRadius: 41,
  },
  avatarCircle: {
    width: 82,
    height: 82,
    borderRadius: 41,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    color: colors.textOnPrimary,
    fontSize: typography.size.xxl,
    fontWeight: typography.weight.bold,
  },
  cameraBadge: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: colors.primaryDark,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: colors.surface,
  },
  userName: {
    fontSize: typography.size.xl,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
    textAlign: 'center',
  },
  userEmail: {
    fontSize: typography.size.xs,
    color: colors.textMuted,
    marginTop: 3,
    textAlign: 'center',
  },
  statusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primaryTint,
    paddingHorizontal: spacing.md,
    paddingVertical: 3,
    borderRadius: radii.pill,
    marginTop: 8,
  },
  editProfileBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primaryTint,
    borderWidth: 1,
    borderColor: '#CCFBF1',
    borderRadius: radii.pill,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
    marginTop: spacing.md,
  },
  editProfileBtnText: {
    fontSize: typography.size.sm,
    fontWeight: typography.weight.bold,
    color: colors.primaryDark,
    marginHorizontal: spacing.xs,
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
    marginBottom: spacing.xs,
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
  highlightRow: {
    backgroundColor: '#F0FDFA',
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
  highlightIconCircle: {
    backgroundColor: '#CCFBF1',
  },
  menuTextContainer: {
    flex: 1,
  },
  menuTitle: {
    fontSize: typography.size.sm,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  highlightTitle: {
    color: colors.primaryDark,
  },
  menuSubtitle: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 2,
  },
  logoutBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FEE2E2',
    borderWidth: 1,
    borderColor: '#FECACA',
    borderRadius: radii.button,
    paddingVertical: spacing.md,
    marginTop: spacing.base,
  },
  logoutBtnText: {
    fontSize: typography.size.sm,
    fontWeight: typography.weight.bold,
    color: '#DC2626',
    marginLeft: spacing.xs,
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
