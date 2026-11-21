# FIWARE — schema de atributos e comandos

## Visão geral

O schema de **atributos** e **comandos** dos dispositivos é definido em configuração (`appsettings`) e funciona como fonte da verdade da integração FIWARE. Esse schema é aplicado automaticamente:

- no **cadastro** de um novo dispositivo
- na **atualização** dos dispositivos já provisionados, ao reiniciar a `Vigia.API`

Protocolo e transporte padrão: **Ultralight** + **MQTT** (também configuráveis).

A configuração fica na seção `Fiware:Devices` de:

- `vigia-api/Vigia.API/appsettings.json`
- `vigia-api/Vigia.API/appsettings.Development.json`

Também pode ser sobrescrita por variáveis de ambiente (ex.: em Docker/K8s), no padrão do ASP.NET Core.

## Cadastro de um dispositivo

Ao cadastrar um dispositivo pela API:

1. O nome deve seguir o padrão `Vigia-{8 caracteres hexadecimais}` (ex.: `Vigia-a1b2c3d4`)
2. O dispositivo é provisionado no FIWARE já com os atributos e comandos de `Fiware:Devices`
3. Em seguida, o registro é persistido no banco da aplicação
4. Se a persistência falhar, o provisionamento no FIWARE é revertido

Devices já existentes no banco não são cadastrados novamente.

## Atualizar comandos e atributos

Alterações de schema são feitas no `appsettings` (ou via env). Após reiniciar a `Vigia.API`, os devices já provisionados são sincronizados com o schema atualizado.

Exemplo da seção:

```json
"Fiware": {
  "ProviderUrl": "http://iot-agent:4041",
  "Devices": {
    "Protocol": "PDI-IoTA-UltraLight",
    "Transport": "MQTT",
    "Commands": [
      { "Name": "stream_on", "Type": "command" },
      { "Name": "stream_off", "Type": "command" }
    ],
    "Attributes": [
      { "ObjectId": "s", "Name": "status", "Type": "Text" },
      { "ObjectId": "dp", "Name": "detected_person", "Type": "Boolean" }
    ]
  }
}
```

### Adicionar um comando

Inclua um item em `Fiware:Devices:Commands`:

```json
{ "Name": "reboot", "Type": "command" }
```

Reinicie a `Vigia.API`.

> O `Type` do comando deve ser sempre `"command"`.

### Adicionar um atributo

Inclua um item em `Fiware:Devices:Attributes`:

```json
{
  "ObjectId": "bl",
  "Name": "battery_level",
  "Type": "Number"
}
```

Reinicie a `Vigia.API`.

Regras dos atributos:

| Campo | Descrição |
|-------|-----------|
| `ObjectId` | Alias curto obrigatório no Ultralight; é o identificador enviado na medida (ex.: `bl\|87`). Deve ser único entre os atributos do device |
| `Name` | Nome do atributo na entidade do Orion |
| `Type` | Tipo NGSI (`Text`, `Boolean`, `Number`, …). Não usar variantes em minúsculo (`text`, `boolean`) |

### Variáveis de ambiente

No ASP.NET Core, arrays do appsettings podem ser sobrescritos por env vars indexadas, por exemplo:

```bash
Fiware__Devices__Commands__0__Name=stream_on
Fiware__Devices__Commands__0__Type=command
Fiware__Devices__Attributes__0__ObjectId=s
Fiware__Devices__Attributes__0__Name=status
Fiware__Devices__Attributes__0__Type=Text
```

## Verificação no MongoDB do IoT Agent

| Collection / campo | Conteúdo |
|--------------------|----------|
| `devices.active` | Atributos provisionados |
| `devices.commands` | Comandos provisionados |
| `commands` | Fila de comandos pendentes no modo *poll* |

Com transporte MQTT, a collection `commands` permanece vazia mesmo após o envio de um comando: o IoT Agent publica no MQTT e não enfileira no MongoDB. Esse é o comportamento esperado.
