/**
 * Manual Model Testing Screen (DEVELOPMENT ONLY)
 * 
 * Allows manual input of the exact 26 physiological features required by
 * Sanjeevni_Best_Stress_Model.pkl for empirical model validation.
 * 
 * NO-MOCK-DATA & PRODUCTION ISOLATION ENFORCED:
 * - All fields initialize strictly to empty string ("").
 * - Does NOT create production sensor data or modify user stress history.
 * - Adheres strictly to Sanjeevni teal/white design system.
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { stressService } from '../../src/services/stressService';
import { ModelTestRequestPayload, ModelTestResponsePayload } from '../../src/api/types';
import { colors, spacing, typography, radii, shadows } from '../../src/theme';
import { SanjeevniCard } from '../../src/components/common/SanjeevniCard';
import { SectionHeader } from '../../src/components/common/SectionHeader';

interface FeatureFieldConfig {
  key: keyof ModelTestRequestPayload;
  label: string;
  unit: string;
  description: string;
}

interface FeatureSectionConfig {
  title: string;
  subtitle: string;
  icon: keyof typeof Ionicons.glyphMap;
  fields: FeatureFieldConfig[];
}

const FEATURE_SECTIONS: FeatureSectionConfig[] = [
  {
    title: 'SECTION 1: Electrodermal Activity (EDA)',
    subtitle: 'Galvanic skin response features derived from 30s window',
    icon: 'water-outline',
    fields: [
      { key: 'eda_mean', label: 'EDA Mean', unit: 'μS', description: 'Mean skin conductance level' },
      { key: 'eda_std', label: 'EDA Std', unit: 'μS', description: 'Standard deviation of skin conductance' },
      { key: 'eda_min', label: 'EDA Min', unit: 'μS', description: 'Minimum skin conductance' },
      { key: 'eda_max', label: 'EDA Max', unit: 'μS', description: 'Maximum skin conductance' },
      { key: 'eda_range', label: 'EDA Range', unit: 'μS', description: 'Peak-to-peak amplitude range (max - min)' },
      { key: 'eda_slope', label: 'EDA Slope', unit: 'μS/s', description: 'Linear trend slope d(EDA)/dt' },
    ],
  },
  {
    title: 'SECTION 2: Skin Conductance Response (SCR)',
    subtitle: 'Phasic skin conductance arousal response metrics',
    icon: 'pulse-outline',
    fields: [
      { key: 'scr_count', label: 'SCR Count', unit: 'count', description: 'Count of phasic SCR peaks' },
      { key: 'scr_mean', label: 'SCR Mean', unit: 'μS', description: 'Mean amplitude of detected phasic SCR peaks' },
    ],
  },
  {
    title: 'SECTION 3: Blood Volume Pulse (BVP)',
    subtitle: 'Optical photoplethysmography waveform characteristics',
    icon: 'heart-circle-outline',
    fields: [
      { key: 'bvp_mean', label: 'BVP Mean', unit: 'raw', description: 'Mean zero-centered bandpassed BVP' },
      { key: 'bvp_std', label: 'BVP Std', unit: 'raw', description: 'Standard deviation of BVP amplitude' },
      { key: 'bvp_min', label: 'BVP Min', unit: 'raw', description: 'Minimum BVP amplitude' },
      { key: 'bvp_max', label: 'BVP Max', unit: 'raw', description: 'Maximum BVP amplitude' },
      { key: 'bvp_range', label: 'BVP Range', unit: 'raw', description: 'BVP amplitude range' },
      { key: 'bvp_hr', label: 'BVP HR', unit: 'BPM', description: 'Heart rate derived from BVP systolic peaks' },
    ],
  },
  {
    title: 'SECTION 4: Heart Rate (HR)',
    subtitle: 'Autonomic cardiac frequency features',
    icon: 'fitness-outline',
    fields: [
      { key: 'hr_mean', label: 'HR Mean', unit: 'BPM', description: 'Mean heart rate across window' },
      { key: 'hr_std', label: 'HR Std', unit: 'BPM', description: 'Standard deviation of heart rate' },
      { key: 'hr_min', label: 'HR Min', unit: 'BPM', description: 'Minimum instantaneous heart rate' },
      { key: 'hr_max', label: 'HR Max', unit: 'BPM', description: 'Maximum instantaneous heart rate' },
    ],
  },
  {
    title: 'SECTION 5: Acceleration (ACC)',
    subtitle: '3D motion magnitude features',
    icon: 'move-outline',
    fields: [
      { key: 'acc_mean', label: 'Acc Mean', unit: 'mag', description: 'Mean 3D acceleration magnitude' },
      { key: 'acc_std', label: 'Acc Std', unit: 'mag', description: 'Standard deviation of acceleration' },
      { key: 'acc_min', label: 'Acc Min', unit: 'mag', description: 'Minimum 3D acceleration magnitude' },
      { key: 'acc_max', label: 'Acc Max', unit: 'mag', description: 'Maximum 3D acceleration magnitude' },
      { key: 'acc_range', label: 'Acc Range', unit: 'mag', description: 'Acceleration magnitude range' },
      { key: 'acc_rms', label: 'Acc RMS', unit: 'mag', description: 'Root Mean Square of 3D acceleration' },
    ],
  },
  {
    title: 'SECTION 6: Temperature (TEMP)',
    subtitle: 'Peripheral skin thermal dynamics',
    icon: 'thermometer-outline',
    fields: [
      { key: 'temp_mean', label: 'Temp Mean', unit: '°C', description: 'Mean peripheral skin temperature' },
      { key: 'temp_std', label: 'Temp Std', unit: '°C', description: 'Standard deviation of temperature' },
    ],
  },
];

export default function ManualModelTestScreen() {
  const router = useRouter();

  // All 26 feature inputs initialized strictly to empty string ("")
  const [inputs, setInputs] = useState<Record<string, string>>({
    eda_mean: '', eda_std: '', eda_min: '', eda_max: '', eda_range: '', eda_slope: '',
    scr_count: '', scr_mean: '',
    bvp_mean: '', bvp_std: '', bvp_min: '', bvp_max: '', bvp_range: '', bvp_hr: '',
    hr_mean: '', hr_std: '', hr_min: '', hr_max: '',
    acc_mean: '', acc_std: '', acc_min: '', acc_max: '', acc_range: '', acc_rms: '',
    temp_mean: '', temp_std: '',
  });

  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<ModelTestResponsePayload | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  const handleInputChange = (key: string, value: string) => {
    setInputs((prev) => ({ ...prev, [key]: value }));
    if (fieldErrors[key]) {
      setFieldErrors((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
    }
    if (apiError) setApiError(null);
  };

  const handleResetFields = () => {
    setInputs({
      eda_mean: '', eda_std: '', eda_min: '', eda_max: '', eda_range: '', eda_slope: '',
      scr_count: '', scr_mean: '',
      bvp_mean: '', bvp_std: '', bvp_min: '', bvp_max: '', bvp_range: '', bvp_hr: '',
      hr_mean: '', hr_std: '', hr_min: '', hr_max: '',
      acc_mean: '', acc_std: '', acc_min: '', acc_max: '', acc_range: '', acc_rms: '',
      temp_mean: '', temp_std: '',
    });
    setFieldErrors({});
    setTestResult(null);
    setApiError(null);
  };

  const handleRunModelTest = async () => {
    // 1. Input Validation
    const newErrors: Record<string, string> = {};
    const parsedPayload: Partial<ModelTestRequestPayload> = {};

    FEATURE_SECTIONS.forEach((section) => {
      section.fields.forEach((f) => {
        const rawVal = (inputs[f.key] || '').trim();
        if (rawVal === '') {
          newErrors[f.key] = 'Please enter a valid number.';
          return;
        }

        const num = Number(rawVal);
        if (isNaN(num) || !isFinite(num)) {
          newErrors[f.key] = 'Please enter a valid number.';
          return;
        }

        parsedPayload[f.key] = num;
      });
    });

    if (Object.keys(newErrors).length > 0) {
      setFieldErrors(newErrors);
      setApiError('Validation failed. Please correct all invalid or empty fields.');
      return;
    }

    setIsRunning(true);
    setApiError(null);
    setTestResult(null);

    try {
      const response = await stressService.runModelTest(parsedPayload as ModelTestRequestPayload);
      setTestResult(response);
    } catch (err: any) {
      console.error('[ManualModelTest] Execution failed:', err);
      const isUnavailable = err?.statusCode === 503 || err?.errorCode === 'MODEL_UNAVAILABLE';
      const msg = isUnavailable
        ? 'Stress prediction ML model is currently unavailable.'
        : (err?.message || 'Unable to execute manual model test. Please check backend connection.');
      setApiError(msg);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        {/* Top Header */}
        <View style={styles.header}>
          <TouchableOpacity
            onPress={() => router.back()}
            style={styles.backButton}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
          </TouchableOpacity>
          <View style={styles.headerTitleContainer}>
            <Text style={styles.headerTitle}>Manual Model Test</Text>
            <Text style={styles.headerSubtitle}>Development tool — enter model features manually</Text>
          </View>
          <View style={styles.devBadge}>
            <Text style={styles.devBadgeText}>DEV ONLY</Text>
          </View>
        </View>

        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* Top Banner Disclaimer */}
          <View style={styles.infoBanner}>
            <Ionicons name="flask-outline" size={20} color={colors.primaryDark} />
            <Text style={styles.infoBannerText}>
              This screen sends exact 26-column feature vectors directly to the loaded joblib ML model
              (Sanjeevni_Best_Stress_Model.pkl). It does NOT modify user stress history or production database records.
            </Text>
          </View>

          {apiError ? (
            <View style={styles.errorCard}>
              <Ionicons name="alert-circle" size={20} color="#DC2626" />
              <Text style={styles.errorCardText}>{apiError}</Text>
            </View>
          ) : null}

          {/* Results Card */}
          {testResult ? (
            <SanjeevniCard style={styles.resultCard}>
              <View style={styles.resultHeaderRow}>
                <View style={styles.resultTag}>
                  <Ionicons name="checkmark-circle" size={16} color={colors.primaryDark} />
                  <Text style={styles.resultTagText}>{testResult.status}</Text>
                </View>
                <Text style={styles.modelNameText}>{testResult.model_name}</Text>
              </View>

              <View style={styles.resultMainContainer}>
                <Text style={styles.resultLabel}>Model Classification</Text>
                <View
                  style={[
                    styles.predictionBadge,
                    testResult.stress_level === 'STRESS' ? styles.stressBadge : styles.baselineBadge,
                  ]}
                >
                  <Text style={styles.predictionBadgeText}>
                    {testResult.stress_level === 'STRESS'
                      ? 'STRESS (Class 1)'
                      : 'BASELINE (Class 0)'}
                  </Text>
                </View>

                <View style={styles.metricsGrid}>
                  <View style={styles.metricItem}>
                    <Text style={styles.metricTitle}>Stress Probability</Text>
                    <Text style={styles.metricValue}>
                      {(testResult.stress_probability * 100.0).toFixed(1)}%
                    </Text>
                    <Text style={styles.metricSub}>Raw model probability [{testResult.stress_probability.toFixed(4)}]</Text>
                  </View>

                  <View style={styles.metricItem}>
                    <Text style={styles.metricTitle}>Confidence</Text>
                    <Text style={styles.metricValue}>
                      {(testResult.confidence * 100.0).toFixed(1)}%
                    </Text>
                    <Text style={styles.metricSub}>Model classification confidence</Text>
                  </View>
                </View>

                <View style={styles.resultFooterRow}>
                  <Text style={styles.resultFooterText}>
                    Features Evaluated: {testResult.feature_count} / 26
                  </Text>
                  <Text style={styles.resultFooterText}>
                    Decision Threshold: {testResult.threshold}
                  </Text>
                </View>
              </View>
            </SanjeevniCard>
          ) : null}

          {/* Form Sections */}
          {FEATURE_SECTIONS.map((section, sIdx) => (
            <View key={sIdx} style={styles.sectionContainer}>
              <SectionHeader title={section.title} subtitle={section.subtitle} />
              <SanjeevniCard style={styles.sectionCard}>
                {section.fields.map((field) => {
                  const hasError = !!fieldErrors[field.key];
                  return (
                    <View key={field.key} style={styles.fieldGroup}>
                      <View style={styles.fieldLabelRow}>
                        <Text style={styles.fieldLabel}>{field.label}</Text>
                        <Text style={styles.fieldUnit}>[{field.unit}]</Text>
                      </View>
                      <Text style={styles.fieldDesc}>{field.description}</Text>

                      <TextInput
                        style={[styles.fieldInput, hasError && styles.fieldInputError]}
                        value={inputs[field.key]}
                        onChangeText={(text) => handleInputChange(field.key, text)}
                        placeholder={`Enter ${field.label} (${field.unit})`}
                        placeholderTextColor={colors.textMuted}
                        keyboardType="decimal-pad"
                        autoCapitalize="none"
                        autoCorrect={false}
                        editable={!isRunning}
                      />

                      {hasError ? (
                        <Text style={styles.fieldErrorText}>{fieldErrors[field.key]}</Text>
                      ) : null}
                    </View>
                  );
                })}
              </SanjeevniCard>
            </View>
          ))}

          {/* Action Buttons */}
          <TouchableOpacity
            activeOpacity={0.8}
            onPress={handleRunModelTest}
            disabled={isRunning}
            style={[styles.runButton, isRunning && styles.runButtonDisabled]}
          >
            {isRunning ? (
              <ActivityIndicator size="small" color={colors.textOnPrimary} />
            ) : (
              <>
                <Ionicons name="flash-outline" size={20} color={colors.textOnPrimary} />
                <Text style={styles.runButtonText}>RUN MODEL TEST</Text>
              </>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            activeOpacity={0.7}
            onPress={handleResetFields}
            disabled={isRunning}
            style={styles.resetButton}
          >
            <Ionicons name="refresh-outline" size={16} color={colors.textMuted} />
            <Text style={styles.resetButtonText}>Reset All Fields</Text>
          </TouchableOpacity>
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.gutter,
    paddingVertical: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderSubtle,
    backgroundColor: colors.surface,
  },
  backButton: {
    padding: spacing.xs,
    marginRight: spacing.sm,
  },
  headerTitleContainer: {
    flex: 1,
  },
  headerTitle: {
    fontSize: typography.size.lg,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  headerSubtitle: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 2,
  },
  devBadge: {
    backgroundColor: '#FEF3C7',
    borderWidth: 1,
    borderColor: '#FDE68A',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: radii.pill,
  },
  devBadgeText: {
    fontSize: 10,
    fontWeight: typography.weight.bold,
    color: '#D97706',
  },
  scrollContent: {
    paddingHorizontal: spacing.gutter,
    paddingTop: spacing.md,
    paddingBottom: spacing.xxl,
  },
  infoBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0FDFA',
    borderWidth: 1,
    borderColor: '#CCFBF1',
    borderRadius: radii.card,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  infoBannerText: {
    flex: 1,
    fontSize: 11,
    color: colors.primaryDark,
    marginLeft: spacing.sm,
    lineHeight: 16,
  },
  errorCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEE2E2',
    borderWidth: 1,
    borderColor: '#FECACA',
    borderRadius: radii.card,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  errorCardText: {
    flex: 1,
    fontSize: typography.size.xs,
    color: '#DC2626',
    marginLeft: spacing.sm,
    fontWeight: typography.weight.medium,
  },
  resultCard: {
    marginBottom: spacing.lg,
    borderColor: colors.primaryTint,
    borderWidth: 1.5,
  },
  resultHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
  },
  resultTag: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primaryTint,
    paddingHorizontal: spacing.sm,
    paddingVertical: 3,
    borderRadius: radii.pill,
  },
  resultTagText: {
    fontSize: 11,
    fontWeight: typography.weight.bold,
    color: colors.primaryDark,
    marginLeft: 4,
  },
  modelNameText: {
    fontSize: 11,
    color: colors.textMuted,
    fontWeight: typography.weight.semibold,
  },
  resultMainContainer: {
    alignItems: 'center',
  },
  resultLabel: {
    fontSize: typography.size.xs,
    color: colors.textMuted,
    marginBottom: spacing.xs,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  predictionBadge: {
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.sm,
    borderRadius: radii.pill,
    marginBottom: spacing.lg,
  },
  stressBadge: {
    backgroundColor: '#FEE2E2',
    borderWidth: 1,
    borderColor: '#FECACA',
  },
  baselineBadge: {
    backgroundColor: '#D1FAE5',
    borderWidth: 1,
    borderColor: '#A7F3D0',
  },
  predictionBadgeText: {
    fontSize: typography.size.base,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  metricsGrid: {
    flexDirection: 'row',
    width: '100%',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
  },
  metricItem: {
    flex: 0.48,
    backgroundColor: colors.surfaceMuted,
    borderRadius: radii.md,
    padding: spacing.md,
    alignItems: 'center',
  },
  metricTitle: {
    fontSize: 11,
    color: colors.textMuted,
    marginBottom: 4,
  },
  metricValue: {
    fontSize: typography.size.xl,
    fontWeight: typography.weight.bold,
    color: colors.primaryDark,
  },
  metricSub: {
    fontSize: 9,
    color: colors.textMuted,
    marginTop: 2,
    textAlign: 'center',
  },
  resultFooterRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
    borderTopWidth: 1,
    borderTopColor: colors.borderSubtle,
    paddingTop: spacing.sm,
  },
  resultFooterText: {
    fontSize: 10,
    color: colors.textMuted,
  },
  sectionContainer: {
    marginBottom: spacing.sm,
  },
  sectionCard: {
    paddingVertical: spacing.sm,
  },
  fieldGroup: {
    marginBottom: spacing.md,
  },
  fieldLabelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 2,
  },
  fieldLabel: {
    fontSize: typography.size.sm,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  fieldUnit: {
    fontSize: 11,
    color: colors.primaryDark,
    fontWeight: typography.weight.semibold,
  },
  fieldDesc: {
    fontSize: 11,
    color: colors.textMuted,
    marginBottom: spacing.xs,
  },
  fieldInput: {
    height: 44,
    backgroundColor: colors.surface,
    borderWidth: 1.5,
    borderColor: colors.borderSubtle,
    borderRadius: radii.card,
    paddingHorizontal: spacing.md,
    fontSize: typography.size.sm,
    color: colors.textPrimary,
  },
  fieldInputError: {
    borderColor: '#EF4444',
    backgroundColor: '#FEF2F2',
  },
  fieldErrorText: {
    fontSize: 10,
    color: '#DC2626',
    marginTop: 3,
    fontWeight: typography.weight.medium,
  },
  runButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primary,
    borderRadius: radii.button,
    paddingVertical: spacing.md,
    marginTop: spacing.md,
    ...shadows.button,
  },
  runButtonDisabled: {
    opacity: 0.6,
  },
  runButtonText: {
    color: colors.textOnPrimary,
    fontSize: typography.size.base,
    fontWeight: typography.weight.bold,
    marginLeft: spacing.xs,
  },
  resetButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.md,
    marginTop: spacing.xs,
  },
  resetButtonText: {
    color: colors.textMuted,
    fontSize: typography.size.xs,
    fontWeight: typography.weight.semibold,
    marginLeft: spacing.xs,
  },
});
