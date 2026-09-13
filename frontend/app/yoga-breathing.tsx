/**
 * Yoga & Interactive Breathing Screen
 * 
 * Interactive paced respiration guide for parasympathetic nervous system tone,
 * plus guided mobility and restorative relaxation postures.
 * Visual baseline: Calm teal/white palette, rounded cards, clean icons,
 * duration tags, clear instructions, interactive Start CTA, and official YouTube
 * instructional videos via YouTube Data API v3 backend.
 */
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  Linking,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, typography, radii, shadows } from '../src/theme';
import { SanjeevniCard } from '../src/components/common/SanjeevniCard';
import { SectionHeader } from '../src/components/common/SectionHeader';
import { PrimaryButton } from '../src/components/common/PrimaryButton';
import { wellnessService } from '../src/services/wellnessService';
import { YouTubeVideoItem } from '../src/api/types';

interface PostureItem {
  title: string;
  searchKey: string;
  duration: string;
  level: string;
  instructions: string;
  benefit: string;
  icon: keyof typeof Ionicons.glyphMap;
  color: string;
}

export default function YogaBreathingScreen() {
  const [isActive, setIsActive] = useState(false);
  const [phase, setPhase] = useState<'Inhale' | 'Hold' | 'Exhale'>('Inhale');
  const [secondsLeft, setSecondsLeft] = useState(4);
  const [cyclesCompleted, setCyclesCompleted] = useState(0);
  const [activeCategory, setActiveCategory] = useState<'All' | 'Breathing' | 'Asanas'>('All');

  const [videoMap, setVideoMap] = useState<
    Record<string, { loading: boolean; videos: YouTubeVideoItem[]; error: boolean; errorMessage?: string }>
  >({});

  const postures: PostureItem[] = [
    {
      title: "Balasana (Child's Pose)",
      searchKey: "Child's Pose",
      duration: '3–5 min',
      level: 'Restorative',
      instructions: 'Kneel on the floor, touch your big toes together, sit on your heels, then separate your knees about as wide as your hips. Fold forward and lay your torso down between your thighs.',
      benefit: 'Stimulates parasympathetic nervous branch & relieves lower back pressure',
      icon: 'body',
      color: colors.yogaAccent,
    },
    {
      title: 'Marjaryasana-Bitilasana (Cat-Cow)',
      searchKey: 'Cat-Cow',
      duration: '5 min',
      level: 'Gentle Mobility',
      instructions: 'Begin on hands and knees. Inhale as you drop your belly and lift chest and tailbone (Cow). Exhale as you draw belly in and arch your spine up to ceiling (Cat).',
      benefit: 'Synchronizes respiration with spinal mobilization to release dorsal tightness',
      icon: 'sync-outline',
      color: '#0284C7',
    },
    {
      title: 'Vrikshasana (Tree Pose)',
      searchKey: 'Tree Pose',
      duration: '3 min',
      level: 'Proprioception',
      instructions: 'Shift weight onto left foot. Place sole of right foot on left inner thigh or calf (avoid the knee). Bring hands to prayer at chest or overhead.',
      benefit: 'Improves neuromuscular focus and calms mental distraction',
      icon: 'fitness-outline',
      color: '#059669',
    },
    {
      title: 'Viparita Karani (Legs-Up-The-Wall)',
      searchKey: 'Legs-Up-The-Wall',
      duration: '5–10 min',
      level: 'Restorative',
      instructions: 'Lie on your back with sitting bones against wall and legs extended straight up. Rest arms comfortably at sides with palms turned upward.',
      benefit: 'Venous drainage to reduce resting heart rate and arterial pressure',
      icon: 'bed-outline',
      color: '#8B5CF6',
    },
    {
      title: 'Savasana (Corpse Pose)',
      searchKey: 'Corpse Pose',
      duration: '5–10 min',
      level: 'Deep Recovery',
      instructions: 'Lie flat on your back, legs separated naturally, arms alongside body with palms up. Close your eyes and allow full relaxation with steady nasal breathing.',
      benefit: 'Full autonomic equilibrium reset and somatic release',
      icon: 'moon-outline',
      color: '#6366F1',
    },
  ];

  // Fetch YouTube instructional videos for postures
  useEffect(() => {
    let isMounted = true;

    async function fetchPostureVideos() {
      postures.forEach(async (p) => {
        if (isMounted) {
          setVideoMap((prev) => ({
            ...prev,
            [p.searchKey]: { loading: true, videos: [], error: false },
          }));
        }

        try {
          const res = await wellnessService.getExerciseVideos(p.searchKey);
          if (isMounted) {
            setVideoMap((prev) => ({
              ...prev,
              [p.searchKey]: {
                loading: false,
                videos: res.videos || [],
                error: false,
              },
            }));
          }
        } catch (err: any) {
          if (isMounted) {
            let errorMsg = "Videos are temporarily unavailable.";
            const statusCode = err?.statusCode ?? err?.status;
            const messageStr = (err?.message || "").toLowerCase();

            if (
              statusCode === 503 ||
              messageStr.includes("configuration") ||
              messageStr.includes("unconfigured") ||
              messageStr.includes("service is temporarily unavailable")
            ) {
              errorMsg = "Video service is temporarily unavailable.";
            } else if (
              statusCode === 504 ||
              statusCode === 408 ||
              statusCode === 0 ||
              messageStr.includes("unable to load") ||
              messageStr.includes("network") ||
              messageStr.includes("timed out") ||
              messageStr.includes("connect")
            ) {
              errorMsg = "Unable to load videos. Please try again.";
            } else if (
              statusCode === 502 ||
              statusCode === 429 ||
              statusCode === 400 ||
              messageStr.includes("temporarily unavailable")
            ) {
              errorMsg = "Videos are temporarily unavailable.";
            }

            setVideoMap((prev) => ({
              ...prev,
              [p.searchKey]: { loading: false, videos: [], error: true, errorMessage: errorMsg },
            }));
          }
        }
      });
    }

    fetchPostureVideos();

    return () => {
      isMounted = false;
    };
  }, []);

  // 4-7-8 Breathing Cycle
  useEffect(() => {
    let timer: any;
    if (isActive) {
      timer = setInterval(() => {
        setSecondsLeft((prev) => {
          if (prev > 1) return prev - 1;
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
      {/* Category Filter Chips */}
      <View style={styles.categoryRow}>
        {(['All', 'Breathing', 'Asanas'] as const).map((cat) => (
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

      {/* Interactive Breathing Ring */}
      {(activeCategory === 'All' || activeCategory === 'Breathing') && (
        <>
          <SectionHeader
            title="4-7-8 Diaphragmatic Breathing"
            subtitle="Paced vagal nerve stimulation to reduce acute stress"
          />
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
        </>
      )}

      {/* Guided Asanas */}
      {(activeCategory === 'All' || activeCategory === 'Asanas') && (
        <>
          <SectionHeader
            title="Restorative Yoga Postures"
            subtitle="Follow step-by-step instructions to relieve somatic stress"
          />

          {postures.map((p, idx) => {
            const vState = videoMap[p.searchKey];

            return (
              <SanjeevniCard key={idx} style={styles.asanaCard}>
                <View style={styles.asanaTop}>
                  <View style={styles.asanaTitleContainer}>
                    <Text style={styles.asanaTitle}>{p.title}</Text>
                    <View style={styles.levelBadge}>
                      <Text style={styles.levelText}>{p.level}</Text>
                    </View>
                  </View>
                  <Text style={styles.asanaDuration}>{p.duration}</Text>
                </View>

                <Text style={styles.instructionHeader}>Instructions:</Text>
                <Text style={styles.asanaInstructions}>{p.instructions}</Text>

                <View style={styles.benefitContainer}>
                  <Ionicons name="sparkles" size={14} color={p.color} />
                  <Text style={styles.benefitText}>{p.benefit}</Text>
                </View>

                {/* Watch & Learn Section */}
                <View style={styles.watchLearnSection}>
                  <View style={styles.watchLearnHeader}>
                    <Ionicons name="logo-youtube" size={16} color="#FF0000" />
                    <Text style={styles.watchLearnTitle}>Watch & Learn</Text>
                  </View>

                  {vState?.loading ? (
                    <View style={styles.videoStateBox}>
                      <ActivityIndicator size="small" color={colors.primary} />
                      <Text style={styles.videoStateText}>Finding helpful videos...</Text>
                    </View>
                  ) : vState?.error ? (
                    <Text style={styles.videoErrorText}>{vState.errorMessage || "Videos are temporarily unavailable."}</Text>
                  ) : !vState?.videos || vState.videos.length === 0 ? (
                    <Text style={styles.videoEmptyText}>No instructional videos found for this exercise.</Text>
                  ) : (
                    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.videoScroll}>
                      {vState.videos.map((vid) => (
                        <TouchableOpacity
                          key={vid.video_id}
                          activeOpacity={0.85}
                          onPress={() => Linking.openURL(vid.youtube_url)}
                          style={styles.videoCard}
                        >
                          <Image
                            source={{ uri: vid.thumbnail_url }}
                            style={styles.videoThumbnail}
                            resizeMode="cover"
                          />
                          <View style={styles.videoInfoBox}>
                            <Text style={styles.videoTitleText} numberOfLines={2}>
                              {vid.title}
                            </Text>
                            <Text style={styles.videoChannelText} numberOfLines={1}>
                              {vid.channel_title}
                            </Text>
                            <View style={styles.watchCtaBtn}>
                              <Ionicons name="play" size={10} color="#FFFFFF" />
                              <Text style={styles.watchCtaText}>Watch on YouTube</Text>
                            </View>
                          </View>
                        </TouchableOpacity>
                      ))}
                    </ScrollView>
                  )}
                </View>
              </SanjeevniCard>
            );
          })}
        </>
      )}
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
  categoryRow: {
    flexDirection: 'row',
    marginBottom: spacing.base,
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
    alignItems: 'flex-start',
    marginBottom: spacing.xs,
  },
  asanaTitleContainer: {
    flex: 1,
    marginRight: spacing.sm,
  },
  asanaTitle: {
    fontSize: typography.size.base,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
    marginBottom: 4,
  },
  levelBadge: {
    backgroundColor: colors.primaryTint,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radii.pill,
    alignSelf: 'flex-start',
  },
  levelText: {
    fontSize: 10,
    fontWeight: typography.weight.semibold,
    color: colors.primaryDark,
  },
  asanaDuration: {
    fontSize: 12,
    color: colors.primary,
    fontWeight: typography.weight.bold,
  },
  instructionHeader: {
    fontSize: typography.size.xs,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
    marginTop: spacing.xs,
    marginBottom: 2,
  },
  asanaInstructions: {
    fontSize: typography.size.xs,
    color: colors.textSecondary,
    lineHeight: 18,
  },
  benefitContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceMuted,
    padding: spacing.sm,
    borderRadius: radii.sm,
    marginTop: spacing.sm,
  },
  benefitText: {
    fontSize: 11,
    color: colors.textSecondary,
    marginLeft: spacing.xs,
    flex: 1,
    lineHeight: 16,
  },
  watchLearnSection: {
    marginTop: spacing.md,
    paddingTop: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.borderSubtle,
  },
  watchLearnHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  watchLearnTitle: {
    fontSize: typography.size.xs,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
    marginLeft: 6,
  },
  videoStateBox: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.xs,
  },
  videoStateText: {
    fontSize: 11,
    color: colors.textMuted,
    marginLeft: spacing.xs,
  },
  videoErrorText: {
    fontSize: 11,
    color: '#DC2626',
    fontStyle: 'italic',
  },
  videoEmptyText: {
    fontSize: 11,
    color: colors.textMuted,
    fontStyle: 'italic',
  },
  videoScroll: {
    flexDirection: 'row',
    marginTop: 4,
  },
  videoCard: {
    width: 170,
    backgroundColor: colors.surfaceSubtle,
    borderRadius: radii.md,
    borderWidth: 1,
    borderColor: colors.border,
    marginRight: spacing.sm,
    overflow: 'hidden',
  },
  videoThumbnail: {
    width: '100%',
    height: 96,
    backgroundColor: colors.borderSubtle,
  },
  videoInfoBox: {
    padding: spacing.xs + 2,
  },
  videoTitleText: {
    fontSize: 11,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
    lineHeight: 15,
    marginBottom: 2,
  },
  videoChannelText: {
    fontSize: 10,
    color: colors.textMuted,
    marginBottom: 6,
  },
  watchCtaBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FF0000',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: radii.pill,
    alignSelf: 'flex-start',
  },
  watchCtaText: {
    fontSize: 9,
    fontWeight: typography.weight.bold,
    color: '#FFFFFF',
    marginLeft: 3,
  },
});
