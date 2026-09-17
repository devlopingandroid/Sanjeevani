/**
 * Home Dashboard Screen
 * 
 * Central screen of the SANJEEVNI wellness wearable platform.
 * Closely follows the reference design layout:
 * - Header: Greeting, User avatar, Active wearable badge
 * - Main: Circular Current Estimated Stress ring
 * - Grid: 5 Physiological metrics (Heart Rate, HRV, Temperature, GSR, Motion)
 * - Section: Stress trend & Sanjeevni Insights
 * 
 * Strictly complies with the NO-MOCK-DATA policy:
 * Only displays real backend values; displays honest "--" / unavailable states otherwise.
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useHealthData } from '../../src/context/HealthDataContext';
import { useAuth } from '../../src/context/AuthContext';
import { colors, spacing, typography, radii } from '../../src/theme';
import { StressRing } from '../../src/components/dashboard/StressRing';
import { MetricCard } from '../../src/components/dashboard/MetricCard';
import { DeviceStatusBadge } from '../../src/components/dashboard/DeviceStatusBadge';
import { SanjeevniInsight } from '../../src/components/dashboard/SanjeevniInsight';
import { SectionHeader } from '../../src/components/common/SectionHeader';
import {
  formatBpm,
  formatSpo2,
  formatMs,
  formatTempF,
  formatGSR,
  formatMotion,
} from '../../src/utils/formatters';
import { DataStatus } from '../../src/api/types';

export default function HomeScreen() {
  const router = useRouter();
  const { user } = useAuth();
  const { summary, bufferSampleCount, isRefreshing, refreshData, triggerStressEvaluation } = useHealthData();
  const [selectedTrendPeriod, setSelectedTrendPeriod] = useState<'Today' | 'Week' | 'Month'>('Today');

  const vitals = summary?.vitals;
  const stress = summary?.stress;
  const dataStatus = summary?.data_status || DataStatus.NO_DATA;
  const deviceStatus = summary?.device_status;
  const deviceId = summary?.device_id || null;

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={refreshData}
            colors={[colors.primary]}
            tintColor={colors.primary}
          />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.userInfo}>
            <View style={styles.avatarCircle}>
              <Text style={styles.avatarText}>SJ</Text>
            </View>
            <View style={styles.userTextContainer}>
              <Text style={styles.greetingText}>Welcome,</Text>
              <Text style={styles.userNameText}>User</Text>
            </View>
          </View>

          <View style={styles.headerRight}>
            <DeviceStatusBadge
              deviceId={deviceId}
              status={deviceStatus || dataStatus}
              onPress={() => router.push('/device-details')}
            />
          </View>
        </View>

        {/* Centerpiece: Current Estimated Stress */}
        <StressRing
          score={stress?.stress_score}
          level={stress?.stress_level}
          dataStatus={dataStatus}
          message={summary?.message}
          onPress={() => router.push('/stress-details')}
        />

        {/* Quick Action Button to re-evaluate on demand */}
        <View style={styles.actionRow}>
          <TouchableOpacity
            activeOpacity={0.8}
            onPress={() => triggerStressEvaluation()}
            style={styles.evaluateBtn}
          >
            <Ionicons name="pulse" size={16} color={colors.primary} />
            <Text style={styles.evaluateBtnText}>
              Evaluate 30s Buffer ({bufferSampleCount || 0} samples)
            </Text>
          </TouchableOpacity>
        </View>

        {/* Physiological Vitals Grid */}
        <SectionHeader
          title="Physiological Vitals"
          subtitle="Real-time ESP32 biosensor stream"
          actionText="View History →"
          onActionPress={() => router.push('/records')}
        />

        <View style={styles.metricsGrid}>
          <View style={styles.metricRow}>
            <MetricCard
              icon="heart"
              iconColor="#EF4444"
              accentBg="#FEE2E2"
              title="Heart Rate"
              value={formatBpm(vitals?.heart_rate_bpm)}
              unit="BPM"
              subtitle="MAX30102 PPG"
            />
            <MetricCard
              icon="medical"
              iconColor="#0284C7"
              accentBg="#E0F2FE"
              title="Blood Oxygen"
              value={formatSpo2(vitals?.spo2)}
              unit=""
              subtitle="SpO2 Sensor"
            />
          </View>

          <View style={styles.metricRow}>
            <MetricCard
              icon="thermometer"
              iconColor="#F59E0B"
              accentBg="#FEF3C7"
              title="Skin Temp"
              value={formatTempF(vitals?.temperature_f)}
              unit=""
              subtitle="MAX30205 Sensor"
            />
            <MetricCard
              icon="water"
              iconColor="#0D9488"
              accentBg="#CCFBF1"
              title="Skin Conductance"
              value={formatGSR(vitals?.skin_conductance_us)}
              unit=""
              subtitle="GSR Electrodes"
            />
          </View>

          <View style={styles.metricRow}>
            <MetricCard
              icon="speedometer"
              iconColor="#6366F1"
              accentBg="#EEF2FF"
              title="Activity Motion"
              value={formatMotion(vitals?.motion_magnitude)}
              unit="units"
              subtitle="MPU6050 3D Mag"
            />
            <MetricCard
              icon="pulse"
              iconColor="#10B981"
              accentBg="#D1FAE5"
              title="HRV (RMSSD)"
              value={formatMs(vitals?.hrv_rmssd_ms)}
              unit="ms"
              subtitle="Autonomic Index"
            />
          </View>
        </View>

        {/* Stress Trend Section */}
        <SectionHeader
          title="Stress Trend"
          subtitle="Empirical autonomic monitoring"
        />

        <View style={styles.filterRow}>
          {(['Today', 'Week', 'Month'] as const).map((period) => (
            <TouchableOpacity
              key={period}
              activeOpacity={0.8}
              onPress={() => setSelectedTrendPeriod(period)}
              style={[
                styles.filterPill,
                selectedTrendPeriod === period && styles.filterPillActive,
              ]}
            >
              <Text
                style={[
                  styles.filterPillText,
                  selectedTrendPeriod === period && styles.filterPillTextActive,
                ]}
              >
                {period}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Honest Trend State */}
        <View style={styles.trendContainer}>
          {dataStatus === DataStatus.REAL_DATA && stress && stress.stress_score !== null ? (
            <View style={styles.trendSummaryRow}>
              <View style={styles.trendCol}>
                <Text style={styles.trendValue}>{Math.round(stress.stress_score)}%</Text>
                <Text style={styles.trendLabel}>Latest Estimate</Text>
              </View>
              <View style={styles.trendDivider} />
              <View style={styles.trendCol}>
                <Text style={styles.trendValue}>{stress.stress_level || 'BASELINE'}</Text>
                <Text style={styles.trendLabel}>Current State</Text>
              </View>
            </View>
          ) : (
            <View style={styles.emptyTrendBox}>
              <Ionicons name="bar-chart-outline" size={24} color={colors.textMuted} />
              <Text style={styles.emptyTrendText}>
                Not enough real sensor data yet to render a trend curve.
              </Text>
            </View>
          )}
        </View>

        {/* Sanjeevni Insights */}
        <SectionHeader
          title="Sanjeevni Insight"
          subtitle="Clinical & physiological observations"
        />
        <SanjeevniInsight
          dataStatus={dataStatus}
          stressScore={stress?.stress_score}
          heartRate={vitals?.heart_rate_bpm}
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: spacing.md,
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatarCircle: {
    width: 44,
    height: 44,
    borderRadius: radii.pill,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  avatarText: {
    color: colors.textOnPrimary,
    fontSize: typography.size.md,
    fontWeight: typography.weight.bold,
  },
  userTextContainer: {
    justifyContent: 'center',
  },
  greetingText: {
    fontSize: typography.size.xs,
    color: colors.textMuted,
    fontWeight: typography.weight.medium,
  },
  userNameText: {
    fontSize: typography.size.lg,
    color: colors.textPrimary,
    fontWeight: typography.weight.bold,
  },
  headerRight: {
    alignItems: 'flex-end',
  },
  actionRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginVertical: spacing.xs,
  },
  evaluateBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.borderTeal,
    paddingHorizontal: spacing.base,
    paddingVertical: spacing.sm,
    borderRadius: radii.pill,
  },
  evaluateBtnText: {
    fontSize: typography.size.xs,
    fontWeight: typography.weight.semibold,
    color: colors.primary,
    marginLeft: 6,
  },
  metricsGrid: {
    marginVertical: spacing.xs,
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },
  filterRow: {
    flexDirection: 'row',
    marginBottom: spacing.md,
  },
  filterPill: {
    paddingHorizontal: spacing.base,
    paddingVertical: spacing.xs + 2,
    borderRadius: radii.pill,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    marginRight: spacing.sm,
  },
  filterPillActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  filterPillText: {
    fontSize: typography.size.xs,
    fontWeight: typography.weight.semibold,
    color: colors.textSecondary,
  },
  filterPillTextActive: {
    color: colors.textOnPrimary,
  },
  trendContainer: {
    backgroundColor: colors.surface,
    borderRadius: radii.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.base,
    marginVertical: spacing.xs,
  },
  trendSummaryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    paddingVertical: spacing.sm,
  },
  trendCol: {
    alignItems: 'center',
  },
  trendValue: {
    fontSize: typography.size.xxl,
    fontWeight: typography.weight.bold,
    color: colors.primaryDark,
  },
  trendLabel: {
    fontSize: typography.size.xs,
    color: colors.textMuted,
    marginTop: 2,
  },
  trendDivider: {
    width: 1,
    height: 36,
    backgroundColor: colors.border,
  },
  emptyTrendBox: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.lg,
  },
  emptyTrendText: {
    fontSize: typography.size.xs,
    color: colors.textMuted,
    textAlign: 'center',
    marginTop: spacing.sm,
    maxWidth: 240,
  },
});
