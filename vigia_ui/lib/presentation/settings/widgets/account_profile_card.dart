import 'package:flutter/material.dart';
import 'package:vigia_ui/domain/DTOs/user_profile.dart';
import 'package:vigia_ui/domain/profile_fields.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/shared/widgets/profile_avatar.dart';

class AccountProfileCard extends StatefulWidget {
  const AccountProfileCard({
    super.key,
    required this.profile,
    required this.onChangePicture,
    required this.onRemovePicture,
    required this.onSave,
    required this.onDeleteAccount,
    this.saving = false,
  });

  final UserProfile profile;
  final VoidCallback onChangePicture;
  final Future<bool> Function() onRemovePicture;
  final Future<bool> Function(String firstName, String lastName, String phone)
  onSave;
  final VoidCallback onDeleteAccount;
  final bool saving;

  @override
  State<AccountProfileCard> createState() => _AccountProfileCardState();
}

class _AccountProfileCardState extends State<AccountProfileCard> {
  static const _avatarSize = 88.0;

  final _firstName = TextEditingController();
  final _lastName = TextEditingController();
  final _phone = TextEditingController();
  var _editing = false;
  var _pendingRemoval = false;

  @override
  void initState() {
    super.initState();
    _firstName.addListener(_onField);
    _lastName.addListener(_onField);
    _phone.addListener(_onField);
  }

  @override
  void didUpdateWidget(covariant AccountProfileCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (_pendingRemoval &&
        widget.profile.pictureUrl != oldWidget.profile.pictureUrl) {
      _pendingRemoval = false;
    }
  }

  @override
  void dispose() {
    _firstName.dispose();
    _lastName.dispose();
    _phone.dispose();
    super.dispose();
  }

  void _onField() {
    if (mounted) setState(() {});
  }

  bool get _fieldsChanged {
    final profile = widget.profile;
    return _firstName.text.trim() != profile.firstName ||
        _lastName.text.trim() != profile.lastName ||
        _phone.text.trim() != profile.phone;
  }

  bool get _canSave {
    final first = _firstName.text.trim();
    final last = _lastName.text.trim();
    final phone = _phone.text.trim();
    if (!isValidProfileName(first) || !isValidProfileName(last)) return false;
    if (!isValidProfilePhone(phone)) return false;
    return _fieldsChanged || _pendingRemoval;
  }

  void _startEdit() {
    if (widget.saving) return;
    _firstName.text = widget.profile.firstName;
    _lastName.text = widget.profile.lastName;
    _phone.text = widget.profile.phone;
    setState(() {
      _editing = true;
      _pendingRemoval = false;
    });
  }

  void _cancelEdit() {
    if (widget.saving) return;
    setState(() {
      _editing = false;
      _pendingRemoval = false;
    });
  }

  void _markRemoval() {
    if (widget.saving) return;
    setState(() => _pendingRemoval = true);
  }

  Future<void> _submit() async {
    if (widget.saving || !_canSave) return;
    var saved = true;
    if (_pendingRemoval) {
      saved = await widget.onRemovePicture();
      if (saved && mounted) setState(() => _pendingRemoval = false);
    }
    if (!saved || !mounted) return;
    if (_fieldsChanged) {
      saved = await widget.onSave(
        _firstName.text.trim(),
        _lastName.text.trim(),
        _phone.text.trim(),
      );
    }
    if (saved && mounted) setState(() => _editing = false);
  }

  @override
  Widget build(BuildContext context) {
    final t = context.translations;
    final theme = Theme.of(context);
    final profile = widget.profile;
    final picture = _pendingRemoval ? null : profile.pictureUrl;
    final canRemove =
        !_pendingRemoval &&
        profile.pictureUrl != null &&
        profile.pictureUrl!.isNotEmpty;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(t.profileTitle, style: theme.textTheme.titleLarge),
            ),
            TextButton(
              key: Key(_editing ? 'profile-cancel' : 'profile-edit'),
              onPressed: widget.saving
                  ? null
                  : (_editing ? _cancelEdit : _startEdit),
              child: Text(_editing ? t.cancel : t.profileEdit),
            ),
          ],
        ),
        const SizedBox(height: 8),
        Card(
          margin: EdgeInsets.zero,
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Center(child: _avatar(theme, picture)),
                const SizedBox(height: 12),
                Text(
                  profile.name,
                  key: const Key('profile-name'),
                  textAlign: TextAlign.center,
                  style: theme.textTheme.titleMedium,
                ),
                if (_editing && canRemove)
                  Center(
                    child: TextButton(
                      key: const Key('profile-remove-picture'),
                      onPressed: widget.saving ? null : _markRemoval,
                      style: TextButton.styleFrom(
                        foregroundColor: theme.colorScheme.error,
                      ),
                      child: Text(t.removeProfilePicture),
                    ),
                  ),
                const SizedBox(height: 20),
                if (_editing) ...[
                  _editor(
                    t.profileFirstName,
                    _firstName,
                    const Key('profile-first-name'),
                  ),
                  const SizedBox(height: 16),
                  _editor(
                    t.profileLastName,
                    _lastName,
                    const Key('profile-last-name'),
                  ),
                  const SizedBox(height: 16),
                  _editor(
                    t.profilePhone,
                    _phone,
                    const Key('profile-phone'),
                    keyboardType: TextInputType.phone,
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    key: const Key('profile-email'),
                    initialValue: profile.email,
                    enabled: false,
                    decoration: InputDecoration(labelText: t.email),
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton(
                      key: const Key('profile-save'),
                      onPressed: widget.saving || !_canSave ? null : _submit,
                      child: Text(t.profileSave),
                    ),
                  ),
                ] else ...[
                  _readout(
                    theme,
                    t.profileFirstName,
                    profile.firstName,
                    const Key('profile-first-name'),
                  ),
                  const SizedBox(height: 16),
                  _readout(
                    theme,
                    t.profileLastName,
                    profile.lastName,
                    const Key('profile-last-name'),
                  ),
                  const SizedBox(height: 16),
                  _readout(
                    theme,
                    t.profilePhone,
                    profile.phone,
                    const Key('profile-phone'),
                  ),
                  const SizedBox(height: 16),
                  _readout(
                    theme,
                    t.email,
                    profile.email,
                    const Key('profile-email'),
                  ),
                  if (profile.canDeleteAccount) ...[
                    const SizedBox(height: 20),
                    Divider(height: 1, color: theme.colorScheme.outlineVariant),
                    const SizedBox(height: 16),
                    Text(
                      t.profileDeleteAccount,
                      style: theme.textTheme.titleSmall?.copyWith(
                        color: theme.colorScheme.error,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(t.profileDeleteHint, style: theme.textTheme.bodySmall),
                    const SizedBox(height: 12),
                    OutlinedButton(
                      key: const Key('profile-delete'),
                      onPressed: widget.saving ? null : widget.onDeleteAccount,
                      style: OutlinedButton.styleFrom(
                        foregroundColor: theme.colorScheme.error,
                        side: BorderSide(color: theme.colorScheme.error),
                      ),
                      child: Text(t.profileDeleteAccount),
                    ),
                  ],
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _avatar(ThemeData theme, String? picture) {
    final face = ProfileAvatar(
      name: widget.profile.name,
      email: widget.profile.email,
      pictureUrl: picture,
      size: _avatarSize,
    );
    if (!_editing) return face;

    return Semantics(
      button: true,
      label: context.translations.changeProfilePicture,
      child: InkWell(
        key: const Key('profile-picture-button'),
        onTap: widget.saving ? null : widget.onChangePicture,
        customBorder: const CircleBorder(),
        child: ClipOval(
          child: SizedBox(
            width: _avatarSize,
            height: _avatarSize,
            child: Stack(
              fit: StackFit.expand,
              children: [
                face,
                const Positioned(
                  left: 0,
                  right: 0,
                  bottom: 0,
                  height: _avatarSize * 0.38,
                  child: ColoredBox(
                    color: Color(0x8C000000),
                    child: Icon(
                      Icons.photo_camera_outlined,
                      color: Colors.white,
                      size: 18,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _readout(ThemeData theme, String label, String value, Key key) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: theme.textTheme.labelMedium?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
        const SizedBox(height: 4),
        Text(value.isEmpty ? '—' : value, key: key),
      ],
    );
  }

  Widget _editor(
    String label,
    TextEditingController controller,
    Key key, {
    TextInputType? keyboardType,
  }) {
    return TextFormField(
      key: key,
      controller: controller,
      enabled: !widget.saving,
      keyboardType: keyboardType,
      textCapitalization: keyboardType == TextInputType.phone
          ? TextCapitalization.none
          : TextCapitalization.words,
      decoration: InputDecoration(labelText: label),
    );
  }
}
