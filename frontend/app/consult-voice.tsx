/**
 * Voice Consultation Screen (Demo Mode)
 * 
 * Displays call preparation interface with controls and honest status state.
 * Strictly avoids fake "connected", "duration", or "professional joined" indicators.
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { colors, spacing, typography, radii, shadows } from '../src/theme';
import { SanjeevniCard } from '../src/components/common/SanjeevniCard';
import { PrimaryButton } from '../src/components/common/PrimaryButton';
import { getDemoProfessionalById } from '../src/data/demoProfessionals';

export default function ConsultVoiceScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id?: string }>();
  const professional = getDemoProfessionalById(id);

  const [isMuted, setIsMuted] = useState(false);
  const [isSpeakerOn, setIsSpeakerOn] = useState(false);

  return (
    <SafeAreaView style={styles.safeArea} edges={['bottom']}>
      <View style={styles.container}>
        {/* Top Badge */}
        <View style={styles.topBadgeRow}>
          <View style={styles.demoBadge}>
            <Ionicons name="flask-outline" size={12} color={colors.primaryDark} />
            <Text style={styles.demoBadgeText}>Demo Consultation</Text>
          </View>
        </View>

        {/* Professional Profile Placeholder */}
        <View style={styles.profileSection}>
          <View style={styles.avatarCircleLarge}>
            <Ionicons name="person-outline" size={56} color={colors.primary} />
          </View>
          <Text style={styles.profName}>{professional.name}</Text>
          <Text style={styles.profSpec}>{professional.specialization}</Text>

          {/* Honest Unconnected Status Notice */}
          <View style={styles.statusBox}>
            <Ionicons name="cloud-offline-outline" size={20} color="#0284C7" />
            <Text style={styles.statusText}>Voice calling is not connected yet.</Text>
          </View>
        </View>

        {/* Audio Controls */}
        <SanjeevniCard style={styles.controlsCard}>
          <Text style={styles.controlsLabel}>Audio Controls (Demo)</Text>

          <View style={styles.controlsRow}>
            {/* Mute Toggle */}
            <TouchableOpacity
              style={[styles.controlBtn, isMuted && styles.controlBtnActive]}
              activeOpacity={0.8}
              onPress={() => setIsMuted(!isMuted)}
            >
              <Ionicons
                name={isMuted ? 'mic-off' : 'mic'}
                size={24}
                color={isMuted ? '#FFFFFF' : colors.primary}
              />
              <Text style={[styles.controlBtnText, isMuted && styles.controlBtnTextActive]}>
                {isMuted ? 'Muted' : 'Mute'}
              </Text>
            </TouchableOpacity>

            {/* Speaker Toggle */}
            <TouchableOpacity
              style={[styles.controlBtn, isSpeakerOn && styles.controlBtnActive]}
              activeOpacity={0.8}
              onPress={() => setIsSpeakerOn(!isSpeakerOn)}
            >
              <Ionicons
                name={isSpeakerOn ? 'volume-high' : 'volume-medium-outline'}
                size={24}
                color={isSpeakerOn ? '#FFFFFF' : colors.primary}
              />
              <Text style={[styles.controlBtnText, isSpeakerOn && styles.controlBtnTextActive]}>
                {isSpeakerOn ? 'Speaker On' : 'Speaker'}
              </Text>
            </TouchableOpacity>

            {/* End Call Button */}
            <TouchableOpacity
              style={styles.endCallBtn}
              activeOpacity={0.8}
              onPress={() => router.back()}
            >
              <Ionicons name="call" size={24} color="#FFFFFF" style={{ transform: [{ rotate: '135deg' }] }} />
              <Text style={styles.endCallBtnText}>End</Text>
            </TouchableOpacity>
          </View>
        </SanjeevniCard>

        {/* Back to Consult Button */}
        <View style={styles.bottomCtaContainer}>
          <PrimaryButton
            title="Back to Consult"
            onPress={() => router.back()}
            variant="outline"
          />
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  container: {
    flex: 1,
    paddingHorizontal: spacing.gutter,
    paddingVertical: spacing.md,
    justifyContent: 'space-between',
  },
  topBadgeRow: {
    alignItems: 'center',
    marginTop: spacing.xs,
  },
  demoBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primaryTint,
    paddingHorizontal: spacing.md,
    paddingVertical: 4,
    borderRadius: radii.pill,
  },
  demoBadgeText: {
    fontSize: 11,
    fontWeight: typography.weight.bold,
    color: colors.primaryDark,
    marginLeft: 4,
  },
  profileSection: {
    alignItems: 'center',
    marginVertical: spacing.xl,
  },
  avatarCircleLarge: {
    width: 110,
    height: 110,
    borderRadius: 55,
    backgroundColor: colors.primaryTint,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.base,
    borderWidth: 3,
    borderColor: colors.primary,
  },
  profName: {
    fontSize: typography.size.xl,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  profSpec: {
    fontSize: typography.size.xs,
    color: colors.textSecondary,
    marginTop: 4,
  },
  statusBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E0F2FE',
    borderWidth: 1,
    borderColor: '#BAE6FD',
    borderRadius: radii.card,
    paddingHorizontal: spacing.base,
    paddingVertical: spacing.sm,
    marginTop: spacing.lg,
  },
  statusText: {
    fontSize: typography.size.xs,
    fontWeight: typography.weight.semibold,
    color: '#0369A1',
    marginLeft: spacing.xs,
  },
  controlsCard: {
    padding: spacing.base,
    alignItems: 'center',
  },
  controlsLabel: {
    fontSize: typography.size.xs,
    fontWeight: typography.weight.bold,
    color: colors.textMuted,
    marginBottom: spacing.md,
  },
  controlsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    width: '100%',
  },
  controlBtn: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: colors.surfaceMuted,
    borderWidth: 1,
    borderColor: colors.border,
  },
  controlBtnActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  controlBtnText: {
    fontSize: 10,
    fontWeight: typography.weight.semibold,
    color: colors.textSecondary,
    marginTop: 4,
  },
  controlBtnTextActive: {
    color: '#FFFFFF',
  },
  endCallBtn: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#DC2626',
  },
  endCallBtnText: {
    fontSize: 10,
    fontWeight: typography.weight.bold,
    color: '#FFFFFF',
    marginTop: 4,
  },
  bottomCtaContainer: {
    marginBottom: spacing.sm,
  },
});
