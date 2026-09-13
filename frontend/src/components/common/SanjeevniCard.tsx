/**
 * SanjeevniCard
 * 
 * Reusable rounded card with calm border, soft shadow, and consistent padding.
 */
import React from 'react';
import { View, StyleSheet, ViewStyle, StyleProp } from 'react-native';
import { colors, radii, spacing, shadows } from '../../theme';

interface SanjeevniCardProps {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
  floating?: boolean;
  tinted?: boolean;
}

export const SanjeevniCard: React.FC<SanjeevniCardProps> = ({
  children,
  style,
  floating = false,
  tinted = false,
}) => {
  return (
    <View
      style={[
        styles.card,
        floating ? shadows.cardFloating : shadows.card,
        tinted && styles.tinted,
        style,
      ]}
    >
      {children}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radii.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.base,
  },
  tinted: {
    backgroundColor: colors.primaryTint,
    borderColor: colors.primarySubtle,
  },
});
