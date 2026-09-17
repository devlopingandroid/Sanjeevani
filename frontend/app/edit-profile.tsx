/**
 * Edit My Profile Screen
 * 
 * Allows authenticated user to update their real name and profile avatar.
 * Backed by FastAPI PATCH /api/v1/users/me and POST /api/v1/users/me/avatar.
 * Strictly adheres to NO-MOCK-DATA policy and preserves Sanjeevni teal/white aesthetic.
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Image,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import { useAuth } from '../src/context/AuthContext';
import { authService } from '../src/services/authService';
import { resolveAvatarUrl, getUserInitials } from '../src/utils/avatar';
import { colors, spacing, typography, radii, shadows } from '../src/theme';
import { SanjeevniCard } from '../src/components/common/SanjeevniCard';

export default function EditProfileScreen() {
  const router = useRouter();
  const { user, updateUser, refreshUser } = useAuth();

  const [fullName, setFullName] = useState<string>(user?.full_name || '');
  const [selectedImageUri, setSelectedImageUri] = useState<string | null>(null);
  const [selectedImageMime, setSelectedImageMime] = useState<string | null>(null);
  const [selectedImageName, setSelectedImageName] = useState<string | null>(null);
  const [imageLoadError, setImageLoadError] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const initials = getUserInitials(fullName || user?.full_name, user?.email);
  const currentAvatarUrl = selectedImageUri || resolveAvatarUrl(user?.profile_image_url);

  const handlePickFromGallery = async () => {
    try {
      const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!permission.granted) {
        Alert.alert(
          'Permission Required',
          'Please grant access to your photo gallery to select a profile photo.'
        );
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.8,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const asset = result.assets[0];
        setSelectedImageUri(asset.uri);
        setSelectedImageMime(asset.mimeType || null);
        setSelectedImageName(asset.fileName || null);
        setImageLoadError(false);
        setErrorMessage(null);
      }
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Photo permission is required to choose a profile picture.');
    }
  };

  const handleTakePhoto = async () => {
    try {
      const permission = await ImagePicker.requestCameraPermissionsAsync();
      if (!permission.granted) {
        Alert.alert(
          'Permission Required',
          'Photo permission is required to choose a profile picture.'
        );
        return;
      }

      const result = await ImagePicker.launchCameraAsync({
        mediaTypes: ['images'],
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.8,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const asset = result.assets[0];
        setSelectedImageUri(asset.uri);
        setSelectedImageMime(asset.mimeType || null);
        setSelectedImageName(asset.fileName || null);
        setImageLoadError(false);
        setErrorMessage(null);
      }
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Unable to access camera.');
    }
  };

  const handleChangePhotoPress = () => {
    Alert.alert(
      'Change Profile Photo',
      'Select an option to update your profile photo:',
      [
        { text: 'Choose from Gallery', onPress: handlePickFromGallery },
        { text: 'Take Photo', onPress: handleTakePhoto },
        { text: 'Cancel', style: 'cancel' },
      ]
    );
  };

  const handleSaveChanges = async () => {
    const trimmedName = fullName.trim();
    if (!trimmedName) {
      setErrorMessage('Full name cannot be empty.');
      return;
    }

    setIsSaving(true);
    setErrorMessage(null);

    try {
      let updatedProfile = user;

      // 1. If a new photo was chosen, upload it to the backend
      if (selectedImageUri) {
        try {
          updatedProfile = await authService.uploadAvatar(
            selectedImageUri,
            selectedImageMime || undefined,
            selectedImageName || undefined
          );
        } catch (uploadErr: any) {
          console.error('[EditProfile] Avatar upload failed:', uploadErr);
          setIsSaving(false);
          const isUnavailable = uploadErr?.statusCode === 503;
          const userMsg = isUnavailable
            ? 'Profile photo service is currently unavailable.'
            : (uploadErr?.message || 'Unable to update profile photo. Please try again.');
          setErrorMessage(userMsg);
          return;
        }
      }

      // 2. If name changed, send PATCH /users/me
      if (trimmedName !== user?.full_name) {
        try {
          updatedProfile = await authService.updateProfile({ full_name: trimmedName });
        } catch (nameErr: any) {
          console.error('[EditProfile] Name update failed:', nameErr);
          setIsSaving(false);
          setErrorMessage('Unable to save profile changes. Please try again.');
          return;
        }
      }

      // 3. Immediately reflect changes in AuthContext and persistent storage
      if (updatedProfile) {
        await updateUser(updatedProfile);
      } else {
        await refreshUser();
      }

      Alert.alert('Success', 'Profile updated successfully.', [
        {
          text: 'OK',
          onPress: () => router.back(),
        },
      ]);
    } catch (err: any) {
      console.error('[EditProfile] Unexpected error:', err);
      setErrorMessage(err.message || 'Unable to save profile changes. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity
            onPress={() => router.back()}
            style={styles.backButton}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Edit My Profile</Text>
          <View style={{ width: 24 }} />
        </View>

        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* Avatar Section */}
          <View style={styles.avatarSection}>
            <TouchableOpacity
              activeOpacity={0.8}
              onPress={handleChangePhotoPress}
              style={styles.avatarWrapper}
            >
              {!imageLoadError && currentAvatarUrl ? (
                <Image
                  source={{ uri: currentAvatarUrl }}
                  style={styles.avatarImage}
                  resizeMode="cover"
                  onError={() => setImageLoadError(true)}
                />
              ) : (
                <View style={styles.initialsContainer}>
                  <Text style={styles.initialsText}>{initials}</Text>
                </View>
              )}
              <View style={styles.cameraBadge}>
                <Ionicons name="camera" size={16} color={colors.textOnPrimary} />
              </View>
            </TouchableOpacity>

            <TouchableOpacity
              activeOpacity={0.7}
              onPress={handleChangePhotoPress}
              style={styles.changePhotoBtn}
            >
              <Ionicons name="image-outline" size={16} color={colors.primary} />
              <Text style={styles.changePhotoText}>Change Photo</Text>
            </TouchableOpacity>
          </View>

          {/* Form Card */}
          <SanjeevniCard style={styles.formCard}>
            {errorMessage ? (
              <View style={styles.errorBanner}>
                <Ionicons name="alert-circle" size={18} color="#EF4444" />
                <Text style={styles.errorBannerText}>{errorMessage}</Text>
              </View>
            ) : null}

            {/* Full Name Field */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Full Name</Text>
              <View style={styles.inputContainer}>
                <Ionicons
                  name="person-outline"
                  size={20}
                  color={colors.primary}
                  style={styles.inputIcon}
                />
                <TextInput
                  style={styles.textInput}
                  value={fullName}
                  onChangeText={(text) => {
                    setFullName(text);
                    if (errorMessage) setErrorMessage(null);
                  }}
                  placeholder="Enter your full name"
                  placeholderTextColor={colors.textMuted}
                  autoCapitalize="words"
                  autoCorrect={false}
                  editable={!isSaving}
                />
                {fullName.length > 0 && !isSaving ? (
                  <TouchableOpacity onPress={() => setFullName('')}>
                    <Ionicons name="close-circle" size={18} color={colors.textMuted} />
                  </TouchableOpacity>
                ) : null}
              </View>
            </View>

            {/* Email Field (Read-only) */}
            <View style={styles.inputGroup}>
              <View style={styles.labelRow}>
                <Text style={styles.inputLabel}>Email Address</Text>
                <View style={styles.readOnlyBadge}>
                  <Ionicons name="lock-closed" size={10} color={colors.textMuted} />
                  <Text style={styles.readOnlyText}>Read-Only</Text>
                </View>
              </View>
              <View style={[styles.inputContainer, styles.readOnlyInput]}>
                <Ionicons
                  name="mail-outline"
                  size={20}
                  color={colors.textMuted}
                  style={styles.inputIcon}
                />
                <TextInput
                  style={[styles.textInput, styles.readOnlyTextInput]}
                  value={user?.email || ''}
                  editable={false}
                />
              </View>
              <Text style={styles.helperText}>
                Email address is permanently bound to your verified authentication credentials.
              </Text>
            </View>
          </SanjeevniCard>

          {/* Action Buttons */}
          <TouchableOpacity
            activeOpacity={0.8}
            onPress={handleSaveChanges}
            disabled={isSaving}
            style={[styles.saveButton, isSaving && styles.saveButtonDisabled]}
          >
            {isSaving ? (
              <ActivityIndicator size="small" color={colors.textOnPrimary} />
            ) : (
              <>
                <Ionicons name="checkmark-sharp" size={18} color={colors.textOnPrimary} />
                <Text style={styles.saveButtonText}>Save Changes</Text>
              </>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            activeOpacity={0.7}
            onPress={() => router.back()}
            disabled={isSaving}
            style={styles.cancelButton}
          >
            <Text style={styles.cancelButtonText}>Cancel / Back</Text>
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.gutter,
    paddingVertical: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderSubtle,
    backgroundColor: colors.surface,
  },
  backButton: {
    padding: spacing.xs,
  },
  headerTitle: {
    fontSize: typography.size.lg,
    fontWeight: typography.weight.bold,
    color: colors.textPrimary,
  },
  scrollContent: {
    paddingHorizontal: spacing.gutter,
    paddingTop: spacing.lg,
    paddingBottom: spacing.xxl,
  },
  avatarSection: {
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  avatarWrapper: {
    position: 'relative',
    width: 104,
    height: 104,
    borderRadius: 52,
    borderWidth: 3,
    borderColor: colors.primaryTint,
    ...shadows.card,
  },
  avatarImage: {
    width: 98,
    height: 98,
    borderRadius: 49,
  },
  initialsContainer: {
    width: 98,
    height: 98,
    borderRadius: 49,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  initialsText: {
    color: colors.textOnPrimary,
    fontSize: 34,
    fontWeight: typography.weight.bold,
  },
  cameraBadge: {
    position: 'absolute',
    bottom: 2,
    right: 2,
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: colors.primaryDark,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: colors.surface,
  },
  changePhotoBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: spacing.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    backgroundColor: colors.primaryTint,
    borderRadius: radii.pill,
  },
  changePhotoText: {
    fontSize: typography.size.xs,
    fontWeight: typography.weight.semibold,
    color: colors.primaryDark,
    marginLeft: 6,
  },
  formCard: {
    marginBottom: spacing.xl,
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEE2E2',
    borderWidth: 1,
    borderColor: '#FECACA',
    borderRadius: radii.card,
    padding: spacing.md,
    marginBottom: spacing.lg,
  },
  errorBannerText: {
    flex: 1,
    fontSize: typography.size.xs,
    color: '#DC2626',
    marginLeft: spacing.sm,
    fontWeight: typography.weight.medium,
  },
  inputGroup: {
    marginBottom: spacing.lg,
  },
  labelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.xs,
  },
  inputLabel: {
    fontSize: typography.size.sm,
    fontWeight: typography.weight.semibold,
    color: colors.textPrimary,
    marginBottom: spacing.xs,
  },
  readOnlyBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surfaceMuted,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: radii.pill,
  },
  readOnlyText: {
    fontSize: 10,
    color: colors.textMuted,
    marginLeft: 4,
    fontWeight: typography.weight.medium,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderWidth: 1.5,
    borderColor: colors.borderSubtle,
    borderRadius: radii.card,
    paddingHorizontal: spacing.md,
    height: 48,
  },
  readOnlyInput: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.borderSubtle,
  },
  inputIcon: {
    marginRight: spacing.sm,
  },
  textInput: {
    flex: 1,
    fontSize: typography.size.sm,
    color: colors.textPrimary,
  },
  readOnlyTextInput: {
    color: colors.textMuted,
  },
  helperText: {
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 6,
    lineHeight: 15,
  },
  saveButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.primary,
    borderRadius: radii.button,
    paddingVertical: spacing.md,
    ...shadows.button,
  },
  saveButtonDisabled: {
    opacity: 0.6,
  },
  saveButtonText: {
    color: colors.textOnPrimary,
    fontSize: typography.size.base,
    fontWeight: typography.weight.bold,
    marginLeft: spacing.xs,
  },
  cancelButton: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.md,
    marginTop: spacing.sm,
  },
  cancelButtonText: {
    color: colors.textMuted,
    fontSize: typography.size.sm,
    fontWeight: typography.weight.semibold,
  },
});
