/**
 * Consult Screen (Professional Support & Telehealth Demo)
 * 
 * Provides a polished demonstration of professional support features.
 * Clearly labeled as Demo Professionals with zero fabricated online states,
 * zero fake patient reviews, and zero fake availability claims.
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { colors, spacing, typography, radii, shadows } from '../../src/theme';
import { SanjeevniCard } from '../../src/components/common/SanjeevniCard';
import { SectionHeader } from '../../src/components/common/SectionHeader';
import { DEMO_PROFESSIONALS } from '../../src/data/demoProfessionals';

export default function ConsultScreen() {
  const router = useRouter();
  const [activeCategory, setActiveCategory] = useState<'All' | 'Ayurveda' | 'Homeopathy'>('All');

  const filteredProfessionals = DEMO_PROFESSIONALS.filter((p) => {
    if (activeCategory === 'All') return true;
    return p.category === activeCategory;
  });

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.screenTitle}>Professional Support</Text>
        <Text style={styles.screenSubtitle}>
          Connect with a wellness professional when you need additional support.
        </Text>

        {/* Primary Action Cards */}
        <SectionHeader
          title="Consultation Options"
          subtitle="Choose how you would like to connect"
        />

        {/* 1. Voice Consultation Action Card */}
        <SanjeevniCard style={styles.actionCard}>
          <View style={styles.actionCardTop}>
            <View style={[styles.iconCircle, { backgroundColor: '#E0F2FE' }]}>
              <Ionicons name="mic-outline" size={24} color="#0284C7" />
            </View>
            <View style={styles.actionTextContent}>
              <Text style={styles.actionTitle}>Voice Consultation</Text>
              <Text style={styles.actionDescription}>Talk to a wellness professional</Text>
            </View>
          </View>
          <TouchableOpacity
            style={styles.actionCtaBtn}
            activeOpacity={0.8}
            onPress={() => router.push('/consult-voice' as any)}
          >
            <Text style={styles.actionCtaText}>Start Voice Consultation</Text>
            <Ionicons name="arrow-forward" size={16} color="#FFFFFF" />
          </TouchableOpacity>
        </SanjeevniCard>

        {/* 2. Chat Consultation Action Card */}
        <SanjeevniCard style={styles.actionCard}>
          <View style={styles.actionCardTop}>
            <View style={[styles.iconCircle, { backgroundColor: '#CCFBF1' }]}>
              <Ionicons name="chatbubbles-outline" size={24} color="#0D9488" />
            </View>
            <View style={styles.actionTextContent}>
              <Text style={styles.actionTitle}>Chat Consultation</Text>
              <Text style={styles.actionDescription}>
                Have a private consultation conversation
              </Text>
            </View>
          </View>
          <TouchableOpacity
            style={[styles.actionCtaBtn, { backgroundColor: '#0D9488' }]}
            activeOpacity={0.8}
            onPress={() => router.push('/consult-chat' as any)}
          >
            <Text style={styles.actionCtaText}>Start Chat</Text>
            <Ionicons name="arrow-forward" size={16} color="#FFFFFF" />
          </TouchableOpacity>
        </SanjeevniCard>

        {/* 3. Submit a Problem Action Card */}
        <SanjeevniCard style={styles.actionCard}>
          <View style={styles.actionCardTop}>
            <View style={[styles.iconCircle, { backgroundColor: '#F3E8FF' }]}>
              <Ionicons name="document-text-outline" size={24} color="#7C3AED" />
            </View>
            <View style={styles.actionTextContent}>
              <Text style={styles.actionTitle}>Submit a Problem</Text>
              <Text style={styles.actionDescription}>
                Describe your concern and request professional support
              </Text>
            </View>
          </View>
          <TouchableOpacity
            style={[styles.actionCtaBtn, { backgroundColor: '#7C3AED' }]}
            activeOpacity={0.8}
            onPress={() => router.push('/consult-submit-problem' as any)}
          >
            <Text style={styles.actionCtaText}>Submit a Problem</Text>
            <Ionicons name="arrow-forward" size={16} color="#FFFFFF" />
          </TouchableOpacity>
        </SanjeevniCard>

        {/* Demo Professionals Section */}
        <View style={styles.sectionHeaderRow}>
          <View>
            <Text style={styles.sectionTitleText}>Demo Professionals</Text>
            <Text style={styles.demoLabelSub}>Sample profiles for demonstration</Text>
          </View>
        </View>

        {/* Category Filter Chips */}
        <View style={styles.categoryRow}>
          {(['All', 'Ayurveda', 'Homeopathy'] as const).map((cat) => (
            <TouchableOpacity
              key={cat}
              activeOpacity={0.8}
              onPress={() => setActiveCategory(cat)}
              style={[
                styles.categoryChip,
                activeCategory === cat && styles.categoryChipActive,
              ]}
            >
              <Text
                style={[
                  styles.categoryChipText,
                  activeCategory === cat && styles.categoryChipTextActive,
                ]}
              >
                {cat}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Demo Professional Cards */}
        {filteredProfessionals.map((prof) => (
          <TouchableOpacity
            key={prof.id}
            activeOpacity={0.9}
            onPress={() => router.push({ pathname: '/consult-detail', params: { id: prof.id } } as any)}
          >
            <SanjeevniCard style={styles.profCard}>
              <View style={styles.profHeaderRow}>
                <View style={styles.avatarCircle}>
                  <Ionicons name="person-outline" size={24} color={colors.primary} />
                </View>
                <View style={styles.profInfo}>
                  <View style={styles.nameRow}>
                    <Text style={styles.profName}>{prof.name}</Text>
                    <View style={styles.demoBadge}>
                      <Text style={styles.demoBadgeText}>Demo Profile</Text>
                    </View>
                  </View>
                  <Text style={styles.profSpec}>{prof.specialization}</Text>
                  <View style={styles.catTag}>
                    <Text style={styles.catTagText}>{prof.category}</Text>
                  </View>
                </View>
              </View>

              <Text style={styles.profBio} numberOfLines={2}>
                {prof.bio}
              </Text>

              {/* Action buttons */}
              <View style={styles.profActionsRow}>
                <TouchableOpacity
                  style={styles.profActionBtnOutline}
                  activeOpacity={0.8}
                  onPress={() => router.push({ pathname: '/consult-chat', params: { id: prof.id } } as any)}
                >
                  <Ionicons name="chatbubble-outline" size={14} color={colors.primary} />
                  <Text style={styles.profActionBtnOutlineText}>Chat</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.profActionBtnPrimary}
                  activeOpacity={0.8}
                  onPress={() => router.push({ pathname: '/consult-voice', params: { id: prof.id } } as any)}
                >
                  <Ionicons name="call-outline" size={14} color="#FFFFFF" />
                  <Text style={styles.profActionBtnPrimaryText}>Voice</Text>
                </TouchableOpacity>
              </View>
            </SanjeevniCard>
          </TouchableOpacity>
        ))}

        {/* Clinical Disclaimer */}
        <View style={styles.noticeBox}>
          <Ionicons name="information-circle-outline" size={16} color={colors.textMuted} />
          <Text style={styles.noticeText}>
            Sanjeevni provides autonomic wellness monitoring only. Professional consultation experiences above are sample profiles for demonstration. In an acute emergency, please contact local emergency healthcare services immediately.
          </Text>
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
  actionCard: {
    marginVertical: spacing.xs,
    padding: spacing.base,
  },
  actionCardTop: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  iconCircle: {
    width: 46,
    height: 46,
    borderRadius: radii.md,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  actionTextContent: {
    flex: 1,
  },
  actionTitle: {
    fontSize: typography.size.base,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
    marginBottom: 2,
  },
  actionDescription: {
    fontSize: typography.size.xs,
    color: colors.textSecondary,
    lineHeight: 16,
  },
  actionCtaBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primary,
    paddingVertical: spacing.sm + 2,
    borderRadius: radii.md,
    marginTop: spacing.xs,
  },
  actionCtaText: {
    fontSize: typography.size.xs,
    fontWeight: typography.weight.bold,
    color: '#FFFFFF',
    marginRight: spacing.xs,
  },
  sectionHeaderRow: {
    marginTop: spacing.lg,
    marginBottom: spacing.xs,
  },
  sectionTitleText: {
    fontSize: typography.size.base,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  demoLabelSub: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 2,
  },
  categoryRow: {
    flexDirection: 'row',
    marginVertical: spacing.sm,
  },
  categoryChip: {
    paddingHorizontal: spacing.base,
    paddingVertical: spacing.xs + 2,
    borderRadius: radii.pill,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    marginRight: spacing.sm,
  },
  categoryChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  categoryChipText: {
    fontSize: typography.size.xs,
    fontWeight: typography.weight.semibold,
    color: colors.textSecondary,
  },
  categoryChipTextActive: {
    color: colors.textOnPrimary,
  },
  profCard: {
    marginVertical: spacing.xs,
    padding: spacing.base,
  },
  profHeaderRow: {
    flexDirection: 'row',
    marginBottom: spacing.xs,
  },
  avatarCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.primaryTint,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  profInfo: {
    flex: 1,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  profName: {
    fontSize: typography.size.base,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  demoBadge: {
    backgroundColor: colors.primaryTint,
    paddingHorizontal: spacing.xs + 2,
    paddingVertical: 2,
    borderRadius: radii.pill,
  },
  demoBadgeText: {
    fontSize: 9,
    fontWeight: typography.weight.bold,
    color: colors.primaryDark,
  },
  profSpec: {
    fontSize: typography.size.xs,
    color: colors.textSecondary,
    marginTop: 2,
  },
  catTag: {
    backgroundColor: colors.surfaceMuted,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radii.pill,
    alignSelf: 'flex-start',
    marginTop: 4,
  },
  catTagText: {
    fontSize: 10,
    fontWeight: typography.weight.semibold,
    color: colors.textMuted,
  },
  profBio: {
    fontSize: typography.size.xs,
    color: colors.textSecondary,
    lineHeight: 18,
    marginVertical: spacing.xs,
  },
  profActionsRow: {
    flexDirection: 'row',
    marginTop: spacing.xs,
  },
  profActionBtnOutline: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.primary,
    borderRadius: radii.md,
    paddingVertical: spacing.xs + 2,
    marginRight: spacing.xs,
  },
  profActionBtnOutlineText: {
    fontSize: typography.size.xs,
    fontWeight: typography.weight.bold,
    color: colors.primary,
    marginLeft: 4,
  },
  profActionBtnPrimary: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primary,
    borderRadius: radii.md,
    paddingVertical: spacing.xs + 2,
    marginLeft: spacing.xs,
  },
  profActionBtnPrimaryText: {
    fontSize: typography.size.xs,
    fontWeight: typography.weight.bold,
    color: '#FFFFFF',
    marginLeft: 4,
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
