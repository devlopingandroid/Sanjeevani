/**
 * StatusBadge
 * 
 * Pill badge for displaying device, telemetry, and stress states cleanly.
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, radii, spacing, typography } from '../../theme';
import { DataStatus, DeviceStatus } from '../../api/types';
import { formatStatusLabel } from '../../utils/formatters';

interface StatusBadgeProps {
  status: DataStatus | DeviceStatus | string;
  label?: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  label,
  size = 'md',
}) => {
  const getBadgeColors = () => {
    switch (status) {
      case DataStatus.REAL_DATA:
      case DeviceStatus.CONNECTED:
      case 'CONNECTED':
      case 'BASELINE':
      case 'LOW':
        return { bg: colors.statusConnectedBg, text: colors.statusConnected };

      case 'MODERATE':
      case DataStatus.INSUFFICIENT_DATA:
      case DeviceStatus.WAITING_FOR_DATA:
      case 'COLLECTING':
        return { bg: colors.statusWaitingBg, text: colors.statusWaiting };

      case 'HIGH':
      case 'STRESS':
      case DataStatus.DEVICE_DISCONNECTED:
      case DeviceStatus.DISCONNECTED:
      case DataStatus.SENSOR_ERROR:
      case DeviceStatus.SENSOR_ERROR:
        return { bg: colors.statusDisconnectedBg, text: colors.statusDisconnected };

      case DataStatus.MODEL_UNAVAILABLE:
      case DataStatus.NO_DATA:
      case DeviceStatus.NO_DATA:
      default:
        return { bg: colors.statusNoDataBg, text: colors.statusNoData };
    }
  };

  const { bg, text } = getBadgeColors();
  const displayLabel = label || (typeof status === 'string' ? status : formatStatusLabel(status));

  return (
    <View
      style={[
        styles.badge,
        { backgroundColor: bg },
        size === 'sm' && styles.badgeSm,
      ]}
    >
      <View style={[styles.dot, { backgroundColor: text }]} />
      <Text
        style={[
          styles.text,
          { color: text },
          size === 'sm' && styles.textSm,
        ]}
      >
        {displayLabel}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.sm + 2,
    paddingVertical: spacing.xs,
    borderRadius: radii.pill,
    alignSelf: 'flex-start',
  },
  badgeSm: {
    paddingHorizontal: spacing.xs + 2,
    paddingVertical: 2,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 6,
  },
  text: {
    fontSize: typography.size.xs,
    fontWeight: typography.weight.semibold,
    textTransform: 'capitalize',
  },
  textSm: {
    fontSize: 10,
  },
});
