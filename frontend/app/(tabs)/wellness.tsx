/**
 * Wellness Screen
 * 
 * Holistic body and mind recovery portal.
 * Features a prominent "Yoga & Wellness" section with informational
 * yoga postures (Child's Pose, Cat-Cow, Tree Pose, etc.) alongside
 * autonomic regulation breathing exercises and nutritional guidance.
 * 
 * Strictly zero fake data: all informational wellness activities are educational.
 */
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, typography, radii, shadows } from '../../src/theme';
import { SanjeevniCard } from '../../src/components/common/SanjeevniCard';
import { SectionHeader } from '../../src/components/common/SectionHeader';
import { WellnessCard } from '../../src/components/wellness/WellnessCard';

interface YogaAsana {
  title: string;
  sanskrit: string;
  category: string;
  duration: string;
  difficulty: 'Gentle' | 'Moderate' | 'Restorative';
  description: string;
  benefits: string;
  icon: keyof typeof Ionicons.glyphMap;
  color: string;
  bg: string;
}

export default function WellnessScreen() {
  const router = useRouter();
  const [selectedFilter, setSelectedFilter] = useState<'All' | 'Restorative' | 'Breathing' | 'Mobility'>('All');

  const yogaAsanas: YogaAsana[] = [
    {
      title: "Child's Pose",
      sanskrit: 'Balasana',
      category: 'Restorative',
      duration: '3–5 min',
      difficulty: 'Restorative',
      description: 'Gently elongates the spine, relaxes hips, and signals parasympathetic calming.',
      benefits: 'Calms adrenal sympathetic response & relieves spinal pressure',
      icon: 'body',
      color: colors.yogaAccent,
      bg: colors.yogaBg,
    },
    {
      title: 'Cat-Cow Flow',
      sanskrit: 'Marjaryasana-Bitilasana',
      category: 'Mobility',
      duration: '5 min',
      difficulty: 'Gentle',
      description: 'Synchronized spinal flexion and extension linked to rhythmic inhalation and exhalation.',
      benefits: 'Stimulates vagus nerve & releases cervical neck tension',
      icon: 'sync-outline',
      color: '#0284C7',
      bg: '#E0F2FE',
    },
    {
      title: 'Tree Pose',
      sanskrit: 'Vrikshasana',
      category: 'Mobility',
      duration: '3 min',
      difficulty: 'Moderate',
      description: 'Standing balance posture fostering proprioceptive focus and mental grounding.',
      benefits: 'Enhances cognitive equilibrium & neuromuscular control',
      icon: 'fitness-outline',
      color: '#059669',
      bg: '#D1FAE5',
    },
    {
      title: 'Legs-Up-The-Wall',
      sanskrit: 'Viparita Karani',
      category: 'Restorative',
      duration: '5–10 min',
      difficulty: 'Restorative',
      description: 'Passive inverted posture enhancing venous return to the heart and autonomic relaxation.',
      benefits: 'Lowers systemic blood pressure & eases adrenal fatigue',
      icon: 'bed-outline',
      color: '#8B5CF6',
      bg: '#F5F3FF',
    },
    {
      title: 'Corpse Pose',
      sanskrit: 'Savasana',
      category: 'Restorative',
      duration: '5–10 min',
      difficulty: 'Restorative',
      description: 'Total neuromuscular release, resting awareness on subtle diaphragmatic breaths.',
      benefits: 'Full parasympathetic reset & autonomic nervous recovery',
      icon: 'moon-outline',
      color: '#6366F1',
      bg: '#EEF2FF',
    },
  ];

  const filteredAsanas = yogaAsanas.filter((item) => {
    if (selectedFilter === 'All') return true;
    if (selectedFilter === 'Restorative') return item.difficulty === 'Restorative';
    if (selectedFilter === 'Mobility') return item.category === 'Mobility';
    return true;
  });

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.screenTitle}>Wellness & Recovery</Text>
        <Text style={styles.screenSubtitle}>Holistic body and mind restoration routines</Text>

        {/* PROMINENT SECTION: Yoga & Wellness */}
        <SectionHeader
          title="Yoga & Postures"
          subtitle="Restorative asanas to balance somatic stress"
          actionText="Practice Timer →"
          onActionPress={() => router.push('/yoga-breathing')}
        />

        {/* Filter Chips */}
        <View style={styles.filterRow}>
          {(['All', 'Restorative', 'Mobility'] as const).map((filter) => (
            <TouchableOpacity
              key={filter}
              activeOpacity={0.8}
              onPress={() => setSelectedFilter(filter)}
              style={[
                styles.filterChip,
                selectedFilter === filter && styles.filterChipActive,
              ]}
            >
              <Text
                style={[
                  styles.filterChipText,
                  selectedFilter === filter && styles.filterChipTextActive,
                ]}
              >
                {filter}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Prominent Yoga Posture Cards */}
        {filteredAsanas.map((asana, idx) => (
          <TouchableOpacity
            key={idx}
            activeOpacity={0.85}
            onPress={() => router.push('/yoga-breathing')}
            style={[styles.yogaCard, shadows.card]}
          >
            <View style={[styles.yogaIconCircle, { backgroundColor: asana.bg }]}>
              <Ionicons name={asana.icon} size={24} color={asana.color} />
            </View>
            <View style={styles.yogaTextContainer}>
              <View style={styles.yogaHeaderRow}>
                <Text style={styles.yogaTitle}>{asana.title}</Text>
                <View style={styles.difficultyBadge}>
                  <Text style={styles.difficultyText}>{asana.difficulty}</Text>
                </View>
              </View>
              <Text style={styles.yogaSanskrit}>{asana.sanskrit} • {asana.duration}</Text>
              <Text style={styles.yogaDescription}>{asana.description}</Text>
              <View style={styles.benefitRow}>
                <Ionicons name="sparkles" size={12} color={colors.primary} />
                <Text style={styles.benefitText}>{asana.benefits}</Text>
              </View>
            </View>
            <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
          </TouchableOpacity>
        ))}

        {/* Breathing & Vagal Regulation */}
        <SectionHeader
          title="Autonomic Regulation"
          subtitle="Evidence-based paced respiration exercises"
        />
        <WellnessCard
          title="Diaphragmatic 4-7-8 Breathing"
          subtitle="Vagal nerve activation to reduce sympathetic tone & lower heart rate"
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

        {/* Lifestyle, Nutrition & Rest */}
        <SectionHeader
          title="Lifestyle & Nutrition"
          subtitle="Holistic support for cellular recovery"
        />
        <WellnessCard
          title="Food & Nutrition Protocol"
          subtitle="Anti-inflammatory dietary guides, magnesium recovery, and hydration tracking"
          icon="restaurant"
          accentColor={colors.nutritionAccent}
          bgColor={colors.nutritionBg}
          onPress={() => router.push('/nutrition')}
        />
        <WellnessCard
          title="Progressive Muscle Relaxation"
          subtitle="Systematic somatic release to normalize autonomic nerve arousal"
          duration="10 min"
          icon="bed"
          accentColor="#8B5CF6"
          bgColor="#F5F3FF"
          onPress={() => router.push('/yoga-breathing')}
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
  filterRow: {
    flexDirection: 'row',
    marginBottom: spacing.sm,
  },
  filterChip: {
    paddingHorizontal: spacing.base,
    paddingVertical: spacing.xs + 2,
    borderRadius: radii.pill,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    marginRight: spacing.sm,
  },
  filterChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  filterChipText: {
    fontSize: typography.size.xs,
    fontWeight: typography.weight.semibold,
    color: colors.textSecondary,
  },
  filterChipTextActive: {
    color: colors.textOnPrimary,
  },
  yogaCard: {
    backgroundColor: colors.surface,
    borderRadius: radii.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.base,
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: spacing.xs + 2,
  },
  yogaIconCircle: {
    width: 48,
    height: 48,
    borderRadius: radii.md,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  yogaTextContainer: {
    flex: 1,
    paddingRight: spacing.sm,
  },
  yogaHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 2,
  },
  yogaTitle: {
    fontSize: typography.size.base,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  difficultyBadge: {
    backgroundColor: colors.primaryTint,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radii.pill,
  },
  difficultyText: {
    fontSize: 10,
    fontWeight: typography.weight.semibold,
    color: colors.primaryDark,
  },
  yogaSanskrit: {
    fontSize: 11,
    color: colors.primaryDark,
    fontWeight: typography.weight.medium,
    marginBottom: 4,
  },
  yogaDescription: {
    fontSize: typography.size.xs,
    color: colors.textSecondary,
    lineHeight: 16,
    marginBottom: 4,
  },
  benefitRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 2,
  },
  benefitText: {
    fontSize: 10,
    color: colors.textMuted,
    marginLeft: 4,
    fontStyle: 'italic',
  },
});
