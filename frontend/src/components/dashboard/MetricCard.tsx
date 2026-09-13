/**
 * MetricCard
 * 
 * Compact, modern card for displaying individual physiological parameters.
 * Strictly presents "--" if sensor reading is unavailable or unphysiological.
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, radii, spacing, typography, shadows } from '../../theme';

interface MetricCardProps {
  icon: keyof typeof Ionicons.glyphMap;
  iconColor?: string;
  title: string;
  value: string;
  unit: string;
  subtitle?: string;
  accentBg?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  icon,
  iconColor = colors.primary,
  title,
  value,
  unit,
  subtitle,
  accentBg = colors.primaryTint,
}) => {
  const isAvailable = value !== '--';

  return (
    <View style={[styles.card, shadows.card]}>
      <View style={styles.topRow}>
        <View style={[styles.iconCircle, { backgroundColor: accentBg }]}>
          <Ionicons name={icon} size={18} color={iconColor} />
        </View>
        <Text style={styles.title}>{title}</Text>
      </View>

      <View style={styles.valueRow}>
        <Text style={[styles.valueText, !isAvailable && styles.valueUnavailable]}>
          {value}
        </Text>
        {isAvailable && unit ? (
          <Text style={styles.unitText}>{unit}</Text>
        ) : null}
      </View>

      <Text style={styles.subtitleText} numberOfLines={1}>
        {subtitle || (isAvailable ? 'Live Telemetry' : 'Unavailable')}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radii.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    flex: 1,
    minWidth: 140,
    margin: spacing.xs,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  iconCircle: {
    width: 32,
    height: 32,
    borderRadius: radii.pill,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.sm,
  },
  title: {
    fontSize: typography.size.xs,
    fontWeight: typography.weight.semibold,
    color: colors.textSecondary,
  },
  valueRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginVertical: 2,
  },
  valueText: {
    fontSize: typography.size.xl,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  valueUnavailable: {
    color: colors.textMuted,
  },
  unitText: {
    fontSize: typography.size.xs,
    fontWeight: typography.weight.medium,
    color: colors.textMuted,
    marginLeft: 4,
  },
  subtitleText: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 2,
  },
});
