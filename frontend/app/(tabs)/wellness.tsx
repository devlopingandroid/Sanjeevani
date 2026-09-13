/**
 * Wellness Screen
 * 
 * Interactive wellness portal featuring Yoga, Guided Breathing,
 * Deep Relaxation, Nutrition, and Professional Support.
 */
import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { colors, spacing, typography } from '../../src/theme';
import { WellnessCard } from '../../src/components/wellness/WellnessCard';
import { SectionHeader } from '../../src/components/common/SectionHeader';

export default function WellnessScreen() {
  const router = useRouter();

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.screenTitle}>Wellness & Restoration</Text>
        <Text style={styles.screenSubtitle}>Holistic body and mind recovery routines</Text>

        <SectionHeader title="Autonomic Regulation" subtitle="Evidence-based breathing exercises" />
        <WellnessCard
          title="Diaphragmatic Breathing"
          subtitle="4-7-8 parasympathetic activation to lower heart rate and reduce stress"
          duration="5 min"
          icon="leaf"
          accentColor={colors.breathingAccent}
          bgColor={colors.breathingBg}
          onPress={() => router.push('/yoga-breathing')}
        />
        <WellnessCard
          title="Box Breathing (Sama Vritti)"
          subtitle="Equal 4-count cycles to stabilize autonomic equilibrium during acute stress"
          duration="4 min"
          icon="snow"
          accentColor="#0284C7"
          bgColor="#E0F2FE"
          onPress={() => router.push('/yoga-breathing')}
        />

        <SectionHeader title="Physical Rebalance" subtitle="Gentle mobility and recovery" />
        <WellnessCard
          title="Restorative Yoga & Posture"
          subtitle="Gentle spinal alignment to relieve tension caused by prolonged sitting"
          duration="15 min"
          icon="body"
          accentColor={colors.yogaAccent}
          bgColor={colors.yogaBg}
          onPress={() => router.push('/yoga-breathing')}
        />
        <WellnessCard
          title="Progressive Muscle Relaxation"
          subtitle="Systematic tension release to normalize sympathetic nerve arousal"
          duration="10 min"
          icon="bed"
          accentColor="#8B5CF6"
          bgColor="#F5F3FF"
          onPress={() => router.push('/yoga-breathing')}
        />

        <SectionHeader title="Lifestyle & Nutrition" subtitle="Holistic daily wellness" />
        <WellnessCard
          title="Food & Nutrition Portal"
          subtitle="Balanced anti-inflammatory nutritional habits and hydration tracking"
          icon="restaurant"
          accentColor={colors.nutritionAccent}
          bgColor={colors.nutritionBg}
          onPress={() => router.push('/nutrition')}
        />
        <WellnessCard
          title="Professional Support Directory"
          subtitle="Connect with certified health counselors and wellness professionals"
          icon="people"
          accentColor="#E11D48"
          bgColor="#FFE4E6"
          onPress={() => router.push('/support')}
        />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollContent: {
    paddingHorizontal: spacing.gutter,
    paddingBottom: spacing.xxl,
  },
  screenTitle: {
    fontSize: typography.size.xxl,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
    marginTop: spacing.sm,
  },
  screenSubtitle: {
    fontSize: typography.size.xs,
    color: colors.textMuted,
    marginBottom: spacing.base,
  },
});
