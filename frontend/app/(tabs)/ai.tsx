/**
 * Sanjeevni AI Screen
 * 
 * Intelligent autonomic nervous system wellness companion.
 * Real, end-to-end conversation powered strictly through FastAPI backend (/api/v1/ai/chat)
 * with full database persistence and health domain guard protection.
 * 
 * Strictly complies with ZERO HARDCODED DATA policy:
 * - Never invents simulated AI dialogues.
 * - Displays honest error messages if AI is offline or key unconfigured.
 * - Real responses come strictly from the backend.
 */
import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { aiService } from '../../src/services/aiService';
import { wellnessService } from '../../src/services/wellnessService';
import { ChatMessage as APIChatMessage, MultimodalWellnessResponse } from '../../src/api/types';
import { colors, spacing, typography, radii, shadows } from '../../src/theme';
import { FormattedText } from '../../src/components/common/FormattedText';

interface UIMessage {
  id: string;
  sender: 'ai' | 'user' | 'system';
  text: string;
  timestamp: string;
}

export default function AIScreen() {
  const router = useRouter();
  const scrollViewRef = useRef<ScrollView>(null);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(false);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [wellnessContext, setWellnessContext] = useState<MultimodalWellnessResponse | null>(null);

  const introSystemMessage: UIMessage = {
    id: 'system-intro',
    sender: 'system',
    text: 'Ask Sanjeevni about your health and wellness.',
    timestamp: 'Sanjeevni Assistant',
  };

  const [messages, setMessages] = useState<UIMessage[]>([introSystemMessage]);

  // Fetch authoritatively computed wellness context strictly from backend API
  const fetchWellnessContext = async (convId?: string) => {
    try {
      const data = await wellnessService.getWellnessContext(convId || undefined);
      setWellnessContext(data);
    } catch {
      // Non-blocking status fetch
    }
  };

  // Load latest active conversation on screen mount if available
  useEffect(() => {
    let isMounted = true;

    async function loadActiveConversation() {
      try {
        setIsInitializing(true);
        fetchWellnessContext();
        const conversations = await aiService.listConversations(1, 0);
        if (conversations && conversations.items && conversations.items.length > 0) {
          const latestConv = conversations.items[0];
          if (isMounted) {
            setActiveConversationId(latestConv.id);
            // Fetch messages for this conversation
            const msgData = await aiService.getMessages(latestConv.id, 50, 0);
            if (msgData && msgData.items && msgData.items.length > 0) {
              const loadedMsgs: UIMessage[] = msgData.items.map((m) => ({
                id: m.id,
                sender: m.role === 'user' ? 'user' : 'ai',
                text: m.message,
                timestamp: new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              }));
              setMessages([introSystemMessage, ...loadedMsgs]);
            }
          }
        }
      } catch (err) {
        // Non-blocking: if network fails or no conversations yet, start fresh
      } finally {
        if (isMounted) {
          setIsInitializing(false);
        }
      }
    }

    loadActiveConversation();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    scrollViewRef.current?.scrollToEnd({ animated: true });
  }, [messages, isLoading]);

  const quickPrompts = [
    { label: 'How can I manage stress?', prompt: 'How can I manage and lower my stress?' },
    { label: 'Help me sleep better', prompt: 'How can I improve my sleep quality?' },
    { label: 'Explain my wellness data', prompt: 'What can you tell me about my current biometric stress data?' },
    { label: 'Give me a breathing exercise', action: () => router.push('/yoga-breathing') },
  ];

  const handleStartNewChat = () => {
    setActiveConversationId(null);
    setMessages([introSystemMessage]);
  };

  const handleSend = async (overridePrompt?: string) => {
    const textToSend = (overridePrompt || inputText).trim();
    if (!textToSend || isLoading) return;

    const userMsg: UIMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setIsLoading(true);

    try {
      // Build conversation history for API context fallback
      const history: APIChatMessage[] = messages
        .filter((m) => m.sender === 'user' || m.sender === 'ai')
        .map((m) => ({
          role: m.sender === 'user' ? 'user' : 'assistant',
          content: m.text,
        }));

      const res = await aiService.sendMessage({
        message: textToSend,
        conversation_id: activeConversationId || undefined,
        conversation_history: history,
        include_health_context: true,
      });

      if (res.conversation_id) {
        setActiveConversationId(res.conversation_id);
        fetchWellnessContext(res.conversation_id);
      } else {
        fetchWellnessContext(activeConversationId || undefined);
      }

      const replyText = res.reply || res.message || 'Response received.';

      const aiMsg: UIMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: replyText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      let displayMessage = err?.message || 'Sanjeevni AI is temporarily unavailable.';
      if (displayMessage.toLowerCase().includes('cancel') || displayMessage.toLowerCase().includes('abort')) {
        displayMessage = 'Sanjeevni AI request timed out. Please check your network connection and try again.';
      }
      const errorMsg: UIMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'system',
        text: displayMessage,
        timestamp: 'Notice',
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <KeyboardAvoidingView
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 88 : 0}
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerTopRow}>
            <View style={styles.aiBadge}>
              <Ionicons name="sparkles" size={14} color={colors.primary} />
              <Text style={styles.aiBadgeText}>Mistral Wellness Intelligence</Text>
            </View>
            
            {/* Authoritative Multimodal Wellness Status Badge */}
            {wellnessContext && (
              <View
                style={[
                  styles.wellnessStatusBadge,
                  wellnessContext.wellness_concern_level === 'critical_concern'
                    ? styles.badgeCritical
                    : wellnessContext.wellness_concern_level === 'high_concern'
                    ? styles.badgeHigh
                    : wellnessContext.wellness_concern_level === 'elevated_concern'
                    ? styles.badgeElevated
                    : styles.badgeNormal,
                ]}
              >
                <View
                  style={[
                    styles.badgeDot,
                    wellnessContext.wellness_concern_level === 'critical_concern'
                      ? styles.dotCritical
                      : wellnessContext.wellness_concern_level === 'high_concern'
                      ? styles.dotHigh
                      : wellnessContext.wellness_concern_level === 'elevated_concern'
                      ? styles.dotElevated
                      : styles.dotNormal,
                  ]}
                />
                <Text
                  style={[
                    styles.wellnessStatusText,
                    wellnessContext.wellness_concern_level === 'critical_concern'
                      ? styles.textCritical
                      : wellnessContext.wellness_concern_level === 'high_concern'
                      ? styles.textHigh
                      : wellnessContext.wellness_concern_level === 'elevated_concern'
                      ? styles.textElevated
                      : styles.textNormal,
                  ]}
                >
                  {wellnessContext.wellness_concern_level === 'critical_concern'
                    ? 'Critical Concern'
                    : wellnessContext.wellness_concern_level === 'high_concern'
                    ? 'High Concern'
                    : wellnessContext.wellness_concern_level === 'elevated_concern'
                    ? 'Elevated Concern'
                    : 'Normal Wellness'}
                </Text>
              </View>
            )}

            <TouchableOpacity
              activeOpacity={0.8}
              onPress={handleStartNewChat}
              style={styles.newChatButton}
            >
              <Ionicons name="add-circle-outline" size={16} color={colors.primaryDark} />
              <Text style={styles.newChatButtonText}>New Chat</Text>
            </TouchableOpacity>
          </View>
          <Text style={styles.headerTitle}>Sanjeevni AI</Text>
          <Text style={styles.headerSubtitle}>Real-time autonomic biofeedback companion</Text>
        </View>

        {/* Chat Messages */}
        <ScrollView
          ref={scrollViewRef}
          style={styles.messagesList}
          contentContainerStyle={styles.messagesContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Supportive Critical Safety Guidance Banner */}
          {(wellnessContext?.wellness_concern_level === 'critical_concern' ||
            wellnessContext?.conversational_risk_level === 'CRITICAL') && (
            <View style={styles.criticalGuidanceBanner}>
              <View style={styles.criticalHeaderRow}>
                <Ionicons name="heart-dislike-outline" size={20} color="#DC2626" />
                <Text style={styles.criticalTitle}>Supportive Safety Guidance</Text>
              </View>
              <Text style={styles.criticalBody}>
                Sanjeevni has detected significant distress in recent interactions. You don't have to navigate this alone. Please consider checking in with your trusted contact or reaching out for immediate support.
              </Text>
              <View style={styles.criticalActionsRow}>
                <TouchableOpacity
                  style={styles.crisisActionBtn}
                  onPress={() => Alert.alert('Support Helpline', 'Tele-MANAS Helpline: 14416 / 1800-891-4416 (24/7 Toll Free Mental Health Support)')}
                >
                  <Ionicons name="call" size={13} color="#DC2626" />
                  <Text style={styles.crisisActionText}>Tele-MANAS (14416)</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.crisisActionBtn}
                  onPress={() => Alert.alert('Emergency Support', 'National Emergency Response: 112')}
                >
                  <Ionicons name="call" size={13} color="#DC2626" />
                  <Text style={styles.crisisActionText}>Emergency (112)</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.crisisActionBtnSecondary}
                  onPress={() => router.push('/trusted-contact' as any)}
                >
                  <Ionicons name="people" size={13} color={colors.primaryDark} />
                  <Text style={styles.crisisActionTextSecondary}>Trusted Contact</Text>
                </TouchableOpacity>
              </View>
              <Text style={styles.criticalDisclaimer}>
                Sanjeevni is an autonomic wellness companion and does not diagnose mental health conditions.
              </Text>
            </View>
          )}
          {isInitializing && (
            <View style={styles.initLoaderContainer}>
              <ActivityIndicator size="small" color={colors.primary} />
              <Text style={styles.initLoaderText}>Loading chat history...</Text>
            </View>
          )}

          {messages.map((msg) => {
            const isUser = msg.sender === 'user';
            const isSystem = msg.sender === 'system';

            if (isSystem) {
              return (
                <View key={msg.id} style={styles.systemBox}>
                  <Ionicons name="information-circle-outline" size={18} color={colors.primary} style={styles.systemIcon} />
                  <View style={styles.systemTextContainer}>
                    <Text style={styles.systemText}>{msg.text}</Text>
                    <Text style={styles.systemTimestamp}>{msg.timestamp}</Text>
                  </View>
                </View>
              );
            }

            return (
              <View
                key={msg.id}
                style={[
                  styles.messageWrapper,
                  isUser ? styles.messageWrapperUser : styles.messageWrapperAI,
                ]}
              >
                <View
                  style={[
                    styles.bubble,
                    isUser ? styles.bubbleUser : styles.bubbleAI,
                    shadows.card,
                  ]}
                >
                  {isUser ? (
                    <Text style={[styles.bubbleText, styles.bubbleTextUser]}>
                      {msg.text}
                    </Text>
                  ) : (
                    <FormattedText
                      content={msg.text}
                      textColor={colors.textPrimary}
                    />
                  )}
                  <Text style={[styles.timestampText, isUser ? styles.timestampUser : styles.timestampAI]}>
                    {msg.timestamp}
                  </Text>
                </View>
              </View>
            );
          })}

          {isLoading && (
            <View style={[styles.messageWrapper, styles.messageWrapperAI]}>
              <View style={[styles.bubble, styles.bubbleAI, styles.loadingBubble]}>
                <ActivityIndicator size="small" color={colors.primary} />
                <Text style={styles.loadingText}>Sanjeevni AI is contemplating...</Text>
              </View>
            </View>
          )}
        </ScrollView>

        {/* Suggested Quick Action Chips */}
        <View style={styles.promptsContainer}>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.promptsContent}
          >
            {quickPrompts.map((p, idx) => (
              <TouchableOpacity
                key={idx}
                activeOpacity={0.8}
                onPress={() => {
                  if (p.action) {
                    p.action();
                  } else if (p.prompt) {
                    handleSend(p.prompt);
                  }
                }}
                style={styles.promptChip}
              >
                <Text style={styles.promptChipText}>{p.label}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        {/* Input Bar */}
        <View style={styles.inputBar}>
          <TextInput
            style={styles.textInput}
            placeholder="Type a wellness question..."
            placeholderTextColor={colors.textMuted}
            value={inputText}
            onChangeText={setInputText}
            onSubmitEditing={() => handleSend()}
            returnKeyType="send"
            editable={!isLoading}
          />
          <TouchableOpacity
            activeOpacity={0.8}
            onPress={() => handleSend()}
            style={[styles.sendButton, (!inputText.trim() || isLoading) && styles.sendButtonDisabled]}
            disabled={!inputText.trim() || isLoading}
          >
            <Ionicons name="send" size={16} color={colors.textOnPrimary} />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
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
  },
  header: {
    paddingHorizontal: spacing.gutter,
    paddingTop: spacing.sm,
    paddingBottom: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    backgroundColor: colors.surface,
  },
  headerTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  aiBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: colors.primaryTint,
    paddingHorizontal: spacing.sm + 2,
    paddingVertical: 3,
    borderRadius: radii.pill,
  },
  aiBadgeText: {
    fontSize: 11,
    fontWeight: typography.weight.bold,
    color: colors.primaryDark,
    marginLeft: 4,
  },
  newChatButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceSubtle,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing.sm + 2,
    paddingVertical: 3,
    borderRadius: radii.pill,
  },
  newChatButtonText: {
    fontSize: 11,
    fontWeight: typography.weight.medium,
    color: colors.primaryDark,
    marginLeft: 4,
  },
  headerTitle: {
    fontSize: typography.size.xl,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  headerSubtitle: {
    fontSize: typography.size.xs,
    color: colors.textMuted,
  },
  messagesList: {
    flex: 1,
  },
  messagesContent: {
    paddingHorizontal: spacing.gutter,
    paddingVertical: spacing.md,
  },
  initLoaderContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.sm,
    marginBottom: spacing.xs,
  },
  initLoaderText: {
    fontSize: typography.size.xs,
    color: colors.textMuted,
    marginLeft: spacing.xs,
  },
  systemBox: {
    flexDirection: 'row',
    backgroundColor: colors.primaryTint,
    borderWidth: 1,
    borderColor: colors.borderTeal,
    borderRadius: radii.card,
    padding: spacing.md,
    marginBottom: spacing.md,
    alignItems: 'flex-start',
  },
  systemIcon: {
    marginRight: spacing.sm,
    marginTop: 2,
  },
  systemTextContainer: {
    flex: 1,
  },
  systemText: {
    fontSize: typography.size.xs,
    color: colors.primaryDark,
    lineHeight: 18,
  },
  systemTimestamp: {
    fontSize: 10,
    color: colors.textMuted,
    marginTop: 4,
  },
  messageWrapper: {
    flexDirection: 'row',
    marginBottom: spacing.md,
    alignItems: 'flex-end',
  },
  messageWrapperAI: {
    justifyContent: 'flex-start',
  },
  messageWrapperUser: {
    justifyContent: 'flex-end',
  },
  bubble: {
    maxWidth: '82%',
    borderRadius: radii.card,
    padding: spacing.md,
  },
  bubbleAI: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderBottomLeftRadius: 4,
  },
  bubbleUser: {
    backgroundColor: colors.primary,
    borderBottomRightRadius: 4,
  },
  bubbleText: {
    fontSize: typography.size.sm,
    lineHeight: 20,
  },
  bubbleTextAI: {
    color: colors.textPrimary,
  },
  bubbleTextUser: {
    color: colors.textOnPrimary,
  },
  timestampText: {
    fontSize: 10,
    marginTop: 4,
    alignSelf: 'flex-end',
  },
  timestampAI: {
    color: colors.textMuted,
  },
  timestampUser: {
    color: colors.primarySubtle,
  },
  loadingBubble: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
  },
  loadingText: {
    fontSize: typography.size.xs,
    color: colors.textMuted,
    marginLeft: spacing.sm,
  },
  promptsContainer: {
    paddingVertical: spacing.xs,
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.borderSubtle,
  },
  promptsContent: {
    paddingHorizontal: spacing.gutter,
  },
  promptChip: {
    backgroundColor: colors.primaryTint,
    borderWidth: 1,
    borderColor: colors.borderTeal,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs + 2,
    borderRadius: radii.pill,
    marginRight: spacing.sm,
  },
  promptChipText: {
    fontSize: typography.size.xs,
    color: colors.primaryDark,
    fontWeight: typography.weight.medium,
  },
  inputBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.gutter,
    paddingVertical: spacing.sm,
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  textInput: {
    flex: 1,
    backgroundColor: colors.surfaceSubtle,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.pill,
    paddingHorizontal: spacing.base,
    paddingVertical: spacing.sm,
    fontSize: typography.size.sm,
    color: colors.textPrimary,
    maxHeight: 100,
  },
  sendButton: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: spacing.sm,
  },
  sendButtonDisabled: {
    backgroundColor: colors.surfaceMuted,
  },
  wellnessStatusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.sm,
    paddingVertical: 3,
    borderRadius: radii.pill,
    borderWidth: 1,
  },
  badgeNormal: {
    backgroundColor: colors.primaryTint,
    borderColor: '#CCFBF1',
  },
  badgeElevated: {
    backgroundColor: '#FEF3C7',
    borderColor: '#FDE68A',
  },
  badgeHigh: {
    backgroundColor: '#FFEDD5',
    borderColor: '#FDBA74',
  },
  badgeCritical: {
    backgroundColor: '#FEE2E2',
    borderColor: '#FECACA',
  },
  badgeDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 4,
  },
  dotNormal: { backgroundColor: colors.primary },
  dotElevated: { backgroundColor: '#D97706' },
  dotHigh: { backgroundColor: '#EA580C' },
  dotCritical: { backgroundColor: '#DC2626' },
  wellnessStatusText: {
    fontSize: 10,
    fontWeight: typography.weight.bold,
  },
  textNormal: { color: colors.primaryDark },
  textElevated: { color: '#B45309' },
  textHigh: { color: '#C2410C' },
  textCritical: { color: '#991B1B' },
  criticalGuidanceBanner: {
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FECACA',
    borderRadius: radii.card,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  criticalHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  criticalTitle: {
    fontSize: typography.size.sm,
    fontWeight: typography.weight.bold,
    color: '#991B1B',
    marginLeft: 6,
  },
  criticalBody: {
    fontSize: 12,
    color: '#7F1D1D',
    lineHeight: 18,
    marginBottom: spacing.sm,
  },
  criticalActionsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginBottom: spacing.xs,
  },
  crisisActionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEE2E2',
    borderWidth: 1,
    borderColor: '#FCA5A5',
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    borderRadius: radii.pill,
  },
  crisisActionText: {
    fontSize: 11,
    fontWeight: typography.weight.bold,
    color: '#991B1B',
    marginLeft: 4,
  },
  crisisActionBtnSecondary: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    borderRadius: radii.pill,
  },
  crisisActionTextSecondary: {
    fontSize: 11,
    fontWeight: typography.weight.medium,
    color: colors.primaryDark,
    marginLeft: 4,
  },
  criticalDisclaimer: {
    fontSize: 10,
    color: colors.textMuted,
    marginTop: 4,
    fontStyle: 'italic',
  },
});
