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
    _selectedRoom = widget.device.room;
    _isClipsEnabled = widget.device.isClipsEnabled;
  }

  @override
  void dispose() {
    _nicknameController.dispose();
    super.dispose();
  }

  bool get _hasUnsavedChanges =>
      _nicknameController.text != (widget.device.nickname ?? '') ||
      _selectedRoom != widget.device.room ||
      _isClipsEnabled != widget.device.isClipsEnabled;

  Future<void> _saveChanges() async {
    if (_isSaving) return;

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

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.start,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildFormHeader(),
                Expanded(
                  child: Padding(
                    padding: EdgeInsets.only(top: 16),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Padding(
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          child: FormTextField(
                            controller: _nicknameController,
                            label: context.translations.deviceName,
                          ),
                        ),
                        Wrap(
                          children: [
                            Text(context.translations.deviceRoom),
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
                                        Converters.translateDeviceRoom(
                                          context,
                                          e,
                                        ),
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
                          ],
                        ),
                        Padding(
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          child: SwitchListTile(
                            title: Wrap(
                              crossAxisAlignment: WrapCrossAlignment.center,
                              children: [
                                Text(context.translations.saveClips),
                                IconButton(
                                  onPressed: () => showModalBottomSheet(
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
                                                  MainAxisAlignment
                                                      .spaceBetween,
                                              children: [
                                                Text(
                                                  context
                                                      .translations
                                                      .whatAreClips,
                                                  style: Theme.of(
                                                    context,
                                                  ).textTheme.titleMedium,
                                                ),
                                                IconButton(
                                                  onPressed: () =>
                                                      Navigator.pop(context),
                                                  icon: Icon(Icons.close),
                                                ),
                                              ],
                                            ),
                                            const SizedBox(height: 16),
                                            Expanded(
                                              child: Text(
                                                context
                                                    .translations
                                                    .whenEnabledClipsWillStoreClipsForAnalysis,
                                                textAlign: TextAlign.justify,
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                    ),
                                  ),
                                  icon: Icon(Icons.info_outline),
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
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
          SizedBox(
            width: double.infinity,
            child: TextButton(
              onPressed: _isSaving ? null : _saveChanges,
              child: _isSaving
                  ? const SizedBox(
                      height: 22,
                      width: 22,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Text(
                      context.translations.saveChanges,
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFormHeader() {
    return Wrap(
      crossAxisAlignment: WrapCrossAlignment.center,
      runAlignment: WrapAlignment.start,
      spacing: 8,
      children: [
        IconButton(
          onPressed: _handleBack,
          icon: Icon(Icons.arrow_back_ios, size: 16),
          style: IconButton.styleFrom(
            padding: EdgeInsets.zero,
            minimumSize: Size.zero,
            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
          ),
        ),
        Text(
          widget.device.nickname ?? widget.device.name,
          style: Theme.of(context).textTheme.titleMedium,
        ),
      ],
    );
  }
}
