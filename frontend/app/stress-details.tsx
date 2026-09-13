/**
 * Estimated Stress Details Modal Screen
 * 
 * Deep-dive analysis of real-time stress probability, confidence,
 * and 26-feature physiological vector.
 */
import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useHealthData } from '../src/context/HealthDataContext';
import { colors, spacing, typography, radii, shadows } from '../src/theme';
import { SanjeevniCard } from '../src/components/common/SanjeevniCard';
import { StatusBadge } from '../src/components/common/StatusBadge';
import { SectionHeader } from '../src/components/common/SectionHeader';
import { PrimaryButton } from '../src/components/common/PrimaryButton';
import { formatStressScore, formatRelativeTime } from '../src/utils/formatters';
import { DataStatus } from '../src/api/types';

export default function StressDetailsScreen() {
  const router = useRouter();
  const { summary, latestStress, triggerStressEvaluation, activeDeviceId } = useHealthData();

  const stress = summary?.stress;
  const dataStatus = summary?.data_status || DataStatus.NO_DATA;
  const isReal = dataStatus === DataStatus.REAL_DATA && stress?.stress_score !== null;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Overview Card */}
      <SanjeevniCard style={styles.mainCard} floating>
        <View style={styles.topRow}>
          <StatusBadge status={dataStatus} />
          <Text style={styles.timestamp}>
            {formatRelativeTime(stress?.predicted_at)}
          </Text>
        </View>

        <View style={styles.scoreContainer}>
          <Text style={[styles.scoreNumber, !isReal && styles.scoreUnavailable]}>
            {isReal ? formatStressScore(stress?.stress_score) : '--'}
          </Text>
          <Text style={styles.scoreLevel}>
            {isReal ? stress?.stress_level : 'NOT EVALUATED'}
          </Text>
          <Text style={styles.modelStatusText}>
            Model: {latestStress?.model_status || 'RandomForest (26 Features)'}
          </Text>
        </View>

        <PrimaryButton
          title="Re-Evaluate 30s Buffer"
          onPress={triggerStressEvaluation}
          variant="secondary"
          icon={<Ionicons name="reload" size={16} color={colors.primary} />}
        />
      </SanjeevniCard>

      {/* Probability & Model Metrics */}
      <SectionHeader title="Inference Metrics" subtitle="Scikit-Learn predict_proba outputs" />
      <SanjeevniCard>
        <View style={styles.metricRow}>
          <Text style={styles.metricLabel}>Raw Class Probability (P1)</Text>
          <Text style={styles.metricVal}>
            {latestStress?.raw_probability !== null && latestStress?.raw_probability !== undefined
              ? latestStress.raw_probability.toFixed(4)
              : '--'}
          </Text>
        </View>
        <View style={styles.metricRow}>
          <Text style={styles.metricLabel}>Confidence Interval</Text>
          <Text style={styles.metricVal}>
            {stress?.confidence ? `${(stress.confidence * 100).toFixed(1)}%` : '--'}
          </Text>
        </View>
        <View style={styles.metricRow}>
          <Text style={styles.metricLabel}>Target Device</Text>
          <Text style={styles.metricVal}>{activeDeviceId || 'None'}</Text>
        </View>
        <View style={[styles.metricRow, { borderBottomWidth: 0 }]}>
          <Text style={styles.metricLabel}>Features Analyzed</Text>
          <Text style={styles.metricVal}>{latestStress?.features_used_count || 0} / 26</Text>
        </View>
      </SanjeevniCard>

      {/* 26 Feature Snapshot Table */}
      {latestStress?.features_snapshot ? (
        <>
          <SectionHeader
            title="Extracted Physiological Features"
            subtitle="Verified 26-feature vector from 30s window"
          />
          <SanjeevniCard style={styles.featuresCard}>
            {Object.entries(latestStress.features_snapshot).map(([key, val], idx) => (
              <View key={key} style={styles.featureItem}>
                <Text style={styles.featureName}>{idx + 1}. {key}</Text>
                <Text style={styles.featureVal}>{typeof val === 'number' ? val.toFixed(3) : val}</Text>
              </View>
            ))}
          </SanjeevniCard>
        </>
      ) : null}

      {/* Clinical Disclaimer */}
      <View style={styles.disclaimerBox}>
        <Ionicons name="shield-outline" size={20} color={colors.primary} />
        <Text style={styles.disclaimerText}>
          Estimated Stress represents an algorithmic approximation of autonomic nervous
          system sympathetic activation derived from multi-modal wearable sensor streams.
          It does not diagnose medical anxiety, clinical distress, or heart disease.
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
  mainCard: {
    alignItems: 'center',
    paddingVertical: spacing.xl,
    marginBottom: spacing.md,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%',
    marginBottom: spacing.md,
  },
  timestamp: {
    fontSize: typography.size.xs,
    color: colors.textMuted,
  },
  scoreContainer: {
    alignItems: 'center',
    marginVertical: spacing.lg,
  },
  scoreNumber: {
    fontSize: 54,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
    letterSpacing: -1,
  },
  scoreUnavailable: {
    color: colors.textMuted,
  },
  scoreLevel: {
    fontSize: typography.size.sm,
    fontWeight: typography.weight.bold,
    color: colors.primaryDark,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginTop: 4,
  },
  modelStatusText: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 6,
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.sm + 2,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderSubtle,
  },
  metricLabel: {
    fontSize: typography.size.sm,
    color: colors.textSecondary,
  },
  metricVal: {
    fontSize: typography.size.sm,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  featuresCard: {
    padding: spacing.sm,
  },
  featureItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
    paddingHorizontal: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderSubtle,
  },
  featureName: {
    fontSize: 12,
    color: colors.textSecondary,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
  featureVal: {
    fontSize: 12,
    fontWeight: typography.weight.bold,
    color: colors.primaryDark,
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
  },
  disclaimerBox: {
    flexDirection: 'row',
    backgroundColor: colors.primaryTint,
    borderRadius: radii.card,
    borderWidth: 1,
    borderColor: colors.borderTeal,
    padding: spacing.md,
    marginTop: spacing.lg,
  },
  disclaimerText: {
    flex: 1,
    fontSize: 11,
    color: colors.textSecondary,
    lineHeight: 16,
    marginLeft: spacing.sm,
  },
});
