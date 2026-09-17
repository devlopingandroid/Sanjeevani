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
  const isDemoMode = dataStatus === DataStatus.DEMO_DATA;
  const isTelemetryActive = dataStatus === DataStatus.REAL_DATA || dataStatus === DataStatus.INSUFFICIENT_DATA || isDemoMode;
  const isModelEvaluated = (isTelemetryActive || isDemoMode) && score !== null && score !== undefined;

  const getRingColor = () => {
    if (isDemoMode) {
      return '#F59E0B'; // Amber demo accent
    }
    if (isModelEvaluated) {
      if (level === 'HIGH' || (score !== undefined && score !== null && score > 65)) {
        return colors.stressHigh;
      }
      if (level === 'MODERATE' || (score !== undefined && score !== null && score > 35)) {
        return colors.stressModerate;
      }
      return colors.stressLow;
    }
    if (isTelemetryActive) {
      return colors.statusConnected;
    }
    return colors.statusNoData;
  };

  const getSubtitle = () => {
    if (isDemoMode) {
      return 'Temporary exhibition simulation — GSR sensor unavailable.';
    }
    if (isModelEvaluated) {
      if (level === 'HIGH') return 'Elevated Sympathetic Arousal';
      if (level === 'MODERATE') return 'Moderate Stress Detected';
      return 'Calm & Restorative Baseline';
    }
    if (isTelemetryActive) {
      return 'Live wearable telemetry active';
    }
    switch (dataStatus) {
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
  };

  const getFooterHint = () => {
    if (isDemoMode) return 'Exhibition Simulation Mode Active';
    if (isModelEvaluated) return 'Tap for 26-feature breakdown →';
    if (isTelemetryActive) return 'Tap Evaluate 30s Buffer below to run ML inference';
    return 'Connect wearable to begin stream';
  };

  const ringColor = getRingColor();
  const displayScore = isModelEvaluated ? formatStressScore(score) : '--';
  const displayLevel = isModelEvaluated
    ? (isDemoMode ? 'DEMO STRESS' : (level || 'EVALUATED'))
    : (isDemoMode ? 'DEMO DATA' : (isTelemetryActive ? 'CONNECTED' : 'NO TELEMETRY'));

  return (
    <TouchableOpacity
      activeOpacity={onPress ? 0.9 : 1}
      onPress={onPress}
      style={[styles.container, shadows.cardFloating, isDemoMode && { borderColor: '#F59E0B' }]}
    >
      <View style={styles.headerRow}>
        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
          <Text style={styles.cardHeader}>CURRENT ESTIMATED STRESS</Text>
          {isDemoMode && (
            <View style={{ backgroundColor: '#FEF3C7', paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4, marginLeft: 8 }}>
              <Text style={{ fontSize: 10, fontWeight: 'bold', color: '#D97706' }}>DEMO DATA</Text>
            </View>
          )}
        </View>
        <View style={[styles.statusDot, { backgroundColor: ringColor }]} />
      </View>

      {/* Ring Visualizer */}
      <View style={styles.ringOuter}>
        <View style={[styles.ringTrack, { borderColor: isTelemetryActive ? colors.primarySubtle : colors.border }]}>
          <View style={[styles.ringProgress, { borderColor: ringColor }]} />
          <View style={styles.ringInner}>
            <Text style={[styles.scoreValue, { color: isModelEvaluated ? colors.textPrimary : colors.textMuted }]}>
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
        <Text style={[styles.footerHintText, isDemoMode && { color: '#D97706' }]}>{getFooterHint()}</Text>
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
