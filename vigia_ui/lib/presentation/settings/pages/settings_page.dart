import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:vigia_ui/domain/enums/error_codes.dart';
import 'package:vigia_ui/domain/exceptions/request_exception.dart';
import 'package:vigia_ui/l10n/app_localizations.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/settings/providers/user_profile_provider.dart';
import 'package:vigia_ui/presentation/settings/widgets/account_profile_card.dart';
import 'package:vigia_ui/presentation/settings/widgets/profile_picture_source_sheet.dart';
import 'package:vigia_ui/presentation/settings/widgets/profile_plan_card.dart';
import 'package:vigia_ui/presentation/settings/widgets/settings_section.dart';
import 'package:vigia_ui/presentation/settings/widgets/settings_tile.dart';
import 'package:vigia_ui/presentation/shell/auth_transition_warm_up.dart';
import 'package:vigia_ui/presentation/user/providers/auth_exit_transition_provider.dart';
import 'package:vigia_ui/presentation/user/providers/auth_session_provider.dart';

class SettingsPage extends ConsumerStatefulWidget {
  const SettingsPage({super.key});

  @override
  ConsumerState<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends ConsumerState<SettingsPage> {
  static const _padding = EdgeInsets.fromLTRB(16, 16, 16, 24);
  static const _maxPictureBytes = 2 * 1024 * 1024;

  final ImagePicker _picker = ImagePicker();
  var _saving = false;

  @override
  Widget build(BuildContext context) {
    final t = context.translations;
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final profile = ref.watch(userProfileProvider);

    return Scaffold(
      body: ListView(
        padding: _padding,
        children: [
          profile.when(
            data: (user) => Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                AccountProfileCard(
                  profile: user,
                  saving: _saving,
                  onChangePicture: _changePicture,
                  onRemovePicture: _removePicture,
                  onSave: _saveProfile,
                  onDeleteAccount: _deleteAccount,
                ),
                const SizedBox(height: 24),
                const ProfilePlanCard(),
              ],
            ),
            loading: () => Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(t.profileTitle, style: theme.textTheme.titleLarge),
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 48),
                  child: Center(child: CircularProgressIndicator()),
                ),
              ],
            ),
            error: (_, _) => Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(t.profileTitle, style: theme.textTheme.titleLarge),
                const SizedBox(height: 24),
                Text(t.profileLoadError),
              ],
            ),
          ),
          const SizedBox(height: 24),
          SettingsSection(
            title: t.session,
            children: [
              SettingsTile(
                icon: Icons.logout_rounded,
                title: t.logout,
                iconColor: colorScheme.error,
                titleColor: colorScheme.error,
                trailing: const SizedBox.shrink(),
                onTap: () => _signOut(context, ref),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Future<bool> _saveProfile(
    String firstName,
    String lastName,
    String phone,
  ) async {
    final t = context.translations;
    setState(() => _saving = true);
    try {
      await ref
          .read(userProfileProvider.notifier)
          .save(firstName: firstName, lastName: lastName, phone: phone);
      if (!mounted) return false;
      _showMessage(t.profileSaved);
      return true;
    } catch (error) {
      if (!mounted) return false;
      _showMessage(_saveMessage(t, error));
      return false;
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _deleteAccount() async {
    final t = context.translations;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(t.profileDeleteTitle),
        content: Text(t.profileDeleteMessage),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: Text(t.cancel),
          ),
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: Text(t.profileDeleteConfirm),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;

    setState(() => _saving = true);
    try {
      await ref.read(userProfileProvider.notifier).delete();
      if (!mounted) return;
      await _signOut(context, ref);
    } catch (error) {
      if (!mounted) return;
      _showMessage(_deleteMessage(t, error));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _changePicture() async {
    final t = context.translations;
    final source = await showProfilePictureSourceSheet(context);
    if (source == null || !mounted) return;

    final XFile? image;
    try {
      image = await _picker.pickImage(source: source);
    } catch (_) {
      if (!mounted) return;
      _showMessage(t.profilePictureError);
      return;
    }
    if (image == null || !mounted) return;

    final bytes = await image.readAsBytes();
    final contentType = _contentType(image);
    if (contentType == null ||
        bytes.isEmpty ||
        bytes.length > _maxPictureBytes) {
      _showMessage(t.profilePictureInvalid);
      return;
    }

    setState(() => _saving = true);
    try {
      await ref
          .read(userProfileProvider.notifier)
          .upload(bytes, image.name, contentType);
    } catch (error) {
      if (!mounted) return;
      _showMessage(_pictureMessage(t, error));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<bool> _removePicture() async {
    final t = context.translations;
    setState(() => _saving = true);
    try {
      await ref.read(userProfileProvider.notifier).remove();
      return true;
    } catch (error) {
      if (!mounted) return false;
      _showMessage(_pictureMessage(t, error));
      return false;
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  String? _contentType(XFile image) {
    final mime = image.mimeType?.toLowerCase();
    if (mime == 'image/jpeg' || mime == 'image/png' || mime == 'image/webp') {
      return mime;
    }

    final name = image.name.toLowerCase();
    if (name.endsWith('.png')) return 'image/png';
    if (name.endsWith('.webp')) return 'image/webp';
    if (name.endsWith('.jpg') || name.endsWith('.jpeg')) return 'image/jpeg';
    return null;
  }

  String _pictureMessage(AppLocalizations t, Object error) {
    if (error is RequestException &&
        (error.errorCode == ErrorCodes.invalidProfilePicture ||
            error.errorCode == ErrorCodes.profilePictureTooLarge)) {
      return t.profilePictureInvalid;
    }
    return t.profilePictureError;
  }

  String _saveMessage(AppLocalizations t, Object error) {
    if (error is RequestException &&
        error.errorCode == ErrorCodes.invalidProfileName) {
      return t.profileNameInvalid;
    }
    if (error is RequestException &&
        error.errorCode == ErrorCodes.invalidProfilePhone) {
      return t.profilePhoneInvalid;
    }
    return t.profileSaveError;
  }

  String _deleteMessage(AppLocalizations t, Object error) {
    if (error is RequestException &&
        error.errorCode == ErrorCodes.accountDeleteForbidden) {
      return t.profileDeleteForbidden;
    }
    return t.profileDeleteError;
  }

  void _showMessage(String message) {
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _signOut(BuildContext context, WidgetRef ref) async {
    await AuthTransitionWarmUp.precacheLogos(context);
    if (!context.mounted) return;
    ref.read(authExitTransitionProvider.notifier).armLogout();
    try {
      await ref.read(authSessionProvider.notifier).signOut();
    } catch (_) {
      ref.read(authExitTransitionProvider.notifier).disarm();
    }
  }
}
