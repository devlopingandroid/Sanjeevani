/**
 * PrimaryButton
 * 
 * Teal accent button matching reference UI with smooth press states.
 */
import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  ViewStyle,
  StyleProp,
} from 'react-native';
import { colors, radii, spacing, typography, shadows } from '../../theme';

interface PrimaryButtonProps {
  title: string;
  onPress: () => void;
  disabled?: boolean;
  loading?: boolean;
  variant?: 'primary' | 'secondary' | 'outline';
  style?: StyleProp<ViewStyle>;
  icon?: React.ReactNode;
}

export const PrimaryButton: React.FC<PrimaryButtonProps> = ({
  title,
  onPress,
  disabled = false,
  loading = false,
  variant = 'primary',
  style,
  icon,
}) => {
  const isOutline = variant === 'outline';
  const isSecondary = variant === 'secondary';

  return (
    <TouchableOpacity
      activeOpacity={0.8}
      onPress={onPress}
      disabled={disabled || loading}
      style={[
        styles.button,
        isOutline && styles.buttonOutline,
        isSecondary && styles.buttonSecondary,
        !isOutline && !isSecondary && shadows.button,
        disabled && styles.buttonDisabled,
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator
          color={isOutline ? colors.primary : colors.textOnPrimary}
          size="small"
        />
      ) : (
        <>
          {icon}
          <Text
            style={[
              styles.text,
              isOutline && styles.textOutline,
              isSecondary && styles.textSecondary,
              disabled && styles.textDisabled,
              icon ? { marginLeft: spacing.sm } : null,
            ]}
          >
            {title}
          </Text>
        </>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    backgroundColor: colors.primary,
    borderRadius: radii.button,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.lg,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonOutline: {
    backgroundColor: 'transparent',
    borderWidth: 1.5,
    borderColor: colors.primary,
  },
  buttonSecondary: {
    backgroundColor: colors.primaryTint,
    borderWidth: 1,
    borderColor: colors.borderTeal,
  },
  buttonDisabled: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
  },
  text: {
    color: colors.textOnPrimary,
    fontSize: typography.size.base,
    fontWeight: typography.weight.semibold,
  },
  textOutline: {
    color: colors.primary,
  },
  textSecondary: {
    color: colors.primaryDark,
  },
  textDisabled: {
    color: colors.textMuted,
  },
});
