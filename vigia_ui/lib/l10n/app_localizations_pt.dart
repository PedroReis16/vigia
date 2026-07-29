// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Portuguese (`pt`).
class AppLocalizationsPt extends AppLocalizations {
  AppLocalizationsPt([String locale = 'pt']) : super(locale);

  @override
  String get appTitle => 'Vigia';

  @override
  String get email => 'Email';

  @override
  String get password => 'Senha';

  @override
  String get login => 'Entrar';

  @override
  String get register => 'Cadastre-se';

  @override
  String get logout => 'Sair';

  @override
  String get noAccount => 'Não tem uma conta?';

  @override
  String get hasAccount => 'Já tem uma conta?';

  @override
  String get invalidCredentials => 'Usuário ou senha inválidos';

  @override
  String get loginError => 'Erro ao fazer login';

  @override
  String get devices => 'Dispositivos';

  @override
  String get settings => 'Configurações';

  @override
  String get home => 'Início';

  @override
  String get stage => 'Etapa';

  @override
  String sheetRecord(String id) {
    return 'Ficha #$id';
  }

  @override
  String get noDevicesFound => 'Nenhum dispositivo encontrado';

  @override
  String errorWithMessage(String message) {
    return 'Erro: $message';
  }

  @override
  String get addDevice => 'Adicionar dispositivo';

  @override
  String get scanningHint =>
      'Siga o tutorial e aproxime o celular do Vigia. A busca já está em andamento.';

  @override
  String get stepPowerOnTitle => 'Ligue o dispositivo';

  @override
  String get stepPowerOnDescription =>
      'Conecte o Vigia à tomada e aguarde até que a luz indique que ele está pronto para a configuração.';

  @override
  String get stepPairTitle => 'Vincule ao aplicativo';

  @override
  String get stepPairDescription =>
      'Aproxime o celular do Vigia para iniciar o vínculo com o aplicativo.';

  @override
  String get stepWaitTitle => 'Aguarde a confirmação';

  @override
  String get stepWaitDescription =>
      'Aguarde alguns segundos até que a configuração seja concluída com sucesso.';

  @override
  String get connectingTitle => 'Conectando';

  @override
  String get connectingDescription =>
      'Dispositivo encontrado. Estabelecendo a conexão com o Vigia…';

  @override
  String get authenticatingTitle => 'Validando dispositivo';

  @override
  String get authenticatingDescription =>
      'Confirmando a identidade do Vigia e autenticando o aplicativo…';

  @override
  String get connectionEstablished => 'Conexão estabelecida';

  @override
  String deviceLinkedSuccess(String deviceName) {
    return '$deviceName foi vinculado com sucesso.';
  }

  @override
  String get confirm => 'Confirmar';

  @override
  String get connectionFailed => 'Não foi possível conectar';

  @override
  String get connectionErrorFallback =>
      'Ocorreu um erro ao procurar ou conectar ao dispositivo.';

  @override
  String get tryAgain => 'Tentar novamente';

  @override
  String get wifiNetwork => 'Rede Wi‑Fi';

  @override
  String get refreshNetworks => 'Atualizar redes';

  @override
  String get selectWifiHint => 'Selecione a rede que o Vigia deve usar.';

  @override
  String get manualWifiHintIos => 'No iOS, informe manualmente o nome da rede.';

  @override
  String get noNetworksFound =>
      'Nenhuma rede encontrada. Tente atualizar a lista.';

  @override
  String get selectOrEnterWifi => 'Selecione ou informe uma rede Wi‑Fi.';

  @override
  String get networkPassword => 'Senha da rede';

  @override
  String get networkPasswordRequired => 'Informe a senha da rede';

  @override
  String get openNetworkNoPassword => 'Rede aberta — senha não necessária.';

  @override
  String get sendCredentials => 'Enviar credenciais';

  @override
  String get networkSsid => 'Nome da rede (SSID)';

  @override
  String get backToFoundNetworks => 'Voltar para redes encontradas';

  @override
  String get noNetworksAvailable => 'Nenhuma rede disponível';

  @override
  String get enterNetworkManually => 'Informar rede manualmente';

  @override
  String get enterAnotherNetwork => 'Informar outra rede';

  @override
  String get signalExcellent => 'Sinal excelente';

  @override
  String get signalGood => 'Sinal bom';

  @override
  String get signalFair => 'Sinal moderado';

  @override
  String get signalWeak => 'Sinal fraco';

  @override
  String get usernameForm => 'Nome completo';

  @override
  String get passwordConfirm => 'Confirmar senha';

  @override
  String get emailInvalid =>
      'O email inserido não representa um endereço válido';

  @override
  String get passwordInvalid => 'A senha deve ter pelo menos 8 caracteres';

  @override
  String get passwordConfirmationInvalid => 'As senhas inseridas não coincidem';
}
