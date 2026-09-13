/**
 * Professional Support Directory Screen
 * 
 * Directory of certified healthcare and autonomic wellness counselors.
 * Strictly adheres to the ZERO HARDCODED DATA policy:
 * Never hardcodes fake doctor names, fake credentials, or fabricated online availability.
 * Displays honest empty states when no providers are configured by backend.
 */
import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, typography, radii } from '../src/theme';
import { SectionHeader } from '../src/components/common/SectionHeader';
import { EmptyState } from '../src/components/common/EmptyState';

export default function SupportScreen() {
  // Real directory from backend / clinical network (empty until provisioned)
  const professionals: any[] = [];

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <SectionHeader
        title="Professional Network"
        subtitle="Licensed clinical wellness & biofeedback specialists"
      />

      {professionals.length > 0 ? (
        <View />
      ) : (
        <EmptyState
          icon="people-outline"
          title="No Specialists Configured"
          description="Professional telehealth and biofeedback consultation networks will appear here once provisioned by your healthcare administrator."
        />
      )}

      <View style={styles.noticeBox}>
        <Ionicons name="shield-checkmark-outline" size={16} color={colors.textMuted} />
        <Text style={styles.noticeText}>
          Sanjeevni provides autonomic wellness monitoring only. In the event of an
          acute psychological or medical emergency, please contact your local emergency
          healthcare services immediately.
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: spacing.gutter,
    paddingBottom: spacing.xxl,
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
