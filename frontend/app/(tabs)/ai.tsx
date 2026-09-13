/**
 * Sanjeevni AI Screen
 * 
 * Intelligent autonomic nervous system wellness companion.
 * Real, end-to-end conversation powered strictly through FastAPI backend (/api/v1/ai/chat)
 * which communicates with xAI Grok.
 * 
 * Strictly complies with ZERO HARDCODED DATA policy:
 * - Never invents simulated AI dialogues.
 * - Displays honest error messages if xAI is offline or key unconfigured.
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
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { aiService } from '../../src/services/aiService';
import { ChatMessage as APIChatMessage } from '../../src/api/types';
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
  const [messages, setMessages] = useState<UIMessage[]>([
    {
      id: 'system-intro',
      sender: 'system',
      text: 'Ask Sanjeevni about your health and wellness.',
      timestamp: 'Sanjeevni Assistant',
    },
  ]);

  useEffect(() => {
    scrollViewRef.current?.scrollToEnd({ animated: true });
  }, [messages, isLoading]);

  const quickPrompts = [
    { label: 'How can I manage stress?', prompt: 'How can I manage and lower my stress?' },
    { label: 'Help me sleep better', prompt: 'How can I improve my sleep quality?' },
    { label: 'Explain my wellness data', prompt: 'What can you tell me about my current biometric stress data?' },
    { label: 'Give me a breathing exercise', action: () => router.push('/yoga-breathing') },
  ];


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
      // Build conversation history for API context
      const history: APIChatMessage[] = messages
        .filter((m) => m.sender === 'user' || m.sender === 'ai')
        .map((m) => ({
          role: m.sender === 'user' ? 'user' : 'assistant',
          content: m.text,
        }));

      const res = await aiService.sendMessage({
        message: textToSend,
        conversation_history: history,
        include_health_context: true,
      });

      const replyText = res.reply || res.message || 'Response received.';

      const aiMsg: UIMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: replyText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err: any) {
      // Honest error reporting from backend with zero fake fallbacks
      const errorMsg: UIMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'system',
        text: err.message || 'Sanjeevni AI is temporarily unavailable.',
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
          <View style={styles.aiBadge}>
            <Ionicons name="sparkles" size={16} color={colors.primary} />
            <Text style={styles.aiBadgeText}>Mistral Wellness Intelligence</Text>
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
  aiBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    backgroundColor: colors.primaryTint,
    paddingHorizontal: spacing.sm + 2,
    paddingVertical: 3,
    borderRadius: radii.pill,
    marginBottom: 4,
  },
  aiBadgeText: {
    fontSize: 11,
    fontWeight: typography.weight.bold,
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
});
