/**
 * SanjeevniInsight
 * 
 * Calm wellness observation card inspired by the reference design.
 * Only presents insights supported by genuine backend data.
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, radii, spacing, typography, shadows } from '../../theme';
import { DataStatus } from '../../api/types';

interface SanjeevniInsightProps {
  dataStatus: DataStatus;
  stressScore: number | null | undefined;
  heartRate: number | null | undefined;
}

export const SanjeevniInsight: React.FC<SanjeevniInsightProps> = ({
  dataStatus,
  stressScore,
  heartRate,
}) => {
  const isRealData = dataStatus === DataStatus.REAL_DATA && stressScore !== null && stressScore !== undefined;

  const getInsightContent = () => {
    if (!isRealData) {
      return {
        title: 'Awaiting Real Telemetry',
        message: 'Personalized physiological observations will appear here once adequate real sensor data has been collected from your ESP32 wearable.',
        icon: 'sparkles-outline' as const,
        badge: 'Status: Standby',
      };
    }

    if (stressScore > 65) {
      return {
        title: 'Elevated Sympathetic Tone',
        message: 'Autonomic nervous system patterns indicate heightened arousal. Consider taking a 3-minute diaphragmatic breathing break.',
        icon: 'pulse' as const,
        badge: 'Actionable Advice',
      };
    }

    if (stressScore > 35) {
      return {
        title: 'Balanced Adaptation',
        message: 'Your physiological markers reflect normal active engagement with stable autonomic homeostasis.',
        icon: 'shield-checkmark-outline' as const,
        badge: 'Optimal Engagement',
      };
    }

    return {
      title: 'Restorative Equilibrium',
      message: 'Parasympathetic tone is dominant. Heart rate variability and skin conductance reflect high relaxation.',
      icon: 'leaf' as const,
      badge: 'Recovery Mode',
    };
  };

  const { title, message, icon, badge } = getInsightContent();

  return (
    <View style={[styles.card, shadows.card]}>
      <View style={styles.topRow}>
        <View style={styles.badgePill}>
          <Text style={styles.badgeText}>{badge}</Text>
        </View>
        <Ionicons name={icon} size={18} color={colors.primary} />
      </View>

      <Text style={styles.title}>{title}</Text>
      <Text style={styles.message}>{message}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.primaryTint,
    borderRadius: radii.card,
    borderWidth: 1,
    borderColor: colors.borderTeal,
    padding: spacing.base,
    marginVertical: spacing.sm,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.sm,
  },
  badgePill: {
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.sm,
    paddingVertical: 3,
    borderRadius: radii.pill,
    borderWidth: 1,
    borderColor: colors.borderTeal,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: typography.weight.bold,
    color: colors.primaryDark,
  },
  title: {
    fontSize: typography.size.base,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
    marginBottom: 4,
  },
  message: {
    fontSize: typography.size.sm,
    color: colors.textSecondary,
    lineHeight: 20,
  },
});
