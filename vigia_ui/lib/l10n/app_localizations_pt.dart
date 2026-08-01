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
  String get registeringTitle => 'Registrando dispositivo';

  @override
  String get registeringDescription =>
      'Criando o registro do dispositivo nos servidores Vigia…';

  @override
  String get testingNetworkTitle => 'Testando a rede';

  @override
  String get testingNetworkDescription =>
      'Aguardando o Vigia conectar ao Wi‑Fi…';

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
  String get devicesLoadError =>
      'Parece que estamos passando por problemas técnicos.';

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

  @override
  String get userEmailAlreadyInUse =>
      'O email já está sendo usado por outro usuário';

  @override
  String get registerUnknownError => 'Ocorreu um erro ao realizar criar conta';

  @override
  String get welcomeToVigia => 'Bem-vindo ao Vigia';

  @override
  String get createAccount => 'Criar conta';

  @override
  String get deviceNickname => 'Nome';

  @override
  String get deviceName => 'Nome do dispositivo';

  @override
  String get deviceRoom => 'Cômodo';

  @override
  String get deviceIdLabel => 'Identificador';

  @override
  String get bedroom => 'Quarto';

  @override
  String get livingRoom => 'Sala';

  @override
  String get kitchen => 'Cozinha';

  @override
  String get bathroom => 'Banheiro';

  @override
  String get office => 'Escritório';

  @override
  String get garage => 'Garagem';

  @override
  String get backyard => 'Quintal';

  @override
  String get frontyard => 'Frente';

  @override
  String get online => 'Ativo';

  @override
  String get offline => 'Desabilitado';

  @override
  String get roomNotDefined => 'Ambiente indefinido';

  @override
  String get saveClips => 'Salvar clips';

  @override
  String get whatAreClips => 'O que são clips?';

  @override
  String get whenEnabledClipsWillStoreClipsForAnalysis =>
      'Quando ativo, o Vigia armazenará clips de vídeo curtos para análise posterior sobre possíveis situações de queda';

  @override
  String get saveChanges => 'Salvar alterações';

  @override
  String get deviceUpdatedSuccess => 'Dispositivo atualizado com sucesso';

  @override
  String get deviceUpdateError => 'Não foi possível atualizar o dispositivo';

  @override
  String get discardChangesTitle => 'Descartar alterações?';

  @override
  String get discardChangesMessage =>
      'Existem alterações que ainda não foram salvas.';

  @override
  String get discard => 'Descartar';

  @override
  String get cancel => 'Cancelar';

  @override
  String get deviceUsers => 'Usuários';

  @override
  String get noUsersFound => 'Nenhum usuário encontrado';

  @override
  String get back => 'Voltar';

  @override
  String get seeAllUsers => 'Ver todos';

  @override
  String deviceUsersCount(int current, int max) {
    return '$current/$max';
  }

  @override
  String get shareDevice => 'Compartilhar';

  @override
  String get shareLimitReached => 'Limite de usuários atingido';

  @override
  String get shareDeviceInviteSubject => 'Convite para o Vigia';

  @override
  String get shareLinkCopied =>
      'Link copiado. Compartilhe com quem deseja convidar.';

  @override
  String get shareLinkError =>
      'Não foi possível gerar o link de compartilhamento';

  @override
  String get deviceOwner => 'Proprietário';

  @override
  String get removeUserTitle => 'Remover usuário?';

  @override
  String removeUserMessage(String name) {
    return 'Remover $name do acesso aos dispositivos deste grupo?';
  }

  @override
  String get removeUserConfirm => 'Remover';

  @override
  String get leaveGroupTitle => 'Sair do grupo?';

  @override
  String get leaveGroupMessage =>
      'Você perderá o acesso aos dispositivos compartilhados neste grupo.';

  @override
  String get leaveGroupConfirm => 'Sair';

  @override
  String get userRemovedSuccess => 'Usuário removido com sucesso';

  @override
  String get leftGroupSuccess => 'Você saiu do grupo';

  @override
  String get userRemoveError => 'Não foi possível remover o usuário';

  @override
  String get acceptingInvite => 'Aceitando convite…';

  @override
  String get inviteAcceptedSuccess =>
      'Convite aceito. Os dispositivos compartilhados já estão disponíveis.';

  @override
  String get inviteAcceptedError => 'Não foi possível aceitar o convite';

  @override
  String get clips => 'Clips';

  @override
  String get viewClips => 'Ver clips';

  @override
  String get account => 'Conta';

  @override
  String get session => 'Sessão';
}
