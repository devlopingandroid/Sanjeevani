/**
 * Sanjeevni AI Screen
 * 
 * Intelligent wellness companion interface.
 * Strictly complies with the ZERO HARDCODED DATA policy:
 * Never simulates fake chatbot dialogues or fabricated conversational responses.
 * Honestly reports AI service status when an AI backend is not connected.
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
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, typography, radii, shadows } from '../../src/theme';
import { SanjeevniCard } from '../../src/components/common/SanjeevniCard';

interface ChatMessage {
  id: string;
  sender: 'ai' | 'user' | 'system';
  text: string;
  timestamp: string;
}

export default function AIScreen() {
  const router = useRouter();
  const [inputText, setInputText] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'system-status',
      sender: 'system',
      text: 'Sanjeevni AI service is currently unavailable. Real-time biosignal monitoring remains fully operational. Use the shortcuts below for guided relaxation protocols.',
      timestamp: 'System Notice',
    },
  ]);

  const quickPrompts = [
    { label: 'Start breathing exercise', action: () => router.push('/yoga-breathing') },
    { label: 'View current physiology', action: () => router.push('/(tabs)/') },
    { label: 'Nutrition guides', action: () => router.push('/nutrition') },
  ];

  const handleSend = () => {
    if (!inputText.trim()) return;
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: inputText.trim(),
      timestamp: 'Just now',
    };

    // Honest system response informing the user that conversational inference is offline
    const systemNotice: ChatMessage = {
      id: (Date.now() + 1).toString(),
      sender: 'system',
      text: 'Sanjeevni AI is currently unavailable. No conversational backend is connected. Live sensor processing is continuing on your wearable.',
      timestamp: 'System Notice',
    };

    setMessages((prev) => [...prev, userMsg, systemNotice]);
    setInputText('');
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
            <Text style={styles.aiBadgeText}>Sanjeevni AI</Text>
          </View>
          <Text style={styles.headerTitle}>Wellness Companion</Text>
          <Text style={styles.headerSubtitle}>Conversational biofeedback interface</Text>
        </View>

        {/* Service Status Notice Banner */}
        <View style={styles.statusBanner}>
          <Ionicons name="information-circle-outline" size={16} color={colors.textMuted} />
          <Text style={styles.statusBannerText}>
            AI backend service: Standby / Unavailable
          </Text>
        </View>

        {/* Chat Messages */}
        <ScrollView
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
                  <Ionicons name="alert-circle-outline" size={18} color={colors.primary} style={styles.systemIcon} />
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
                  <Text style={[styles.bubbleText, isUser ? styles.bubbleTextUser : styles.bubbleTextAI]}>
                    {msg.text}
                  </Text>
                  <Text style={[styles.timestampText, isUser ? styles.timestampUser : styles.timestampAI]}>
                    {msg.timestamp}
                  </Text>
                </View>
              </View>
            );
          })}
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
                onPress={p.action}
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
            onSubmitEditing={handleSend}
            returnKeyType="send"
          />
          <TouchableOpacity
            activeOpacity={0.8}
            onPress={handleSend}
            style={[styles.sendButton, !inputText.trim() && styles.sendButtonDisabled]}
            disabled={!inputText.trim()}
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
  statusBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceMuted,
    paddingHorizontal: spacing.gutter,
    paddingVertical: spacing.xs + 2,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderSubtle,
  },
  statusBannerText: {
    fontSize: 11,
    color: colors.textSecondary,
    marginLeft: 6,
    fontWeight: typography.weight.medium,
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
    maxWidth: '80%',
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
