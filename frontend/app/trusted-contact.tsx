/**
 * Trusted Contact & Consent Screen
 *
 * Configures voluntary, consent-driven trusted contact for severe/critical distress notifications.
 *
 * Mandatory UI Text:
 * "This contact may be notified when Sanjeevni detects a severe or critical distress situation.
 * Sanjeevni does not diagnose mental health conditions. Normal and elevated concern levels never trigger a notification."
 */
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Switch,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { trustedContactService } from '../src/services/trustedContactService';
import {
  TrustedContactRecord,
  NotificationLevel,
} from '../src/api/types';
import { colors, spacing, typography, radii, shadows } from '../src/theme';
import { SanjeevniCard } from '../src/components/common/SanjeevniCard';

export default function TrustedContactScreen() {
  const router = useRouter();
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [contact, setContact] = useState<TrustedContactRecord | null>(null);

  // Form State
  const [name, setName] = useState<string>('');
  const [phoneNumber, setPhoneNumber] = useState<string>('');
  const [relationship, setRelationship] = useState<string>('');
  const [enabled, setEnabled] = useState<boolean>(true);
  const [consentGiven, setConsentGiven] = useState<boolean>(false);
  const [notificationLevel, setNotificationLevel] = useState<NotificationLevel>(
    NotificationLevel.HIGH_AND_CRITICAL
  );

  useEffect(() => {
    fetchContact();
  }, []);

  const fetchContact = async () => {
    setLoading(true);
    try {
      const data = await trustedContactService.getTrustedContact();
      if (data) {
        setContact(data);
        setName(data.name);
        setPhoneNumber(data.phone_number);
        setRelationship(data.relationship || '');
        setEnabled(data.enabled);
        setConsentGiven(data.consent_given);
        setNotificationLevel(data.notification_level);
      }
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to load trusted contact.');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!name.trim()) {
      Alert.alert('Validation Error', 'Please enter a valid name for your contact.');
      return;
    }

    const phoneRegex = /^\+?[0-9\s\-()]{7,20}$/;
    if (!phoneNumber.trim() || !phoneRegex.test(phoneNumber.trim())) {
      Alert.alert('Validation Error', 'Please enter a valid phone number (7-20 digits).');
      return;
    }

    if (!consentGiven) {
      Alert.alert(
        'Consent Mandatory',
        'You must explicitly provide consent before configuring or enabling a trusted contact.'
      );
      return;
    }

    setSaving(true);
    try {
      if (contact) {
        // Update existing contact
        const updated = await trustedContactService.updateTrustedContact({
          name: name.trim(),
          phone_number: phoneNumber.trim(),
          relationship: relationship.trim() || null,
          enabled,
          consent_given: consentGiven,
          notification_level: notificationLevel,
        });
        setContact(updated);
        Alert.alert('Success', 'Trusted contact settings updated successfully.');
      } else {
        // Create new contact
        const created = await trustedContactService.createTrustedContact({
          name: name.trim(),
          phone_number: phoneNumber.trim(),
          relationship: relationship.trim() || null,
          enabled,
          consent_given: consentGiven,
          notification_level: notificationLevel,
        });
        setContact(created);
        Alert.alert('Success', 'Trusted contact saved successfully.');
      }
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to save trusted contact.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = () => {
    Alert.alert(
      'Remove Trusted Contact',
      'Are you sure you want to remove your trusted contact? They will no longer be notified during distress situations.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: async () => {
            setSaving(true);
            try {
              await trustedContactService.deleteTrustedContact();
              setContact(null);
              setName('');
              setPhoneNumber('');
              setRelationship('');
              setEnabled(true);
              setConsentGiven(false);
              setNotificationLevel(NotificationLevel.HIGH_AND_CRITICAL);
              Alert.alert('Removed', 'Trusted contact has been deleted.');
            } catch (err: any) {
              Alert.alert('Error', err.message || 'Failed to remove trusted contact.');
            } finally {
              setSaving(false);
            }
          },
        },
      ]
    );
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea} edges={['bottom']}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Required Mandatory Disclaimer Card */}
        <View style={styles.disclaimerBanner}>
          <Ionicons name="shield-checkmark" size={24} color={colors.primaryDark} style={styles.disclaimerIcon} />
          <View style={styles.disclaimerTextContainer}>
            <Text style={styles.disclaimerTitle}>Distress Notification Policy</Text>
            <Text style={styles.disclaimerBody}>
              This contact may be notified when Sanjeevni detects a severe or critical distress situation. Sanjeevni does not diagnose mental health conditions. Normal and elevated concern levels never trigger a notification.
            </Text>
          </View>
        </View>

        {/* Contact Form Card */}
        <SanjeevniCard style={styles.card}>
          <Text style={styles.cardHeader}>Trusted Contact Information</Text>
          <Text style={styles.cardSubheader}>
            Voluntarily configure a trusted person to be alerted during high-distress events.
          </Text>

          {/* Name Field */}
          <Text style={styles.label}>Contact Name *</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g. Dr. Priya Sharma / Mom"
            placeholderTextColor={colors.textMuted}
            value={name}
            onChangeText={setName}
          />

          {/* Phone Field */}
          <Text style={styles.label}>Phone Number *</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g. +91 98765 43210"
            placeholderTextColor={colors.textMuted}
            keyboardType="phone-pad"
            value={phoneNumber}
            onChangeText={setPhoneNumber}
          />

          {/* Relationship Field */}
          <Text style={styles.label}>Relationship (Optional)</Text>
          <TextInput
            style={styles.input}
            placeholder="e.g. Parent / Physician / Friend"
            placeholderTextColor={colors.textMuted}
            value={relationship}
            onChangeText={setRelationship}
          />

          {/* Notification Preference Selector */}
          <Text style={styles.label}>Notification Preference *</Text>
          <Text style={styles.helperText}>
            Note: "Normal" and "Elevated" concern levels NEVER trigger notifications under any setting.
          </Text>
          
          <TouchableOpacity
            activeOpacity={0.8}
            onPress={() => setNotificationLevel(NotificationLevel.HIGH_AND_CRITICAL)}
            style={[
              styles.optionCard,
              notificationLevel === NotificationLevel.HIGH_AND_CRITICAL && styles.optionCardSelected,
            ]}
          >
            <Ionicons
              name={
                notificationLevel === NotificationLevel.HIGH_AND_CRITICAL
                  ? 'radio-button-on'
                  : 'radio-button-off'
              }
              size={20}
              color={
                notificationLevel === NotificationLevel.HIGH_AND_CRITICAL
                  ? colors.primaryDark
                  : colors.textMuted
              }
            />
            <View style={styles.optionTextWrapper}>
              <Text style={styles.optionTitle}>High & Critical Situations</Text>
              <Text style={styles.optionSub}>
                Notify contact during both High distress risk and Critical emergencies.
              </Text>
            </View>
          </TouchableOpacity>

          <TouchableOpacity
            activeOpacity={0.8}
            onPress={() => setNotificationLevel(NotificationLevel.CRITICAL_ONLY)}
            style={[
              styles.optionCard,
              notificationLevel === NotificationLevel.CRITICAL_ONLY && styles.optionCardSelected,
            ]}
          >
            <Ionicons
              name={
                notificationLevel === NotificationLevel.CRITICAL_ONLY
                  ? 'radio-button-on'
                  : 'radio-button-off'
              }
              size={20}
              color={
                notificationLevel === NotificationLevel.CRITICAL_ONLY
                  ? colors.primaryDark
                  : colors.textMuted
              }
            />
            <View style={styles.optionTextWrapper}>
              <Text style={styles.optionTitle}>Critical Only</Text>
              <Text style={styles.optionSub}>
                Notify contact strictly during confirmed Critical emergencies only.
              </Text>
            </View>
          </TouchableOpacity>

          {/* Enable / Disable Switch */}
          <View style={styles.switchRow}>
            <View style={styles.switchTextWrapper}>
              <Text style={styles.switchTitle}>Enable Notifications</Text>
              <Text style={styles.switchSub}>
                Temporarily pause or activate trusted contact alerts.
              </Text>
            </View>
            <Switch
              value={enabled}
              onValueChange={setEnabled}
              trackColor={{ false: '#D1D5DB', true: '#99F6E4' }}
              thumbColor={enabled ? colors.primaryDark : '#F3F4F6'}
            />
          </View>

          {/* Mandatory Consent Checkbox */}
          <TouchableOpacity
            activeOpacity={0.8}
            onPress={() => setConsentGiven(!consentGiven)}
            style={styles.consentRow}
          >
            <Ionicons
              name={consentGiven ? 'checkbox' : 'square-outline'}
              size={24}
              color={consentGiven ? colors.primaryDark : colors.textMuted}
            />
            <Text style={styles.consentText}>
              I explicitly consent for Sanjeevni to notify this trusted contact during severe or critical distress situations.
            </Text>
          </TouchableOpacity>

          {/* Submit Action */}
          <TouchableOpacity
            activeOpacity={0.8}
            onPress={handleSave}
            disabled={saving}
            style={[styles.saveBtn, saving && styles.disabledBtn]}
          >
            {saving ? (
              <ActivityIndicator color={colors.textOnPrimary} />
            ) : (
              <>
                <Ionicons name="checkmark-circle" size={20} color={colors.textOnPrimary} />
                <Text style={styles.saveBtnText}>
                  {contact ? 'Update Trusted Contact' : 'Save Trusted Contact'}
                </Text>
              </>
            )}
          </TouchableOpacity>

          {/* Delete Action (if contact exists) */}
          {contact && (
            <TouchableOpacity
              activeOpacity={0.8}
              onPress={handleDelete}
              disabled={saving}
              style={styles.deleteBtn}
            >
              <Ionicons name="trash-outline" size={18} color="#EF4444" />
              <Text style={styles.deleteBtnText}>Remove Trusted Contact</Text>
            </TouchableOpacity>
          )}
        </SanjeevniCard>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
  },
  scrollContent: {
    padding: spacing.gutter,
  },
  disclaimerBanner: {
    flexDirection: 'row',
    backgroundColor: '#F0FDFA',
    borderWidth: 1,
    borderColor: '#CCFBF1',
    borderRadius: radii.card,
    padding: spacing.md,
    marginBottom: spacing.base,
    alignItems: 'flex-start',
  },
  disclaimerIcon: {
    marginRight: spacing.sm,
    marginTop: 2,
  },
  disclaimerTextContainer: {
    flex: 1,
  },
  disclaimerTitle: {
    fontSize: typography.size.sm,
    fontWeight: typography.weight.bold,
    color: colors.primaryDark,
    marginBottom: 4,
  },
  disclaimerBody: {
    fontSize: 12,
    color: colors.textSecondary,
    lineHeight: 18,
  },
  card: {
    padding: spacing.lg,
  },
  cardHeader: {
    fontSize: typography.size.lg,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  cardSubheader: {
    fontSize: typography.size.xs,
    color: colors.textMuted,
    marginTop: 2,
    marginBottom: spacing.md,
  },
  label: {
    fontSize: typography.size.sm,
    fontWeight: typography.weight.semibold,
    color: colors.textPrimary,
    marginTop: spacing.md,
    marginBottom: spacing.xs,
  },
  helperText: {
    fontSize: 11,
    color: colors.textMuted,
    marginBottom: spacing.sm,
  },
  input: {
    backgroundColor: colors.surfaceMuted,
    borderWidth: 1,
    borderColor: colors.borderSubtle,
    borderRadius: radii.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    fontSize: typography.size.sm,
    color: colors.textPrimary,
  },
  optionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceMuted,
    borderWidth: 1,
    borderColor: colors.borderSubtle,
    borderRadius: radii.card,
    padding: spacing.md,
    marginBottom: spacing.sm,
  },
  optionCardSelected: {
    backgroundColor: '#F0FDFA',
    borderColor: colors.primary,
  },
  optionTextWrapper: {
    marginLeft: spacing.sm,
    flex: 1,
  },
  optionTitle: {
    fontSize: typography.size.sm,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  optionSub: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 2,
  },
  switchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: spacing.lg,
    paddingTop: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.borderSubtle,
  },
  switchTextWrapper: {
    flex: 1,
    marginRight: spacing.md,
  },
  switchTitle: {
    fontSize: typography.size.sm,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  switchSub: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 2,
  },
  consentRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginTop: spacing.lg,
    padding: spacing.md,
    backgroundColor: '#FAF5FF',
    borderWidth: 1,
    borderColor: '#E9D5FF',
    borderRadius: radii.card,
  },
  consentText: {
    flex: 1,
    marginLeft: spacing.sm,
    fontSize: 12,
    fontWeight: typography.weight.medium,
    color: colors.textPrimary,
    lineHeight: 18,
  },
  saveBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primary,
    borderRadius: radii.button,
    paddingVertical: spacing.md,
    marginTop: spacing.xl,
  },
  disabledBtn: {
    opacity: 0.6,
  },
  saveBtnText: {
    fontSize: typography.size.md,
    fontWeight: typography.weight.bold,
    color: colors.textOnPrimary,
    marginLeft: spacing.xs,
  },
  deleteBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FEE2E2',
    borderWidth: 1,
    borderColor: '#FECACA',
    borderRadius: radii.button,
    paddingVertical: spacing.sm,
    marginTop: spacing.md,
  },
  deleteBtnText: {
    fontSize: typography.size.sm,
    fontWeight: typography.weight.bold,
    color: '#DC2626',
    marginLeft: spacing.xs,
  },
});
