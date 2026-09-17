/**
 * Chat Consultation Screen (Demo Mode)
 * 
 * Provides a text-based consultation interface demo.
 * Clearly displays honest demo notice and avoids fake doctor auto-replies.
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
import { useLocalSearchParams, useRouter } from 'expo-router';
import { colors, spacing, typography, radii, shadows } from '../src/theme';
import { getDemoProfessionalById } from '../src/data/demoProfessionals';

interface ChatMessage {
  id: string;
  sender: 'user' | 'system';
  text: string;
  timestamp: string;
}

export default function ConsultChatScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id?: string }>();
  const professional = getDemoProfessionalById(id);

  const [inputText, setInputText] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'init-msg',
      sender: 'system',
      text: `Demo consultation session initiated with ${professional.name}. Messaging system is in demonstration mode.`,
      timestamp: 'Just now',
    },
  ]);

  const sendMessage = () => {
    if (!inputText.trim()) return;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      text: inputText.trim(),
      timestamp: 'Just now',
    };

    const systemNotice: ChatMessage = {
      id: `sys-${Date.now() + 1}`,
      sender: 'system',
      text: 'Demo message composed. Professional messaging system is not connected.',
      timestamp: 'Just now',
    };

    setMessages((prev) => [...prev, userMsg, systemNotice]);
    setInputText('');
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['bottom']}>
      <KeyboardAvoidingView
        style={styles.keyboardContainer}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        {/* Header Professional Bar */}
        <View style={styles.headerBar}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backBtn}>
            <Ionicons name="chevron-back" size={24} color={colors.textPrimary} />
          </TouchableOpacity>
          <View style={styles.headerTitleBox}>
            <Text style={styles.headerName}>{professional.name}</Text>
            <Text style={styles.headerSpec}>{professional.specialization}</Text>
          </View>
          <View style={styles.demoBadge}>
            <Text style={styles.demoBadgeText}>Demo</Text>
          </View>
        </View>

        {/* Demo Notice Banner */}
        <View style={styles.demoNoticeBanner}>
          <Ionicons name="information-circle-outline" size={16} color="#0369A1" />
          <Text style={styles.demoNoticeText}>
            Demo consultation — Professional messaging is not connected yet.
          </Text>
        </View>

        {/* Messages Scroll Area */}
        <ScrollView
          style={styles.messageScroll}
          contentContainerStyle={styles.messageContent}
          showsVerticalScrollIndicator={false}
        >
          {messages.map((msg) => {
            if (msg.sender === 'system') {
              return (
                <View key={msg.id} style={styles.systemMessageContainer}>
                  <Ionicons name="alert-circle-outline" size={14} color={colors.textMuted} />
                  <Text style={styles.systemMessageText}>{msg.text}</Text>
                </View>
              );
            }

            return (
              <View key={msg.id} style={styles.userMessageBubble}>
                <Text style={styles.userMessageText}>{msg.text}</Text>
                <Text style={styles.userMessageTime}>{msg.timestamp}</Text>
              </View>
            );
          })}
        </ScrollView>

        {/* Message Input Composer */}
        <View style={styles.composerContainer}>
          <TextInput
            style={styles.inputField}
            placeholder="Type your message for demo..."
            placeholderTextColor={colors.textMuted}
            value={inputText}
            onChangeText={setInputText}
            multiline
          />
          <TouchableOpacity
            style={[styles.sendBtn, !inputText.trim() && styles.sendBtnDisabled]}
            activeOpacity={0.8}
            onPress={sendMessage}
            disabled={!inputText.trim()}
          >
            <Ionicons name="send" size={18} color="#FFFFFF" />
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
  keyboardContainer: {
    flex: 1,
  },
  headerBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.gutter,
    paddingVertical: spacing.sm,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderSubtle,
  },
  backBtn: {
    paddingRight: spacing.sm,
  },
  headerTitleBox: {
    flex: 1,
  },
  headerName: {
    fontSize: typography.size.sm + 1,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  headerSpec: {
    fontSize: 10,
    color: colors.textMuted,
    marginTop: 1,
  },
  demoBadge: {
    backgroundColor: colors.primaryTint,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radii.pill,
  },
  demoBadgeText: {
    fontSize: 9,
    fontWeight: typography.weight.bold,
    color: colors.primaryDark,
  },
  demoNoticeBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E0F2FE',
    paddingHorizontal: spacing.gutter,
    paddingVertical: spacing.xs + 2,
  },
  demoNoticeText: {
    flex: 1,
    fontSize: 11,
    fontWeight: typography.weight.medium,
    color: '#0369A1',
    marginLeft: 6,
  },
  messageScroll: {
    flex: 1,
  },
  messageContent: {
    padding: spacing.gutter,
    paddingBottom: spacing.lg,
  },
  systemMessageContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surfaceMuted,
    borderRadius: radii.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    marginVertical: spacing.xs + 2,
    alignSelf: 'center',
  },
  systemMessageText: {
    fontSize: 11,
    color: colors.textMuted,
    marginLeft: 4,
    textAlign: 'center',
  },
  userMessageBubble: {
    alignSelf: 'flex-end',
    backgroundColor: colors.primary,
    borderRadius: radii.card,
    borderBottomRightRadius: radii.xs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    marginVertical: spacing.xs,
    maxWidth: '80%',
  },
  userMessageText: {
    fontSize: typography.size.xs + 1,
    color: '#FFFFFF',
    lineHeight: 18,
  },
  userMessageTime: {
    fontSize: 9,
    color: 'rgba(255, 255, 255, 0.7)',
    marginTop: 4,
    alignSelf: 'flex-end',
  },
  composerContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.gutter,
    paddingVertical: spacing.sm,
    backgroundColor: colors.surface,
    borderTopWidth: 1,
    borderTopColor: colors.borderSubtle,
  },
  inputField: {
    flex: 1,
    backgroundColor: colors.surfaceMuted,
    borderRadius: radii.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs + 4,
    fontSize: typography.size.xs + 1,
    color: colors.textPrimary,
    maxHeight: 100,
  },
  sendBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: spacing.xs + 2,
  },
  sendBtnDisabled: {
    backgroundColor: colors.border,
  },
});
