/**
 * My Wellness Record Screen
 * 
 * Health profile overview + historical real telemetry log.
 * Strictly consumes genuine records from /api/v1/history/vitals/{device_id}.
 * Never displays fabricated historical curves.
 */
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useHealthData } from '../src/context/HealthDataContext';
import { historyService } from '../src/services/historyService';
import { VitalsHistoryRecord } from '../src/api/types';
import { colors, spacing, typography, radii, shadows } from '../src/theme';
import { SanjeevniCard } from '../src/components/common/SanjeevniCard';
import { SectionHeader } from '../src/components/common/SectionHeader';
import { EmptyState } from '../src/components/common/EmptyState';
import { MetricHistoryRow } from '../src/components/records/MetricHistoryRow';

export default function RecordsScreen() {
  const { activeDeviceId } = useHealthData();
  const [records, setRecords] = useState<VitalsHistoryRecord[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  // User health metrics state (profile data from backend/user settings)
  const [height] = useState<string | null>(null);
  const [weight] = useState<string | null>(null);
  const [age] = useState<string | null>(null);
  const [activityTier] = useState<string | null>(null);

  const fetchHistory = async () => {
    if (!activeDeviceId) return;
    try {
      setIsLoading(true);
      const data = await historyService.getVitalsHistory(activeDeviceId, 30);
      setRecords(data);
    } catch {
      // Historical endpoint offline or empty
      setRecords([]);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [activeDeviceId]);

  const onRefresh = async () => {
    setIsRefreshing(true);
    await fetchHistory();
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.scrollContent}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl
          refreshing={isRefreshing}
          onRefresh={onRefresh}
          colors={[colors.primary]}
          tintColor={colors.primary}
        />
      }
    >
      {/* Health Overview Card */}
      <SectionHeader title="Biometric Profile" subtitle="Configured user attributes" />
      <SanjeevniCard style={styles.profileCard}>
        <View style={styles.profileGrid}>
          <View style={styles.profileItem}>
            <Ionicons name="body-outline" size={20} color={colors.primary} />
            <Text style={styles.profileValue}>{height || '--'}</Text>
            <Text style={styles.profileLabel}>Height</Text>
          </View>

          <View style={styles.profileItem}>
            <Ionicons name="barbell-outline" size={20} color={colors.primary} />
            <Text style={styles.profileValue}>{weight || '--'}</Text>
            <Text style={styles.profileLabel}>Weight</Text>
          </View>

          <View style={styles.profileItem}>
            <Ionicons name="calendar-outline" size={20} color={colors.primary} />
            <Text style={styles.profileValue}>{age || '--'}</Text>
            <Text style={styles.profileLabel}>Age</Text>
          </View>

          <View style={styles.profileItem}>
            <Ionicons name="fitness-outline" size={20} color={colors.primary} />
            <Text style={styles.profileValue}>{activityTier || '--'}</Text>
            <Text style={styles.profileLabel}>Activity</Text>
          </View>
        </View>
      </SanjeevniCard>

      {/* Telemetry History Section */}
      <SectionHeader
        title="Telemetry History"
        subtitle={activeDeviceId ? `Records for ${activeDeviceId}` : 'Select a device'}
        actionText="Refresh"
        onActionPress={fetchHistory}
      />

      {records.length > 0 ? (
        <SanjeevniCard style={styles.historyCard}>
          <View style={styles.historyHeader}>
            <Text style={[styles.headerCol, { flex: 1.2 }]}>Time</Text>
            <Text style={styles.headerCol}>HR</Text>
            <Text style={styles.headerCol}>HRV</Text>
            <Text style={styles.headerCol}>Temp</Text>
            <Text style={styles.headerCol}>EDA</Text>
          </View>

          {records.map((rec, idx) => (
            <MetricHistoryRow key={`${rec.timestamp}-${idx}`} record={rec} />
          ))}
        </SanjeevniCard>
      ) : (
        <EmptyState
          icon="document-text-outline"
          title="No Wellness Records Yet"
          description={
            activeDeviceId
              ? `No historical sensor samples have been persisted for wearable '${activeDeviceId}'. Stream telemetry to build records.`
              : 'Connect your ESP32 wearable to begin logging real physiological data.'
          }
        />
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollContent: {
    paddingHorizontal: spacing.gutter,
    paddingBottom: spacing.xxl,
    paddingTop: spacing.sm,
  },
  profileCard: {
    paddingVertical: spacing.lg,
  },
  profileGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
  },
  profileItem: {
    alignItems: 'center',
  },
  profileValue: {
    fontSize: typography.size.md,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
    marginTop: 4,
  },
  profileLabel: {
    fontSize: typography.size.xs,
    color: colors.textMuted,
    marginTop: 2,
  },
  historyCard: {
    padding: spacing.base,
  },
  historyHeader: {
    flexDirection: 'row',
    borderBottomWidth: 1.5,
    borderBottomColor: colors.border,
    paddingBottom: spacing.sm,
    marginBottom: spacing.xs,
  },
  headerCol: {
    flex: 1,
    fontSize: typography.size.xs,
    fontWeight: typography.weight.bold,
    color: colors.textSecondary,
    textAlign: 'center',
  },
});
