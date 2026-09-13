/**
 * Food & Nutrition Screen
 * 
 * Holistic nutrition, hydration tracking, and anti-inflammatory diet guides.
 * Strictly avoids fabricating personalized calorie burn without real backend calculation.
 */
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, typography, radii, shadows } from '../src/theme';
import { SanjeevniCard } from '../src/components/common/SanjeevniCard';
import { SectionHeader } from '../src/components/common/SectionHeader';

export default function NutritionScreen() {
  const [waterGlasses, setWaterGlasses] = useState(0);

  const mealGuides = [
    {
      meal: 'Breakfast',
      suggestion: 'Oatmeal with walnuts, chia seeds, and fresh berries',
      tags: ['Complex Carbs', 'Omega-3', 'High Fiber'],
    },
    {
      meal: 'Lunch',
      suggestion: 'Quinoa bowl with steamed greens, avocado, and grilled tofu or chicken',
      tags: ['Lean Protein', 'Healthy Fats', 'Magnesium'],
    },
    {
      meal: 'Dinner',
      suggestion: 'Lentil soup or roasted salmon with sweet potato and broccoli',
      tags: ['Light Digestion', 'Zinc', 'B-Vitamins'],
    },
    {
      meal: 'Stress Recovery Snacks',
      suggestion: 'Dark chocolate (>70%), raw almonds, or chamomile infusion',
      tags: ['Flavonoids', 'Anti-Oxidant', 'Tryptophan'],
    },
  ];

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Hydration Tracker */}
      <SectionHeader title="Hydration Balance" subtitle="Essential for blood volume & autonomic tone" />
      <SanjeevniCard style={styles.hydrationCard} floating>
        <View style={styles.hydrationTop}>
          <View style={styles.waterBadge}>
            <Ionicons name="water" size={24} color="#0284C7" />
          </View>
          <View style={styles.hydrationText}>
            <Text style={styles.hydrationCount}>{waterGlasses} / 8 Glasses</Text>
            <Text style={styles.hydrationSubtitle}>
              {waterGlasses > 0
                ? `~${waterGlasses * 250} ml consumed today`
                : 'No hydration logged today'}
            </Text>
          </View>
        </View>

        <View style={styles.waterButtonsRow}>
          <TouchableOpacity
            activeOpacity={0.8}
            onPress={() => setWaterGlasses((prev) => Math.max(0, prev - 1))}
            style={styles.waterBtn}
          >
            <Ionicons name="remove" size={18} color={colors.primary} />
          </TouchableOpacity>
          <TouchableOpacity
            activeOpacity={0.8}
            onPress={() => setWaterGlasses((prev) => Math.min(16, prev + 1))}
            style={[styles.waterBtn, styles.waterBtnAdd]}
          >
            <Ionicons name="add" size={18} color={colors.textOnPrimary} />
          </TouchableOpacity>
        </View>
      </SanjeevniCard>

      {/* Recommended Nutritional Protocol */}
      <SectionHeader
        title="Anti-Inflammatory Meal Guides"
        subtitle="Nutritional support to modulate sympathetic stress"
      />

      {mealGuides.map((m, idx) => (
        <SanjeevniCard key={idx} style={styles.mealCard}>
          <View style={styles.mealHeader}>
            <Text style={styles.mealTitle}>{m.meal}</Text>
            <Ionicons name="restaurant-outline" size={16} color={colors.primary} />
          </View>
          <Text style={styles.mealSuggestion}>{m.suggestion}</Text>
          <View style={styles.tagRow}>
            {m.tags.map((tag, tIdx) => (
              <View key={tIdx} style={styles.tagPill}>
                <Text style={styles.tagText}>{tag}</Text>
              </View>
            ))}
          </View>
        </SanjeevniCard>
      ))}

      {/* Honest Tracking Notice */}
      <View style={styles.noticeBox}>
        <Ionicons name="sparkles-outline" size={16} color={colors.textMuted} />
        <Text style={styles.noticeText}>
          Personalized metabolic calorie calculations will integrate once continuous
          active energy expenditure telemetry is validated by your wearable.
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
  hydrationCard: {
    padding: spacing.base,
    marginBottom: spacing.md,
  },
  hydrationTop: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  waterBadge: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#E0F2FE',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  hydrationText: {
    flex: 1,
  },
  hydrationCount: {
    fontSize: typography.size.lg,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  hydrationSubtitle: {
    fontSize: typography.size.xs,
    color: colors.textMuted,
    marginTop: 2,
  },
  waterButtonsRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    borderTopWidth: 1,
    borderTopColor: colors.borderSubtle,
    paddingTop: spacing.sm,
  },
  waterBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 1.5,
    borderColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: spacing.sm,
  },
  waterBtnAdd: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  mealCard: {
    marginVertical: spacing.xs,
    padding: spacing.base,
  },
  mealHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  mealTitle: {
    fontSize: typography.size.base,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  mealSuggestion: {
    fontSize: typography.size.sm,
    color: colors.textSecondary,
    lineHeight: 18,
    marginBottom: spacing.sm,
  },
  tagRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  tagPill: {
    backgroundColor: colors.primaryTint,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radii.pill,
    marginRight: 6,
    marginBottom: 4,
  },
  tagText: {
    fontSize: 10,
    fontWeight: typography.weight.semibold,
    color: colors.primaryDark,
  },
  noticeBox: {
    flexDirection: 'row',
    backgroundColor: colors.surfaceMuted,
    borderRadius: radii.card,
    padding: spacing.md,
    marginTop: spacing.lg,
  },
  noticeText: {
    flex: 1,
    fontSize: 11,
    color: colors.textMuted,
    marginLeft: spacing.sm,
    lineHeight: 16,
  },
});
