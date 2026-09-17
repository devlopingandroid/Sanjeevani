/**
 * Problem Submission Screen (Demo Mode)
 * 
 * Form allowing user to describe concerns and request professional support.
 * Clearly displays honest demo post-submission feedback state.
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { colors, spacing, typography, radii, shadows } from '../src/theme';
import { SanjeevniCard } from '../src/components/common/SanjeevniCard';
import { PrimaryButton } from '../src/components/common/PrimaryButton';

export default function ConsultSubmitProblemScreen() {
  const router = useRouter();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [preferredType, setPreferredType] = useState<'Chat' | 'Voice'>('Chat');
  const [preferredTime, setPreferredTime] = useState('');

  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = () => {
    if (!title.trim() || !description.trim()) return;
    setIsSubmitted(true);
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['bottom']}>
      <KeyboardAvoidingView
        style={styles.keyboardContainer}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {isSubmitted ? (
            /* Post-Submission Demo Feedback State */
            <View style={styles.submittedContainer}>
              <View style={styles.submittedIconCircle}>
                <Ionicons name="checkmark-circle-outline" size={56} color={colors.primary} />
              </View>
              <Text style={styles.submittedTitle}>Request Saved for Demonstration</Text>
              <Text style={styles.submittedSubtitle}>
                Your concern details have been captured in demonstration mode.
              </Text>

              <SanjeevniCard style={styles.submittedNoticeCard}>
                <Ionicons name="information-circle-outline" size={20} color="#0284C7" />
                <Text style={styles.submittedNoticeText}>
                  Professional consultation services are not connected yet. Real clinical assignment will be enabled once backend providers are connected.
                </Text>
              </SanjeevniCard>

              <PrimaryButton
                title="Back to Consult"
                onPress={() => router.back()}
                style={styles.backBtn}
              />
            </View>
          ) : (
            /* Submission Form */
            <>
              <Text style={styles.formHeaderTitle}>Describe Your Concern</Text>
              <Text style={styles.formHeaderSubtitle}>
                Provide details about your wellness concern to request professional guidance.
              </Text>

              {/* Demo Notice Banner */}
              <View style={styles.demoNoticeBox}>
                <Ionicons name="flask-outline" size={16} color="#0369A1" />
                <Text style={styles.demoNoticeText}>
                  Demonstration form — requests are logged locally for UI testing.
                </Text>
              </View>

              <SanjeevniCard style={styles.formCard}>
                {/* 1. Concern Title */}
                <Text style={styles.label}>1. Concern Title *</Text>
                <TextInput
                  style={styles.textInput}
                  placeholder="e.g. Sleep disturbance & tension"
                  placeholderTextColor={colors.textMuted}
                  value={title}
                  onChangeText={setTitle}
                />

                {/* 2. Describe Your Concern */}
                <Text style={styles.label}>2. Describe Your Concern *</Text>
                <TextInput
                  style={[styles.textInput, styles.textArea]}
                  placeholder="Describe your symptoms, duration, or what you would like support with..."
                  placeholderTextColor={colors.textMuted}
                  value={description}
                  onChangeText={setDescription}
                  multiline
                  numberOfLines={5}
                />

                {/* 3. Preferred Consultation Type */}
                <Text style={styles.label}>3. Preferred Consultation Type</Text>
                <View style={styles.typeSelectorRow}>
                  {(['Chat', 'Voice'] as const).map((type) => (
                    <TouchableOpacity
                      key={type}
                      style={[
                        styles.typeChip,
                        preferredType === type && styles.typeChipActive,
                      ]}
                      activeOpacity={0.8}
                      onPress={() => setPreferredType(type)}
                    >
                      <Ionicons
                        name={type === 'Chat' ? 'chatbubbles-outline' : 'mic-outline'}
                        size={16}
                        color={preferredType === type ? '#FFFFFF' : colors.textSecondary}
                      />
                      <Text
                        style={[
                          styles.typeChipText,
                          preferredType === type && styles.typeChipTextActive,
                        ]}
                      >
                        {type} Consultation
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>

                {/* 4. Optional Preferred Time */}
                <Text style={styles.label}>4. Preferred Time (Optional)</Text>
                <TextInput
                  style={styles.textInput}
                  placeholder="e.g. Weekdays after 5:00 PM"
                  placeholderTextColor={colors.textMuted}
                  value={preferredTime}
                  onChangeText={setPreferredTime}
                />

                {/* Submit CTA */}
                <PrimaryButton
                  title="Submit Request"
                  onPress={handleSubmit}
                  disabled={!title.trim() || !description.trim()}
                  style={styles.submitBtn}
                  icon={<Ionicons name="paper-plane-outline" size={18} color="#FFFFFF" />}
                />
              </SanjeevniCard>
            </>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  keyboardContainer: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: spacing.gutter,
    paddingVertical: spacing.md,
    paddingBottom: spacing.xxl,
  },
  formHeaderTitle: {
    fontSize: typography.size.lg,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  formHeaderSubtitle: {
    fontSize: typography.size.xs,
    color: colors.textMuted,
    marginTop: 2,
    marginBottom: spacing.sm,
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
    color: '#0369A1',
    marginLeft: spacing.xs,
  },
  formCard: {
    padding: spacing.base,
  },
  label: {
    fontSize: typography.size.xs + 1,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
    marginTop: spacing.sm,
    marginBottom: spacing.xs,
  },
  textInput: {
    backgroundColor: colors.surfaceMuted,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    fontSize: typography.size.xs + 1,
    color: colors.textPrimary,
  },
  textArea: {
    height: 110,
    textAlignVertical: 'top',
  },
  typeSelectorRow: {
    flexDirection: 'row',
    marginVertical: spacing.xs,
  },
  typeChip: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surfaceMuted,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.md,
    paddingVertical: spacing.sm,
    marginRight: spacing.xs,
  },
  typeChipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  typeChipText: {
    fontSize: typography.size.xs,
    fontWeight: typography.weight.semibold,
    color: colors.textSecondary,
    marginLeft: 6,
  },
  typeChipTextActive: {
    color: '#FFFFFF',
  },
  submitBtn: {
    marginTop: spacing.lg,
  },
  submittedContainer: {
    alignItems: 'center',
    paddingVertical: spacing.xl,
  },
  submittedIconCircle: {
    width: 88,
    height: 88,
    borderRadius: 44,
    backgroundColor: colors.primaryTint,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  submittedTitle: {
    fontSize: typography.size.lg,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
    textAlign: 'center',
  },
  submittedSubtitle: {
    fontSize: typography.size.xs,
    color: colors.textSecondary,
    textAlign: 'center',
    marginTop: 4,
    marginBottom: spacing.lg,
  },
  submittedNoticeCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E0F2FE',
    borderWidth: 1,
    borderColor: '#BAE6FD',
    padding: spacing.base,
    marginBottom: spacing.xl,
  },
  submittedNoticeText: {
    flex: 1,
    fontSize: 12,
    color: '#0369A1',
    marginLeft: spacing.sm,
    lineHeight: 18,
  },
  backBtn: {
    width: '100%',
  },
});
