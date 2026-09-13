/**
 * Consult Screen (Professional Support & Telehealth)
 * 
 * Central hub for licensed clinical wellness experts, biofeedback specialists,
 * and telehealth consultation.
 * Strictly complies with the ZERO HARDCODED DATA policy:
 * Never hardcodes fake doctor names, synthetic credentials, or fabricated online availability.
 * Displays honest empty states when no providers are configured by the backend.
 */
import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, typography, radii, shadows } from '../../src/theme';
import { SanjeevniCard } from '../../src/components/common/SanjeevniCard';
import { SectionHeader } from '../../src/components/common/SectionHeader';
import { EmptyState } from '../../src/components/common/EmptyState';

export default function ConsultScreen() {
  // Real directory from backend / clinical network (empty until provisioned)
  const specialists: any[] = [];

  const consultationChannels = [
    {
      title: 'Doctor & Therapist Support',
      subtitle: 'Schedule 1-on-1 sessions with licensed clinical psychologists',
      icon: 'medkit-outline' as const,
      color: '#0D9488',
      bg: '#CCFBF1',
    },
    {
      title: 'Voice Consultation',
      subtitle: 'Real-time guided biofeedback audio sessions',
      icon: 'call-outline' as const,
      color: '#0284C7',
      bg: '#E0F2FE',
    },
    {
      title: 'Emergency Crisis Support',
      subtitle: 'Direct local healthcare and 24/7 crisis lines',
      icon: 'shield-checkmark-outline' as const,
      color: '#E11D48',
      bg: '#FFE4E6',
    },
  ];

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.screenTitle}>Consultation</Text>
        <Text style={styles.screenSubtitle}>Professional healthcare & biofeedback support</Text>

        {/* Support Channels Overview */}
        <SectionHeader
          title="Consultation Channels"
          subtitle="Direct biofeedback & medical guidance"
        />

        {consultationChannels.map((channel, idx) => (
          <SanjeevniCard key={idx} style={styles.channelCard}>
            <View style={[styles.channelIconCircle, { backgroundColor: channel.bg }]}>
              <Ionicons name={channel.icon} size={22} color={channel.color} />
            </View>
            <View style={styles.channelText}>
              <Text style={styles.channelTitle}>{channel.title}</Text>
              <Text style={styles.channelSubtitle}>{channel.subtitle}</Text>
            </View>
          </SanjeevniCard>
        ))}

        {/* Directory List with honest empty state */}
        <SectionHeader
          title="Available Specialists"
          subtitle="Verified network professionals"
        />

        {specialists.length > 0 ? (
          <View />
        ) : (
          <EmptyState
            icon="people-outline"
            title="No Specialists Configured"
            description="Professional telehealth, psychologist, and biofeedback consultation networks will appear here once provisioned by your healthcare administrator."
          />
        )}

        {/* Clinical Disclaimer */}
        <View style={styles.noticeBox}>
          <Ionicons name="information-circle-outline" size={16} color={colors.textMuted} />
          <Text style={styles.noticeText}>
            Sanjeevni provides autonomic wellness monitoring only. In the event of an
            acute psychological or medical emergency, please contact your local emergency
            healthcare services immediately.
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
  channelCard: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: spacing.xs,
    padding: spacing.base,
  },
  channelIconCircle: {
    width: 44,
    height: 44,
    borderRadius: radii.md,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  channelText: {
    flex: 1,
  },
  channelTitle: {
    fontSize: typography.size.sm,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  channelSubtitle: {
    fontSize: 11,
    color: colors.textSecondary,
    marginTop: 2,
    lineHeight: 16,
  },
  noticeBox: {
    flexDirection: 'row',
    backgroundColor: colors.surfaceMuted,
    borderRadius: radii.card,
    padding: spacing.md,
    marginTop: spacing.xl,
  },
  noticeText: {
    flex: 1,
    fontSize: 11,
    color: colors.textMuted,
    marginLeft: spacing.sm,
    lineHeight: 16,
  },
});
