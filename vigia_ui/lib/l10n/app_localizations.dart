import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_es.dart';
import 'app_localizations_pt.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('pt'),
    Locale('en'),
    Locale('es'),
  ];

  /// No description provided for @appTitle.
  ///
  /// In pt, this message translates to:
  /// **'Vigia'**
  String get appTitle;

  /// No description provided for @email.
  ///
  /// In pt, this message translates to:
  /// **'Email'**
  String get email;

  /// No description provided for @password.
  ///
  /// In pt, this message translates to:
  /// **'Senha'**
  String get password;

  /// No description provided for @login.
  ///
  /// In pt, this message translates to:
  /// **'Entrar'**
  String get login;

  /// No description provided for @register.
  ///
  /// In pt, this message translates to:
  /// **'Cadastre-se'**
  String get register;

  /// No description provided for @logout.
  ///
  /// In pt, this message translates to:
  /// **'Sair'**
  String get logout;

  /// No description provided for @noAccount.
  ///
  /// In pt, this message translates to:
  /// **'Não tem uma conta?'**
  String get noAccount;

  /// No description provided for @hasAccount.
  ///
  /// In pt, this message translates to:
  /// **'Já tem uma conta?'**
  String get hasAccount;

  /// No description provided for @invalidCredentials.
  ///
  /// In pt, this message translates to:
  /// **'Usuário ou senha inválidos'**
  String get invalidCredentials;

  /// No description provided for @loginError.
  ///
  /// In pt, this message translates to:
  /// **'Erro ao fazer login'**
  String get loginError;

  /// No description provided for @devices.
  ///
  /// In pt, this message translates to:
  /// **'Dispositivos'**
  String get devices;

  /// No description provided for @settings.
  ///
  /// In pt, this message translates to:
  /// **'Configurações'**
  String get settings;

  /// No description provided for @home.
  ///
  /// In pt, this message translates to:
  /// **'Início'**
  String get home;

  /// No description provided for @stage.
  ///
  /// In pt, this message translates to:
  /// **'Etapa'**
  String get stage;

  /// No description provided for @sheetRecord.
  ///
  /// In pt, this message translates to:
  /// **'Ficha #{id}'**
  String sheetRecord(String id);

  /// No description provided for @noDevicesFound.
  ///
  /// In pt, this message translates to:
  /// **'Nenhum dispositivo encontrado'**
  String get noDevicesFound;

  /// No description provided for @errorWithMessage.
  ///
  /// In pt, this message translates to:
  /// **'Erro: {message}'**
  String errorWithMessage(String message);

  /// No description provided for @addDevice.
  ///
  /// In pt, this message translates to:
  /// **'Adicionar dispositivo'**
  String get addDevice;

  /// No description provided for @scanningHint.
  ///
  /// In pt, this message translates to:
  /// **'Siga o tutorial e aproxime o celular do Vigia. A busca já está em andamento.'**
  String get scanningHint;

  /// No description provided for @stepPowerOnTitle.
  ///
  /// In pt, this message translates to:
  /// **'Ligue o dispositivo'**
  String get stepPowerOnTitle;

  /// No description provided for @stepPowerOnDescription.
  ///
  /// In pt, this message translates to:
  /// **'Conecte o Vigia à tomada e aguarde até que a luz indique que ele está pronto para a configuração.'**
  String get stepPowerOnDescription;

  /// No description provided for @stepPairTitle.
  ///
  /// In pt, this message translates to:
  /// **'Vincule ao aplicativo'**
  String get stepPairTitle;

  /// No description provided for @stepPairDescription.
  ///
  /// In pt, this message translates to:
  /// **'Aproxime o celular do Vigia para iniciar o vínculo com o aplicativo.'**
  String get stepPairDescription;

  /// No description provided for @stepWaitTitle.
  ///
  /// In pt, this message translates to:
  /// **'Aguarde a confirmação'**
  String get stepWaitTitle;

  /// No description provided for @stepWaitDescription.
  ///
  /// In pt, this message translates to:
  /// **'Aguarde alguns segundos até que a configuração seja concluída com sucesso.'**
  String get stepWaitDescription;

  /// No description provided for @connectingTitle.
  ///
  /// In pt, this message translates to:
  /// **'Conectando'**
  String get connectingTitle;

  /// No description provided for @connectingDescription.
  ///
  /// In pt, this message translates to:
  /// **'Dispositivo encontrado. Estabelecendo a conexão com o Vigia…'**
  String get connectingDescription;

  /// No description provided for @authenticatingTitle.
  ///
  /// In pt, this message translates to:
  /// **'Validando dispositivo'**
  String get authenticatingTitle;

  /// No description provided for @authenticatingDescription.
  ///
  /// In pt, this message translates to:
  /// **'Confirmando a identidade do Vigia e autenticando o aplicativo…'**
  String get authenticatingDescription;

  /// No description provided for @connectionEstablished.
  ///
  /// In pt, this message translates to:
  /// **'Conexão estabelecida'**
  String get connectionEstablished;

  /// No description provided for @deviceLinkedSuccess.
  ///
  /// In pt, this message translates to:
  /// **'{deviceName} foi vinculado com sucesso.'**
  String deviceLinkedSuccess(String deviceName);

  /// No description provided for @confirm.
  ///
  /// In pt, this message translates to:
  /// **'Confirmar'**
  String get confirm;

  /// No description provided for @connectionFailed.
  ///
  /// In pt, this message translates to:
  /// **'Não foi possível conectar'**
  String get connectionFailed;

  /// No description provided for @connectionErrorFallback.
  ///
  /// In pt, this message translates to:
  /// **'Ocorreu um erro ao procurar ou conectar ao dispositivo.'**
  String get connectionErrorFallback;

  /// No description provided for @tryAgain.
  ///
  /// In pt, this message translates to:
  /// **'Tentar novamente'**
  String get tryAgain;

  /// No description provided for @wifiNetwork.
  ///
  /// In pt, this message translates to:
  /// **'Rede Wi‑Fi'**
  String get wifiNetwork;

  /// No description provided for @refreshNetworks.
  ///
  /// In pt, this message translates to:
  /// **'Atualizar redes'**
  String get refreshNetworks;

  /// No description provided for @selectWifiHint.
  ///
  /// In pt, this message translates to:
  /// **'Selecione a rede que o Vigia deve usar.'**
  String get selectWifiHint;

  /// No description provided for @manualWifiHintIos.
  ///
  /// In pt, this message translates to:
  /// **'No iOS, informe manualmente o nome da rede.'**
  String get manualWifiHintIos;

  /// No description provided for @noNetworksFound.
  ///
  /// In pt, this message translates to:
  /// **'Nenhuma rede encontrada. Tente atualizar a lista.'**
  String get noNetworksFound;

  /// No description provided for @selectOrEnterWifi.
  ///
  /// In pt, this message translates to:
  /// **'Selecione ou informe uma rede Wi‑Fi.'**
  String get selectOrEnterWifi;

  /// No description provided for @networkPassword.
  ///
  /// In pt, this message translates to:
  /// **'Senha da rede'**
  String get networkPassword;

  /// No description provided for @networkPasswordRequired.
  ///
  /// In pt, this message translates to:
  /// **'Informe a senha da rede'**
  String get networkPasswordRequired;

  /// No description provided for @openNetworkNoPassword.
  ///
  /// In pt, this message translates to:
  /// **'Rede aberta — senha não necessária.'**
  String get openNetworkNoPassword;

  /// No description provided for @sendCredentials.
  ///
  /// In pt, this message translates to:
  /// **'Enviar credenciais'**
  String get sendCredentials;

  /// No description provided for @networkSsid.
  ///
  /// In pt, this message translates to:
  /// **'Nome da rede (SSID)'**
  String get networkSsid;

  /// No description provided for @backToFoundNetworks.
  ///
  /// In pt, this message translates to:
  /// **'Voltar para redes encontradas'**
  String get backToFoundNetworks;

  /// No description provided for @noNetworksAvailable.
  ///
  /// In pt, this message translates to:
  /// **'Nenhuma rede disponível'**
  String get noNetworksAvailable;

  /// No description provided for @enterNetworkManually.
  ///
  /// In pt, this message translates to:
  /// **'Informar rede manualmente'**
  String get enterNetworkManually;

  /// No description provided for @enterAnotherNetwork.
  ///
  /// In pt, this message translates to:
  /// **'Informar outra rede'**
  String get enterAnotherNetwork;

  /// No description provided for @signalExcellent.
  ///
  /// In pt, this message translates to:
  /// **'Sinal excelente'**
  String get signalExcellent;

  /// No description provided for @signalGood.
  ///
  /// In pt, this message translates to:
  /// **'Sinal bom'**
  String get signalGood;

  /// No description provided for @signalFair.
  ///
  /// In pt, this message translates to:
  /// **'Sinal moderado'**
  String get signalFair;

  /// No description provided for @signalWeak.
  ///
  /// In pt, this message translates to:
  /// **'Sinal fraco'**
  String get signalWeak;

  /// No description provided for @usernameForm.
  ///
  /// In pt, this message translates to:
  /// **'Nome completo'**
  String get usernameForm;

  /// No description provided for @passwordConfirm.
  ///
  /// In pt, this message translates to:
  /// **'Confirmar senha'**
  String get passwordConfirm;

  /// No description provided for @emailInvalid.
  ///
  /// In pt, this message translates to:
  /// **'O email inserido não representa um endereço válido'**
  String get emailInvalid;

  /// No description provided for @passwordInvalid.
  ///
  /// In pt, this message translates to:
  /// **'A senha deve ter pelo menos 8 caracteres'**
  String get passwordInvalid;

  /// No description provided for @passwordConfirmationInvalid.
  ///
  /// In pt, this message translates to:
  /// **'As senhas inseridas não coincidem'**
  String get passwordConfirmationInvalid;

  /// No description provided for @userEmailAlreadyInUse.
  ///
  /// In pt, this message translates to:
  /// **'O email já está sendo usado por outro usuário'**
  String get userEmailAlreadyInUse;

  /// No description provided for @registerUnknownError.
  ///
  /// In pt, this message translates to:
  /// **'Ocorreu um erro ao realizar criar conta'**
  String get registerUnknownError;

  /// No description provided for @welcomeToVigia.
  ///
  /// In pt, this message translates to:
  /// **'Bem-vindo ao Vigia'**
  String get welcomeToVigia;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'es', 'pt'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'es':
      return AppLocalizationsEs();
    case 'pt':
      return AppLocalizationsPt();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
