/**
 * MetricHistoryRow
 * 
 * Historical telemetry row displaying timestamp and real physiological values.
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, spacing, typography } from '../../theme';
import { formatBpm, formatMs, formatTempF, formatGSR, formatRelativeTime } from '../../utils/formatters';
import { VitalsHistoryRecord } from '../../api/types';

interface MetricHistoryRowProps {
  record: VitalsHistoryRecord;
}

export const MetricHistoryRow: React.FC<MetricHistoryRowProps> = ({ record }) => {
  return (
    <View style={styles.row}>
      <View style={styles.timeCol}>
        <Text style={styles.timeText}>{formatRelativeTime(record.timestamp)}</Text>
      </View>

      <View style={styles.metricCol}>
        <Text style={styles.metricValue}>{formatBpm(record.heart_rate_bpm)}</Text>
        <Text style={styles.metricLabel}>BPM</Text>
      </View>

      <View style={styles.metricCol}>
        <Text style={styles.metricValue}>{formatMs(record.hrv_rmssd_ms)}</Text>
        <Text style={styles.metricLabel}>HRV</Text>
      </View>

      <View style={styles.metricCol}>
        <Text style={styles.metricValue}>{formatTempF(record.temperature_f)}</Text>
        <Text style={styles.metricLabel}>Temp</Text>
      </View>

      <View style={styles.metricCol}>
        <Text style={styles.metricValue}>{formatGSR(record.skin_conductance_us)}</Text>
        <Text style={styles.metricLabel}>EDA</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.sm + 2,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderSubtle,
  },
  timeCol: {
    flex: 1.2,
  },
  timeText: {
    fontSize: typography.size.xs,
    color: colors.textMuted,
    fontWeight: typography.weight.medium,
  },
  metricCol: {
    flex: 1,
    alignItems: 'center',
  },
  metricValue: {
    fontSize: typography.size.sm,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  metricLabel: {
    fontSize: 10,
    color: colors.textMuted,
  },
});
