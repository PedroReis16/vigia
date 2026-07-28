import 'package:flutter/material.dart';
import 'package:vigia_ui/data/services/wifi_scan_service.dart';
import 'package:vigia_ui/domain/DTOs/wifi_network.dart';

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
          _scanError = 'Nenhuma rede encontrada. Tente atualizar a lista.';
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
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Selecione ou informe uma rede Wi‑Fi.')),
      );
      return;
    }

    if (_requiresPassword && !(_formKey.currentState?.validate() ?? false)) {
      return;
    }

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
          Text('Adicionar dispositivo', style: textTheme.titleLarge),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: Text(
                  'Rede Wi‑Fi',
                  style: textTheme.titleMedium,
                ),
              ),
              if (_wifiScan.isScanSupported)
                IconButton(
                  tooltip: 'Atualizar redes',
                  onPressed: busy || _loadingNetworks ? null : _loadNetworks,
                  icon: _loadingNetworks
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.refresh),
                ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            _wifiScan.isScanSupported
                ? 'Selecione a rede que o Vigia deve usar.'
                : 'No iOS, informe manualmente o nome da rede.',
            style: textTheme.bodySmall,
          ),
          const SizedBox(height: 12),
          if (_scanError != null) ...[
            Text(
              _scanError!,
              style: textTheme.bodySmall?.copyWith(color: colorScheme.error),
            ),
            const SizedBox(height: 8),
          ],
          Expanded(child: _buildNetworkSection(textTheme, colorScheme, busy)),
          if (hasSelection) ...[
            const SizedBox(height: 12),
            if (_requiresPassword) ...[
              TextFormField(
                controller: _passwordController,
                enabled: !busy,
                obscureText: _obscurePassword,
                textInputAction: TextInputAction.done,
                onFieldSubmitted: (_) => _submit(),
                decoration: InputDecoration(
                  labelText: 'Senha da rede',
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
                    return 'Informe a senha da rede';
                  }
                  return null;
                },
              ),
            ] else
              Text(
                'Rede aberta — senha não necessária.',
                style: textTheme.bodySmall,
                textAlign: TextAlign.center,
              ),
          ],
          const SizedBox(height: 16),
          FilledButton(
            onPressed: busy || !hasSelection ? null : _submit,
            child: busy
                ? const SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Text('Enviar credenciais'),
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
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextFormField(
            controller: _manualSsidController,
            enabled: !busy,
            textInputAction: TextInputAction.next,
            onChanged: (_) => setState(() {}),
            decoration: const InputDecoration(
              labelText: 'Nome da rede (SSID)',
            ),
          ),
          if (_wifiScan.isScanSupported) ...[
            const SizedBox(height: 8),
            TextButton(
              onPressed: busy ? null : _loadNetworks,
              child: const Text('Voltar para redes encontradas'),
            ),
          ],
        ],
      );
    }

    if (_loadingNetworks) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_networks.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              'Nenhuma rede disponível',
              style: textTheme.bodyMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: busy ? null : _enableManualEntry,
              child: const Text('Informar rede manualmente'),
            ),
          ],
        ),
      );
    }

    return Column(
      children: [
        Expanded(
          child: ListView.separated(
            itemCount: _networks.length,
            separatorBuilder: (_, _) => const Divider(height: 1),
            itemBuilder: (context, index) {
              final network = _networks[index];
              final selected = _selectedNetwork?.ssid == network.ssid;

              return ListTile(
                selected: selected,
                selectedTileColor: colorScheme.primaryContainer,
                leading: Icon(
                  network.isSecure ? Icons.lock_outline : Icons.wifi,
                  color: selected ? colorScheme.primary : null,
                ),
                title: Text(network.ssid),
                subtitle: Text(_signalLabel(network.signalLevel)),
                trailing: _SignalIcon(level: network.signalLevel),
                onTap: busy ? null : () => _selectNetwork(network),
              );
            },
          ),
        ),
        TextButton(
          onPressed: busy ? null : _enableManualEntry,
          child: const Text('Informar outra rede'),
        ),
      ],
    );
  }

  String _signalLabel(int level) {
    if (level >= -50) return 'Sinal excelente';
    if (level >= -60) return 'Sinal bom';
    if (level >= -70) return 'Sinal moderado';
    return 'Sinal fraco';
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
