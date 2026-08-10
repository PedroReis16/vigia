import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:vigia_ui/domain/enums/device_rooms.dart';
import 'package:vigia_ui/domain/helpers/converters.dart';
import 'package:vigia_ui/domain/ui_models/device_ui.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/devices/providers/devices_provider.dart';
import 'package:vigia_ui/presentation/shared/extensions/show_snackbar.dart';
import 'package:vigia_ui/presentation/shared/widgets/form_text_field.dart';

class EditDeviceProperties extends ConsumerStatefulWidget {
  const EditDeviceProperties({
    super.key,
    required this.device,
    required this.returnToPreviousPage,
  });

  final DeviceUIModel device;
  final VoidCallback returnToPreviousPage;

  @override
  ConsumerState<EditDeviceProperties> createState() =>
      _EditDevicePropertiesState();
}

class _EditDevicePropertiesState extends ConsumerState<EditDeviceProperties> {
  late final TextEditingController _nicknameController;
  DeviceRooms? _selectedRoom;
  late bool _isClipsEnabled = false;
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    _nicknameController = TextEditingController(text: widget.device.nickname);
    _nicknameController.addListener(_onFormChanged);
    _selectedRoom = widget.device.room;
    _isClipsEnabled = widget.device.isClipsEnabled;
  }

  @override
  void dispose() {
    _nicknameController.removeListener(_onFormChanged);
    _nicknameController.dispose();
    super.dispose();
  }

  void _onFormChanged() {
    if (mounted) setState(() {});
  }

  bool get _hasUnsavedChanges {
    final nickname = _nicknameController.text.trim();
    final originalNickname = (widget.device.nickname ?? '').trim();
    return nickname != originalNickname ||
        _selectedRoom != widget.device.room ||
        _isClipsEnabled != widget.device.isClipsEnabled;
  }

  bool get _canSave => !_isSaving && _hasUnsavedChanges;

  Future<void> _saveChanges() async {
    if (!_canSave) return;

    FocusScope.of(context).unfocus();
    setState(() => _isSaving = true);

    try {
      final nickname = _nicknameController.text.trim();

      await ref
          .read(devicesProvider.notifier)
          .updateDevice(
            widget.device.id,
            nickname: nickname.isEmpty ? null : nickname,
            room: _selectedRoom,
            isClipsEnabled: _isClipsEnabled,
          );

      if (!mounted) return;

      context.showSnackbar(
        message: context.translations.deviceUpdatedSuccess,
        color: Theme.of(context).colorScheme.primary,
      );
      widget.returnToPreviousPage();
    } catch (_) {
      if (!mounted) return;

      context.showSnackbar(
        message: context.translations.deviceUpdateError,
        color: Theme.of(context).colorScheme.error,
      );
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  Future<void> _handleBack() async {
    if (_isSaving) return;

    FocusManager.instance.primaryFocus?.unfocus();

    if (_hasUnsavedChanges) {
      final shouldDiscard = await showDialog<bool>(
        context: context,
        barrierDismissible: false,
        builder: (context) => AlertDialog(
          title: Text(context.translations.discardChangesTitle),
          content: Text(context.translations.discardChangesMessage),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: Text(context.translations.cancel),
            ),
            TextButton(
              onPressed: () => Navigator.pop(context, true),
              child: Text(context.translations.discard),
            ),
          ],
        ),
      );

      if (shouldDiscard != true || !mounted) return;
    }

    widget.returnToPreviousPage();
  }

  void _dismissKeyboard() {
    FocusManager.instance.primaryFocus?.unfocus();
  }

  @override
  Widget build(BuildContext context) {
    final t = context.translations;
    final theme = Theme.of(context);

    return GestureDetector(
      onTap: _dismissKeyboard,
      behavior: HitTestBehavior.opaque,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Wrap(
              runSpacing: 8,
              alignment: WrapAlignment.start,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                IconButton(
                  onPressed: _handleBack,
                  icon: const Icon(Icons.arrow_back_ios),
                ),
                Text(
                  widget.device.nickname ?? widget.device.name,
                  style: theme.textTheme.titleLarge,
                ),
              ],
            ),
            const SizedBox(height: 8),
            Expanded(
              child: ListView(
                keyboardDismissBehavior:
                    ScrollViewKeyboardDismissBehavior.onDrag,
                padding: const EdgeInsets.only(bottom: 16),
                children: [
                  FormTextField(
                    controller: _nicknameController,
                    label: t.deviceName,
                  ),
                  const SizedBox(height: 16),
                  Text(t.deviceRoom, style: theme.textTheme.labelLarge),
                  const SizedBox(height: 8),
                  DropdownButtonFormField<DeviceRooms>(
                    initialValue: widget.device.room,
                    decoration: InputDecoration(
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    items: DeviceRooms.values
                        .map(
                          (e) => DropdownMenuItem(
                            value: e,
                            alignment: Alignment.center,
                            child: Text(
                              Converters.translateDeviceRoom(context, e),
                            ),
                          ),
                        )
                        .toList(),
                    onChanged: _isSaving
                        ? null
                        : (value) {
                            setState(() {
                              _selectedRoom = value;
                            });
                          },
                  ),
                  const SizedBox(height: 8),
                  SwitchListTile(
                    contentPadding: EdgeInsets.zero,
                    title: Wrap(
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: [
                        Text(t.saveClips),
                        IconButton(
                          onPressed: () {
                            _dismissKeyboard();
                            showModalBottomSheet(
                              context: context,
                              builder: (context) => SizedBox(
                                width: double.infinity,
                                height: 200,
                                child: Padding(
                                  padding: const EdgeInsets.all(16),
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Row(
                                        mainAxisAlignment:
                                            MainAxisAlignment.spaceBetween,
                                        children: [
                                          Text(
                                            t.whatAreClips,
                                            style: theme.textTheme.titleMedium,
                                          ),
                                          IconButton(
                                            onPressed: () =>
                                                Navigator.pop(context),
                                            icon: const Icon(Icons.close),
                                          ),
                                        ],
                                      ),
                                      const SizedBox(height: 16),
                                      Expanded(
                                        child: Text(
                                          t.whenEnabledClipsWillStoreClipsForAnalysis,
                                          textAlign: TextAlign.justify,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            );
                          },
                          icon: const Icon(Icons.info_outline),
                        ),
                      ],
                    ),
                    value: _isClipsEnabled,
                    onChanged: _isSaving
                        ? null
                        : (value) {
                            setState(() {
                              _isClipsEnabled = value;
                            });
                          },
                  ),
                ],
              ),
            ),
            SafeArea(
              top: false,
              child: Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: SizedBox(
                  width: double.infinity,
                  child: FilledButton(
                    onPressed: _canSave ? _saveChanges : null,
                    child: _isSaving
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : Text(t.saveChanges),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
