/**
 * DeviceStatusBadge
 * 
 * Header pill component displaying active wearable connectivity state.
 */
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, radii, spacing, typography } from '../../theme';
import { DeviceStatus, DataStatus } from '../../api/types';

interface DeviceStatusBadgeProps {
  deviceId: string | null;
  status: DeviceStatus | DataStatus;
  onPress?: () => void;
}

export const DeviceStatusBadge: React.FC<DeviceStatusBadgeProps> = ({
  deviceId,
  status,
  onPress,
}) => {
  const isConnected =
    status === DeviceStatus.CONNECTED || status === DataStatus.REAL_DATA;

  return (
    <TouchableOpacity
      activeOpacity={0.8}
      onPress={onPress}
      style={[
        styles.container,
        { backgroundColor: isConnected ? colors.statusConnectedBg : colors.surfaceMuted },
      ]}
    >
      <Ionicons
        name={isConnected ? 'watch' : 'watch-outline'}
        size={14}
        color={isConnected ? colors.statusConnected : colors.textMuted}
      />
      <Text
        style={[
          styles.text,
          { color: isConnected ? colors.statusConnected : colors.textSecondary },
        ]}
      >
        {deviceId ? `${deviceId}` : 'No Wearable'}
      </Text>
      <View
        style={[
          styles.indicatorDot,
          { backgroundColor: isConnected ? colors.statusConnected : colors.statusDisconnected },
        ]}
      />
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.sm + 2,
    paddingVertical: spacing.xs + 2,
    borderRadius: radii.pill,
    borderWidth: 1,
    borderColor: colors.border,
  },
  text: {
    fontSize: typography.size.xs,
    fontWeight: typography.weight.semibold,
    marginHorizontal: 6,
  },
  indicatorDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
});
