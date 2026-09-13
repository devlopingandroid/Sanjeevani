/**
 * Professional Detail Screen (Demo Mode)
 * 
 * Displays sample professional profile, specialization, and consultation options.
 * Clearly labeled with "Demo Professional" and honest demo mode notice.
 */
import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { colors, spacing, typography, radii, shadows } from '../src/theme';
import { SanjeevniCard } from '../src/components/common/SanjeevniCard';
import { SectionHeader } from '../src/components/common/SectionHeader';
import { PrimaryButton } from '../src/components/common/PrimaryButton';
import { getDemoProfessionalById } from '../src/data/demoProfessionals';

export default function ConsultDetailScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id?: string }>();
  const professional = getDemoProfessionalById(id);

  return (
    <SafeAreaView style={styles.safeArea} edges={['bottom']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Header Profile Card */}
        <SanjeevniCard style={styles.headerCard}>
          <View style={styles.avatarLarge}>
            <Ionicons name="person-outline" size={40} color={colors.primary} />
          </View>
          <Text style={styles.profName}>{professional.name}</Text>
          <Text style={styles.profSpec}>{professional.specialization}</Text>

          <View style={styles.badgeRow}>
            <View style={styles.demoBadge}>
              <Ionicons name="flask-outline" size={12} color={colors.primaryDark} />
              <Text style={styles.demoBadgeText}>Demo Professional</Text>
            </View>
            <View style={styles.categoryBadge}>
              <Text style={styles.categoryBadgeText}>{professional.category}</Text>
            </View>
          </View>
        </SanjeevniCard>

        {/* Demo Notice Banner */}
        <View style={styles.demoNoticeBox}>
          <Ionicons name="information-circle" size={18} color="#0284C7" />
          <Text style={styles.demoNoticeText}>
            Demo mode — real professional connection is not configured yet.
          </Text>
        </View>

        {/* About Section */}
        <SectionHeader
          title="About"
          subtitle="Professional background & specialization"
        />
        <SanjeevniCard style={styles.sectionCard}>
          <Text style={styles.bioText}>{professional.bio}</Text>
        </SanjeevniCard>

        {/* Consultation Options Section */}
        <SectionHeader
          title="Consultation Options"
          subtitle="Select your preferred mode of interaction"
        />

        <SanjeevniCard style={styles.sectionCard}>
          <TouchableOpacity
            style={styles.optionRow}
            activeOpacity={0.8}
            onPress={() => router.push({ pathname: '/consult-chat', params: { id: professional.id } } as any)}
          >
            <View style={[styles.optionIcon, { backgroundColor: '#CCFBF1' }]}>
              <Ionicons name="chatbubbles-outline" size={22} color="#0D9488" />
            </View>
            <View style={styles.optionTextContent}>
              <Text style={styles.optionTitle}>Chat Consultation</Text>
              <Text style={styles.optionSubtitle}>Private text-based consultation</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
          </TouchableOpacity>

          <View style={styles.divider} />

          <TouchableOpacity
            style={styles.optionRow}
            activeOpacity={0.8}
            onPress={() => router.push({ pathname: '/consult-voice', params: { id: professional.id } } as any)}
          >
            <View style={[styles.optionIcon, { backgroundColor: '#E0F2FE' }]}>
              <Ionicons name="mic-outline" size={22} color="#0284C7" />
            </View>
            <View style={styles.optionTextContent}>
              <Text style={styles.optionTitle}>Voice Consultation</Text>
              <Text style={styles.optionSubtitle}>Direct audio conversation demo</Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={colors.textMuted} />
          </TouchableOpacity>
        </SanjeevniCard>

        {/* Action Buttons */}
        <View style={styles.ctaContainer}>
          <PrimaryButton
            title="Start Chat Consultation"
            onPress={() => router.push({ pathname: '/consult-chat', params: { id: professional.id } } as any)}
            style={styles.ctaBtn}
            icon={<Ionicons name="chatbubbles" size={18} color="#FFFFFF" />}
          />
          <PrimaryButton
            title="Start Voice Consultation"
            onPress={() => router.push({ pathname: '/consult-voice', params: { id: professional.id } } as any)}
            variant="outline"
            style={styles.ctaBtnSecondary}
            icon={<Ionicons name="mic" size={18} color={colors.primary} />}
          />
        </View>
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
    paddingVertical: spacing.md,
    paddingBottom: spacing.xxl,
  },
  headerCard: {
    alignItems: 'center',
    paddingVertical: spacing.lg,
    marginBottom: spacing.md,
  },
  avatarLarge: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.primaryTint,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  profName: {
    fontSize: typography.size.lg,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  profSpec: {
    fontSize: typography.size.xs,
    color: colors.textSecondary,
    marginTop: 2,
    marginBottom: spacing.xs,
  },
  badgeRow: {
    flexDirection: 'row',
    marginTop: spacing.xs,
  },
  demoBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primaryTint,
    paddingHorizontal: spacing.sm,
    paddingVertical: 3,
    borderRadius: radii.pill,
    marginRight: spacing.xs,
  },
  demoBadgeText: {
    fontSize: 10,
    fontWeight: typography.weight.bold,
    color: colors.primaryDark,
    marginLeft: 4,
  },
  categoryBadge: {
    backgroundColor: colors.surfaceMuted,
    paddingHorizontal: spacing.sm,
    paddingVertical: 3,
    borderRadius: radii.pill,
  },
  categoryBadgeText: {
    fontSize: 10,
    fontWeight: typography.weight.semibold,
    color: colors.textMuted,
  },
  demoNoticeBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E0F2FE',
    borderWidth: 1,
    borderColor: '#BAE6FD',
    borderRadius: radii.card,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  demoNoticeText: {
    flex: 1,
    fontSize: 12,
    fontWeight: typography.weight.medium,
    color: '#0369A1',
    marginLeft: spacing.xs,
    lineHeight: 16,
  },
  sectionCard: {
    padding: spacing.base,
    marginBottom: spacing.md,
  },
  bioText: {
    fontSize: typography.size.xs,
    color: colors.textSecondary,
    lineHeight: 20,
  },
  optionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.xs,
  },
  optionIcon: {
    width: 40,
    height: 40,
    borderRadius: radii.md,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  optionTextContent: {
    flex: 1,
  },
  optionTitle: {
    fontSize: typography.size.sm,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  optionSubtitle: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 2,
  },
  divider: {
    height: 1,
    backgroundColor: colors.borderSubtle,
    marginVertical: spacing.xs,
  },
  ctaContainer: {
    marginTop: spacing.md,
  },
  ctaBtn: {
    marginBottom: spacing.sm,
  },
  ctaBtnSecondary: {},
});
