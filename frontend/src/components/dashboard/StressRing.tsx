/**
 * StressRing
 * 
 * Circular stress visualization centerpiece matching the reference design.
 * Displays the real probability, discrete stress state (LOW, MODERATE, HIGH),
 * or honest unavailable status without ever faking values.
 */
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { colors, radii, spacing, typography, shadows } from '../../theme';
import { DataStatus } from '../../api/types';
import { formatStressScore } from '../../utils/formatters';

interface StressRingProps {
  score: number | null | undefined;
  level: string | null | undefined;
  dataStatus: DataStatus;
  message?: string;
  onPress?: () => void;
}

export const StressRing: React.FC<StressRingProps> = ({
  score,
  level,
  dataStatus,
  message,
  onPress,
}) => {
  const isRealData = dataStatus === DataStatus.REAL_DATA && score !== null && score !== undefined;

  const getRingColor = () => {
    if (!isRealData) return colors.statusNoData;
    if (level === 'HIGH' || (score !== undefined && score !== null && score > 65)) {
      return colors.stressHigh;
    }
    if (level === 'MODERATE' || (score !== undefined && score !== null && score > 35)) {
      return colors.stressModerate;
    }
    return colors.stressLow;
  };

  const getSubtitle = () => {
    if (!isRealData) {
      switch (dataStatus) {
        case DataStatus.INSUFFICIENT_DATA:
          return 'Collecting sensor window (30s)...';
        case DataStatus.DEVICE_DISCONNECTED:
          return 'Wearable disconnected';
        case DataStatus.SENSOR_ERROR:
          return 'Sensor lead-off detected';
        case DataStatus.MODEL_UNAVAILABLE:
          return 'ML model offline';
        case DataStatus.NO_DATA:
        default:
          return 'Waiting for sensor telemetry';
      }
    }
    if (level === 'HIGH') return 'Elevated Sympathetic Arousal';
    if (level === 'MODERATE') return 'Moderate Stress Detected';
    return 'Calm & Restorative Baseline';
  };

  const ringColor = getRingColor();
  const displayScore = isRealData ? formatStressScore(score) : '--';
  const displayLevel = isRealData ? (level || 'EVALUATED') : 'NO TELEMETRY';

  return (
    <TouchableOpacity
      activeOpacity={onPress ? 0.9 : 1}
      onPress={onPress}
      style={[styles.container, shadows.cardFloating]}
    >
      <View style={styles.headerRow}>
        <Text style={styles.cardHeader}>CURRENT ESTIMATED STRESS</Text>
        <View style={[styles.statusDot, { backgroundColor: ringColor }]} />
      </View>

      {/* Ring Visualizer */}
      <View style={styles.ringOuter}>
        <View style={[styles.ringTrack, { borderColor: isRealData ? colors.primarySubtle : colors.border }]}>
          <View style={[styles.ringProgress, { borderColor: ringColor }]} />
          <View style={styles.ringInner}>
            <Text style={[styles.scoreValue, { color: isRealData ? colors.textPrimary : colors.textMuted }]}>
              {displayScore}
            </Text>
            <Text style={[styles.levelLabel, { color: ringColor }]}>
              {displayLevel}
            </Text>
          </View>
        </View>
      </View>

      <Text style={styles.subtitleText}>{getSubtitle()}</Text>

      {message ? (
        <Text style={styles.detailMessage} numberOfLines={2}>
          {message}
        </Text>
      ) : null}

      <View style={styles.footerHint}>
        <Text style={styles.footerHintText}>
          {isRealData ? 'Tap for 26-feature breakdown →' : 'Connect wearable to begin stream'}
        </Text>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.surface,
    borderRadius: radii.cardLg,
    borderWidth: 1.5,
    borderColor: colors.borderTeal,
    padding: spacing.lg,
    alignItems: 'center',
    marginVertical: spacing.md,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%',
    marginBottom: spacing.base,
  },
  cardHeader: {
    fontSize: typography.size.xs,
    fontWeight: typography.weight.bold,
    color: colors.primaryDark,
    letterSpacing: 0.8,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  ringOuter: {
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: spacing.sm,
  },
  ringTrack: {
    width: 170,
    height: 170,
    borderRadius: 85,
    borderWidth: 10,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primaryTint,
  },
  ringProgress: {
    position: 'absolute',
    width: 170,
    height: 170,
    borderRadius: 85,
    borderWidth: 10,
    borderLeftColor: 'transparent',
    borderBottomColor: 'transparent',
    transform: [{ rotate: '45deg' }],
  },
  ringInner: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  scoreValue: {
    fontSize: typography.size.display,
    fontWeight: typography.weight.bold,
    letterSpacing: -1,
  },
  levelLabel: {
    fontSize: typography.size.xs,
    fontWeight: typography.weight.bold,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginTop: 2,
  },
  subtitleText: {
    fontSize: typography.size.sm,
    fontWeight: typography.weight.medium,
    color: colors.textSecondary,
    textAlign: 'center',
    marginTop: spacing.md,
  },
  detailMessage: {
    fontSize: typography.size.xs,
    color: colors.textMuted,
    textAlign: 'center',
    marginTop: 4,
    paddingHorizontal: spacing.sm,
  },
  footerHint: {
    marginTop: spacing.md,
    paddingTop: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.borderSubtle,
    width: '100%',
    alignItems: 'center',
  },
  footerHintText: {
    fontSize: typography.size.xs,
    color: colors.primary,
    fontWeight: typography.weight.semibold,
  },
});
