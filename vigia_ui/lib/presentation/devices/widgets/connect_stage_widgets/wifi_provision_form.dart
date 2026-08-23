import 'package:flutter/material.dart';
import 'package:vigia_ui/data/services/wifi_scan_service.dart';
import 'package:vigia_ui/domain/DTOs/wifi_network.dart';
import 'package:vigia_ui/l10n/l10n_extension.dart';
import 'package:vigia_ui/presentation/shared/extensions/show_snackbar.dart';
import 'package:vigia_ui/presentation/shared/widgets/app_loading_indicator.dart';

class WifiProvisionForm extends StatefulWidget {
  const WifiProvisionForm({
    required this.onSubmit,
    this.isSubmitting = false,
    super.key,
  });

  final Future<void> Function(String ssid, String password) onSubmit;
  final bool isSubmitting;

  @override
  State<WifiProvisionForm> createState() => _WifiProvisionFormState();
}

class _WifiProvisionFormState extends State<WifiProvisionForm> {
  final _wifiScan = WifiScanService();
  final _formKey = GlobalKey<FormState>();
  final _manualSsidController = TextEditingController();
  final _passwordController = TextEditingController();

  List<WifiNetwork> _networks = [];
  WifiNetwork? _selectedNetwork;
  var _loadingNetworks = true;
  var _obscurePassword = true;
  var _submitting = false;
  var _manualEntry = false;
  String? _scanError;

  @override
  void initState() {
    super.initState();
    _manualEntry = !_wifiScan.isScanSupported;
    _loadNetworks();
  }

  @override
  void dispose() {
    _manualSsidController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _loadNetworks() async {
    if (!_wifiScan.isScanSupported) {
      setState(() {
        _loadingNetworks = false;
        _manualEntry = true;
      });
      return;
    }

    setState(() {
      _loadingNetworks = true;
      _scanError = null;
      _selectedNetwork = null;
    });

    try {
      final networks = await _wifiScan.scanNearbyNetworks();
      if (!mounted) return;
      setState(() {
        _networks = networks;
        _loadingNetworks = false;
        if (networks.isEmpty) {
          _scanError = context.translations.noNetworksFound;
        }
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _loadingNetworks = false;
        _scanError = error.toString();
      });
    }
  }

  void _selectNetwork(WifiNetwork network) {
    setState(() {
      _selectedNetwork = network;
      _manualEntry = false;
      _manualSsidController.clear();
      _passwordController.clear();
    });
  }

  void _enableManualEntry() {
    setState(() {
      _manualEntry = true;
      _selectedNetwork = null;
      _passwordController.clear();
    });
  }

  String? get _selectedSsid {
    if (_manualEntry) return _manualSsidController.text.trim();
    return _selectedNetwork?.ssid;
  }

  bool get _requiresPassword {
    if (_manualEntry) return true;
    return _selectedNetwork?.isSecure ?? true;
  }

  Future<void> _submit() async {
    if (_submitting || widget.isSubmitting) return;

    final ssid = _selectedSsid;
    if (ssid == null || ssid.isEmpty) {
      context.showSnackbar(
        message: context.translations.selectOrEnterWifi,
        color: Theme.of(context).colorScheme.error,
      );
      return;
    }

    if (_requiresPassword && !(_formKey.currentState?.validate() ?? false)) {
      return;
    }

    FocusScope.of(context).unfocus();
    setState(() => _submitting = true);
    try {
      await widget.onSubmit(ssid, _passwordController.text);
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final textTheme = theme.textTheme;
    final colorScheme = theme.colorScheme;
    final busy = _submitting || widget.isSubmitting;
    final hasSelection =
        _selectedNetwork != null ||
        (_manualEntry && _manualSsidController.text.trim().isNotEmpty);

    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(context.translations.addDevice, style: textTheme.titleLarge),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: Text(
                  context.translations.wifiNetwork,
                  style: textTheme.titleMedium,
                ),
              ),
              if (_wifiScan.isScanSupported)
                IconButton(
                  tooltip: context.translations.refreshNetworks,
                  onPressed: busy || _loadingNetworks ? null : _loadNetworks,
                  icon: _loadingNetworks
                      ? AppLoadingIndicator(
                          size: 20,
                          strokeWidth: 2,
                          color: colorScheme.primary,
                        )
                      : Icon(
                          Icons.refresh_rounded,
                          color: colorScheme.primary,
                        ),
                ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            _wifiScan.isScanSupported
                ? context.translations.selectWifiHint
                : context.translations.manualWifiHintIos,
            style: textTheme.bodySmall?.copyWith(
              color: colorScheme.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: 12),
          if (_scanError != null) ...[
            Text(
              _scanError!,
              style: textTheme.bodySmall?.copyWith(color: colorScheme.error),
            ),
            const SizedBox(height: 8),
          ],
          // List mode expands to fill; manual entry stacks fields naturally.
          if (_manualEntry)
            _buildNetworkSection(textTheme, colorScheme, busy)
          else
            Expanded(
              child: _buildNetworkSection(textTheme, colorScheme, busy),
            ),
          if (hasSelection) ...[
            const SizedBox(height: 12),
            if (_requiresPassword)
              TextFormField(
                controller: _passwordController,
                enabled: !busy,
                obscureText: _obscurePassword,
                textInputAction: TextInputAction.done,
                onFieldSubmitted: (_) => _submit(),
                decoration: InputDecoration(
                  labelText: context.translations.networkPassword,
                  prefixIcon: Icon(
                    Icons.lock_outline,
                    color: colorScheme.onSurfaceVariant,
                  ),
                  suffixIcon: IconButton(
                    onPressed: busy
                        ? null
                        : () => setState(
                            () => _obscurePassword = !_obscurePassword,
                          ),
                    icon: Icon(
                      _obscurePassword
                          ? Icons.visibility_outlined
                          : Icons.visibility_off_outlined,
                    ),
                  ),
                ),
                validator: (value) {
                  if (!_requiresPassword) return null;
                  if (value == null || value.isEmpty) {
                    return context.translations.networkPasswordRequired;
                  }
                  return null;
                },
              )
            else
              Text(
                context.translations.openNetworkNoPassword,
                style: textTheme.bodySmall?.copyWith(
                  color: colorScheme.onSurfaceVariant,
                ),
                textAlign: TextAlign.center,
              ),
          ],
          if (_manualEntry) const Spacer(),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: FilledButton(
              onPressed: busy || !hasSelection ? null : _submit,
              child: busy
                  ? AppLoadingIndicator(
                      size: 16,
                      strokeWidth: 2,
                      color: colorScheme.onPrimary,
                    )
                  : Text(context.translations.sendCredentials),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNetworkSection(
    TextTheme textTheme,
    ColorScheme colorScheme,
    bool busy,
  ) {
    if (_manualEntry) {
      return Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextFormField(
            controller: _manualSsidController,
            enabled: !busy,
            textInputAction: TextInputAction.next,
            onChanged: (_) => setState(() {}),
            decoration: InputDecoration(
              labelText: context.translations.networkSsid,
              prefixIcon: Icon(
                Icons.wifi,
                color: colorScheme.onSurfaceVariant,
              ),
            ),
          ),
          if (_wifiScan.isScanSupported) ...[
            const SizedBox(height: 8),
            TextButton(
              onPressed: busy ? null : _loadNetworks,
              style: const ButtonStyle(splashFactory: NoSplash.splashFactory),
              child: Text(context.translations.backToFoundNetworks),
            ),
          ],
        ],
      );
    }

    if (_loadingNetworks) {
      return const Center(child: AppLoadingIndicator(strokeWidth: 2));
    }

    if (_networks.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              context.translations.noNetworksAvailable,
              style: textTheme.bodyMedium?.copyWith(
                color: colorScheme.onSurfaceVariant,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: busy ? null : _enableManualEntry,
              child: Text(context.translations.enterNetworkManually),
            ),
          ],
        ),
      );
    }

    return Column(
      children: [
        Expanded(
          child: Card(
            margin: EdgeInsets.zero,
            clipBehavior: Clip.antiAlias,
            child: ListView.separated(
              itemCount: _networks.length,
              separatorBuilder: (_, _) => Divider(
                height: 1,
                indent: 52,
                color: colorScheme.outlineVariant,
              ),
              itemBuilder: (context, index) {
                final network = _networks[index];
                final selected = _selectedNetwork?.ssid == network.ssid;

                return InkWell(
                  onTap: busy ? null : () => _selectNetwork(network),
                  child: ColoredBox(
                    color: selected
                        ? colorScheme.primaryContainer
                        : Colors.transparent,
                    child: Padding(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 14,
                      ),
                      child: Row(
                        children: [
                          Icon(
                            network.isSecure
                                ? Icons.lock_outline
                                : Icons.wifi,
                            size: 22,
                            color: colorScheme.primary,
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  network.ssid,
                                  style: textTheme.bodyLarge?.copyWith(
                                    fontWeight: FontWeight.w500,
                                    color: colorScheme.onSurface,
                                  ),
                                ),
                                const SizedBox(height: 2),
                                Text(
                                  _signalLabel(network.signalLevel),
                                  style: textTheme.bodySmall?.copyWith(
                                    color: colorScheme.onSurfaceVariant,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          _SignalIcon(level: network.signalLevel),
                          if (selected) ...[
                            const SizedBox(width: 8),
                            Icon(
                              Icons.check_rounded,
                              size: 20,
                              color: colorScheme.primary,
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
        ),
        TextButton(
          onPressed: busy ? null : _enableManualEntry,
          style: const ButtonStyle(splashFactory: NoSplash.splashFactory),
          child: Text(context.translations.enterAnotherNetwork),
        ),
      ],
    );
  }

  String _signalLabel(int level) {
    if (level >= -50) return context.translations.signalExcellent;
    if (level >= -60) return context.translations.signalGood;
    if (level >= -70) return context.translations.signalFair;
    return context.translations.signalWeak;
  }
}

class _SignalIcon extends StatelessWidget {
  const _SignalIcon({required this.level});

  final int level;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final bars = switch (level) {
      >= -50 => 3,
      >= -65 => 2,
      >= -75 => 1,
      _ => 0,
    };

    return Row(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        for (var i = 0; i < 3; i++)
          Container(
            width: 4,
            height: 6 + (i * 4),
            margin: const EdgeInsets.only(left: 2),
            decoration: BoxDecoration(
              color: i < bars
                  ? colorScheme.primary
                  : colorScheme.onSurfaceVariant.withValues(alpha: 0.4),
              borderRadius: BorderRadius.circular(1),
            ),
          ),
      ],
    );
  }
}
