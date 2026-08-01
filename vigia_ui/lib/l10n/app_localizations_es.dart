// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Spanish Castilian (`es`).
class AppLocalizationsEs extends AppLocalizations {
  AppLocalizationsEs([String locale = 'es']) : super(locale);

  @override
  String get appTitle => 'Vigia';

  @override
  String get email => 'Correo electrónico';

  @override
  String get password => 'Contraseña';

  @override
  String get login => 'Entrar';

  @override
  String get register => 'Regístrate';

  @override
  String get logout => 'Cerrar sesión';

  @override
  String get noAccount => '¿No tienes una cuenta?';

  @override
  String get hasAccount => '¿Ya tienes una cuenta?';

  @override
  String get invalidCredentials => 'Usuario o contraseña inválidos';

  @override
  String get loginError => 'Error al iniciar sesión';

  @override
  String get devices => 'Dispositivos';

  @override
  String get settings => 'Configuración';

  @override
  String get home => 'Inicio';

  @override
  String get stage => 'Etapa';

  @override
  String sheetRecord(String id) {
    return 'Ficha #$id';
  }

  @override
  String get noDevicesFound => 'No se encontraron dispositivos';

  @override
  String errorWithMessage(String message) {
    return 'Error: $message';
  }

  @override
  String get addDevice => 'Agregar dispositivo';

  @override
  String get scanningHint =>
      'Sigue el tutorial y acerca el celular al Vigia. La búsqueda ya está en curso.';

  @override
  String get stepPowerOnTitle => 'Enciende el dispositivo';

  @override
  String get stepPowerOnDescription =>
      'Conecta el Vigia al enchufe y espera hasta que la luz indique que está listo para la configuración.';

  @override
  String get stepPairTitle => 'Vincula con la aplicación';

  @override
  String get stepPairDescription =>
      'Acerca el celular al Vigia para iniciar el vínculo con la aplicación.';

  @override
  String get stepWaitTitle => 'Espera la confirmación';

  @override
  String get stepWaitDescription =>
      'Espera unos segundos hasta que la configuración se complete con éxito.';

  @override
  String get connectingTitle => 'Conectando';

  @override
  String get connectingDescription =>
      'Dispositivo encontrado. Estableciendo la conexión con el Vigia…';

  @override
  String get authenticatingTitle => 'Validando dispositivo';

  @override
  String get authenticatingDescription =>
      'Confirmando la identidad del Vigia y autenticando la aplicación…';

  @override
  String get registeringTitle => 'Registrando dispositivo';

  @override
  String get registeringDescription =>
      'Creando el registro del dispositivo en los servidores Vigia…';

  @override
  String get testingNetworkTitle => 'Probando la red';

  @override
  String get testingNetworkDescription =>
      'Esperando a que Vigia se conecte al Wi‑Fi…';

  @override
  String get connectionEstablished => 'Conexión establecida';

  @override
  String deviceLinkedSuccess(String deviceName) {
    return '$deviceName se vinculó con éxito.';
  }

  @override
  String get confirm => 'Confirmar';

  @override
  String get connectionFailed => 'No fue posible conectar';

  @override
  String get connectionErrorFallback =>
      'Ocurrió un error al buscar o conectar el dispositivo.';

  @override
  String get tryAgain => 'Intentar de nuevo';

  @override
  String get devicesLoadError =>
      'Parece que estamos teniendo problemas técnicos.';

  @override
  String get wifiNetwork => 'Red Wi‑Fi';

  @override
  String get refreshNetworks => 'Actualizar redes';

  @override
  String get selectWifiHint => 'Selecciona la red que el Vigia debe usar.';

  @override
  String get manualWifiHintIos =>
      'En iOS, ingresa el nombre de la red manualmente.';

  @override
  String get noNetworksFound =>
      'No se encontraron redes. Intenta actualizar la lista.';

  @override
  String get selectOrEnterWifi => 'Selecciona o ingresa una red Wi‑Fi.';

  @override
  String get networkPassword => 'Contraseña de la red';

  @override
  String get networkPasswordRequired => 'Ingresa la contraseña de la red';

  @override
  String get openNetworkNoPassword =>
      'Red abierta — no se necesita contraseña.';

  @override
  String get sendCredentials => 'Enviar credenciales';

  @override
  String get networkSsid => 'Nombre de la red (SSID)';

  @override
  String get backToFoundNetworks => 'Volver a las redes encontradas';

  @override
  String get noNetworksAvailable => 'No hay redes disponibles';

  @override
  String get enterNetworkManually => 'Ingresar red manualmente';

  @override
  String get enterAnotherNetwork => 'Ingresar otra red';

  @override
  String get signalExcellent => 'Señal excelente';

  @override
  String get signalGood => 'Señal buena';

  @override
  String get signalFair => 'Señal moderada';

  @override
  String get signalWeak => 'Señal débil';

  @override
  String get usernameForm => 'Nombre completo';

  @override
  String get passwordConfirm => 'Confirmar contraseña';

  @override
  String get emailInvalid =>
      'La dirección de correo electrónico ingresada no es una dirección válida';

  @override
  String get passwordInvalid =>
      'La contraseña debe tener al menos 8 caracteres';

  @override
  String get passwordConfirmationInvalid =>
      'Las contraseñas ingresadas no coinciden';

  @override
  String get userEmailAlreadyInUse =>
      'El correo electrónico ya está siendo utilizado por otro usuario';

  @override
  String get registerUnknownError =>
      'Se produjo un error al intentar crear la cuenta';

  @override
  String get welcomeToVigia => 'Bienvenido a Vigia';

  @override
  String get createAccount => 'Inscribirse';

  @override
  String get deviceNickname => 'Nombre';

  @override
  String get deviceName => 'Nombre del dispositivo';

  @override
  String get deviceRoom => 'Habitación';

  @override
  String get deviceIdLabel => 'Identificador';

  @override
  String get bedroom => 'Dormitorio';

  @override
  String get livingRoom => 'Sala de estar';

  @override
  String get kitchen => 'Cocina';

  @override
  String get bathroom => 'Baño';

  @override
  String get office => 'Oficina';

  @override
  String get garage => 'Garaje';

  @override
  String get backyard => 'Patio trasero';

  @override
  String get frontyard => 'Patio delantero';

  @override
  String get online => 'Activo';

  @override
  String get offline => 'Inactivo';

  @override
  String get roomNotDefined => 'Habitación no definida';

  @override
  String get saveClips => 'Guardar clips';

  @override
  String get whatAreClips => '¿Qué son los clips?';

  @override
  String get whenEnabledClipsWillStoreClipsForAnalysis =>
      'Cuando está activado, Vigia almacenará clips de video cortos para un análisis posterior sobre posibles situaciones de caída.';

  @override
  String get saveChanges => 'Guardar cambios';

  @override
  String get deviceUpdatedSuccess => 'Dispositivo actualizado con éxito';

  @override
  String get deviceUpdateError => 'No se pudo actualizar el dispositivo';

  @override
  String get discardChangesTitle => '¿Descartar cambios?';

  @override
  String get discardChangesMessage => 'Hay cambios que aún no se han guardado.';

  @override
  String get discard => 'Descartar';

  @override
  String get cancel => 'Cancelar';

  @override
  String get deviceUsers => 'Usuarios';

  @override
  String get noUsersFound => 'No se encontraron usuarios';

  @override
  String get back => 'Volver';

  @override
  String get seeAllUsers => 'Ver todos';

  @override
  String deviceUsersCount(int current, int max) {
    return '$current/$max';
  }

  @override
  String get shareDevice => 'Compartir';

  @override
  String get shareLimitReached => 'Límite de usuarios alcanzado';

  @override
  String get shareDeviceInviteSubject => 'Invitación a Vigia';

  @override
  String get shareLinkCopied =>
      'Enlace copiado. Compártelo con quien quieras invitar.';

  @override
  String get shareLinkError => 'No se pudo generar el enlace de compartición';

  @override
  String get deviceOwner => 'Propietario';

  @override
  String get removeUserTitle => '¿Eliminar usuario?';

  @override
  String removeUserMessage(String name) {
    return '¿Eliminar a $name del acceso a los dispositivos de este grupo?';
  }

  @override
  String get removeUserConfirm => 'Eliminar';

  @override
  String get leaveGroupTitle => '¿Salir del grupo?';

  @override
  String get leaveGroupMessage =>
      'Perderás el acceso a los dispositivos compartidos de este grupo.';

  @override
  String get leaveGroupConfirm => 'Salir';

  @override
  String get userRemovedSuccess => 'Usuario eliminado con éxito';

  @override
  String get leftGroupSuccess => 'Saliste del grupo';

  @override
  String get userRemoveError => 'No se pudo eliminar el usuario';

  @override
  String get acceptingInvite => 'Aceptando invitación…';

  @override
  String get inviteAcceptedSuccess =>
      'Invitación aceptada. Los dispositivos compartidos ya están disponibles.';

  @override
  String get inviteAcceptedError => 'No se pudo aceptar la invitación';

  @override
  String get clips => 'Clips';

  @override
  String get viewClips => 'Ver clips';

  @override
  String get account => 'Cuenta';

  @override
  String get session => 'Sesión';
}
