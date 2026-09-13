/**
 * Yoga & Interactive Breathing Screen
 * 
 * Interactive paced respiration guide for parasympathetic nervous system tone,
 * plus guided mobility and relaxation postures.
 */
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, typography, radii, shadows } from '../src/theme';
import { SanjeevniCard } from '../src/components/common/SanjeevniCard';
import { SectionHeader } from '../src/components/common/SectionHeader';
import { PrimaryButton } from '../src/components/common/PrimaryButton';

export default function YogaBreathingScreen() {
  const [isActive, setIsActive] = useState(false);
  const [phase, setPhase] = useState<'Inhale' | 'Hold' | 'Exhale'>('Inhale');
  const [secondsLeft, setSecondsLeft] = useState(4);
  const [cyclesCompleted, setCyclesCompleted] = useState(0);

  // 4-7-8 Breathing Cycle
  useEffect(() => {
    let timer: any;
    if (isActive) {
      timer = setInterval(() => {
        setSecondsLeft((prev) => {
          if (prev > 1) return prev - 1;
          // Switch phase
          if (phase === 'Inhale') {
            setPhase('Hold');
            return 7;
          } else if (phase === 'Hold') {
            setPhase('Exhale');
            return 8;
          } else {
            setPhase('Inhale');
            setCyclesCompleted((c) => c + 1);
            return 4;
          }
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [isActive, phase]);

  const toggleSession = () => {
    if (isActive) {
      setIsActive(false);
      setPhase('Inhale');
      setSecondsLeft(4);
    } else {
      setIsActive(true);
      setPhase('Inhale');
      setSecondsLeft(4);
    }
  };

  const getPhaseColor = () => {
    switch (phase) {
      case 'Inhale':
        return colors.primary;
      case 'Hold':
        return '#0284C7';
      case 'Exhale':
        return '#8B5CF6';
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Interactive Breathing Ring */}
      <SectionHeader title="4-7-8 Diaphragmatic Breathing" subtitle="Paced vagal nerve stimulation" />
      <SanjeevniCard style={styles.breathingCard} floating>
        <View
          style={[
            styles.breathingCircle,
            { borderColor: getPhaseColor(), backgroundColor: colors.primaryTint },
          ]}
        >
          <Text style={[styles.phaseText, { color: getPhaseColor() }]}>
            {isActive ? phase : 'Ready'}
          </Text>
          <Text style={styles.secondsText}>
            {isActive ? `${secondsLeft}s` : 'Tap Start'}
          </Text>
        </View>

        <Text style={styles.cycleCounter}>
          Cycles completed: {cyclesCompleted}
        </Text>

        <PrimaryButton
          title={isActive ? 'Stop Session' : 'Begin 4-7-8 Breathing'}
          onPress={toggleSession}
          variant={isActive ? 'outline' : 'primary'}
          style={styles.startBtn}
          icon={<Ionicons name={isActive ? 'stop' : 'play'} size={18} color={isActive ? colors.primary : colors.textOnPrimary} />}
        />
      </SanjeevniCard>

      {/* Guided Asanas */}
      <SectionHeader title="Restorative Yoga Postures" subtitle="Reduce physical somatic stress" />

      <SanjeevniCard style={styles.asanaCard}>
        <View style={styles.asanaTop}>
          <Text style={styles.asanaTitle}>Balasana (Child's Pose)</Text>
          <Text style={styles.asanaDuration}>3–5 min</Text>
        </View>
        <Text style={styles.asanaDesc}>
          Gently stretches hips, thighs, and ankles while calming the brain and helping
          relieve stress and fatigue.
        </Text>
      </SanjeevniCard>

      <SanjeevniCard style={styles.asanaCard}>
        <View style={styles.asanaTop}>
          <Text style={styles.asanaTitle}>Viparita Karani (Legs-Up-The-Wall)</Text>
          <Text style={styles.asanaDuration}>5–10 min</Text>
        </View>
        <Text style={styles.asanaDesc}>
          Improves lymphatic and venous drainage back to the heart, signaling the autonomic
          nervous system to enter restorative rest.
        </Text>
      </SanjeevniCard>

      <SanjeevniCard style={styles.asanaCard}>
        <View style={styles.asanaTop}>
          <Text style={styles.asanaTitle}>Savasana (Corpse Pose)</Text>
          <Text style={styles.asanaDuration}>5 min</Text>
        </View>
        <Text style={styles.asanaDesc}>
          Complete neuromuscular relaxation. Focus on gentle diaphragmatic belly breathing
          and release tension throughout the forehead and jaw.
        </Text>
      </SanjeevniCard>
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
  breathingCard: {
    alignItems: 'center',
    paddingVertical: spacing.xl,
    marginBottom: spacing.md,
  },
  breathingCircle: {
    width: 170,
    height: 170,
    borderRadius: 85,
    borderWidth: 8,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.base,
  },
  phaseText: {
    fontSize: typography.size.lg,
    fontWeight: typography.weight.bold,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  secondsText: {
    fontSize: typography.size.display,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
    marginTop: 2,
  },
  cycleCounter: {
    fontSize: typography.size.xs,
    color: colors.textMuted,
    marginBottom: spacing.md,
  },
  startBtn: {
    width: 220,
  },
  asanaCard: {
    marginVertical: spacing.xs,
    padding: spacing.base,
  },
  asanaTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  asanaTitle: {
    fontSize: typography.size.base,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  asanaDuration: {
    fontSize: 11,
    color: colors.primary,
    fontWeight: typography.weight.semibold,
  },
  asanaDesc: {
    fontSize: typography.size.xs,
    color: colors.textSecondary,
    lineHeight: 18,
  },
});
