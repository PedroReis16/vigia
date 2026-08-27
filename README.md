# VIGIA - Sistema doméstico para o monitoramento de quedas



## Dispositivo embarcado

O ambiente embarcado esta sendo utilizado uma placa Raspberry PI 5 com 8 GB de memória RAM de processamento, sendo executado com o Raspberry PI OS Lite 64-bits como sistema operacional principal.

### Pré-Requisitos

Antes de iniciar a configuração, certifique-se:
    - A placa foi configurada pelo Raspberry Pi Imager com usuário e senha definidos
    - Acesso físico à placa (monitor + teclado) ou acesso remoto via SSH com senha ainda ativo
    - Conta criada em `login.tailscale.com`

### Configurando o ambiente

- `Hostname e mDNS`
    O mDNS permite acessar o dispositivo pelo nome em qualquer rede local, sem precisar conhecer o IP da placa

    ```
        # Alterar o hostname
        sudo hostnamectl set-hostname vigia

        # Garantir que avahi sobre no boot

        sudo systemctl enable avahi-daemon
        sudo systemctl start avahi-daemon

    ```

    Após configurado, o dispotivio poderá ser acessado em qualquer rede local pelo endereço `vigia.local`.
    ```
        ssh vigia@vigia.local
    ``` 


- `SSH`  
    O SSH esta configurado para ser a única forma de acesso ao sistema, garantindo que apenas dispositivos confiáveis tenham acesso ao terminal da placa.

    - **Habilitar o SSH**
    
        ```
            sudo systemctl enable ssh #Habilita o serviço SSH para iniciar automaticamente
            sudo systemctl start ssh #Inicia o SSH
        ```

    - **Adicionar a chave pública no Pi**

        ```
            mkdir -p ~/.ssh && chmod 700 ~/.ssh
            echo "<CHAVE_PUBLICA>" >> ~/.ssh/authorized_keys   #Substitua `<CHAVE_PUBLICA>` pela sua chave
            chmod 600 ~/.ssh/authorized_keys

            sudo systemctl restart ssh
        ```

        - Nesse ponto, a chave pública foi configurada e o acesso deve estar habilitado
            
            ```
                exit #Desconectar do ambiente
                
                ssh vigia@<IP_PLACA> #Acesse novamente, se não pedir senha, o acesso foi realizado com sucesso via SSH
            ```

    - `Desabilitar autenticação por senha no Pi` **(Execute essa etapa apenas quando tiver certeza que a conexão por SSH esta funcionando)**

        Nessa etapa, etapa iremos configurar a placa de maneira que o acesso fique habilitado apenas chaves SSH

        - **Edite o arquivo de configuração do cloud-init**
            O arquivo de cloud-init é utilizado no ambiente para configuração do sistema operacional para ambiente em nuvem, tendo prioridade de execução sobre os demais arquivos de configuração

            - **Acesse o arquivo**
                ```
                    sudo nano /etc/ssh/sshd_config.d/50-cloud-init.conf
                ```

            - **Altere o conteúdo para**

                ````
                    PasswordAuthentication no

                ```
        - **Edite o arquivo sshd_config**

            ```
                sudo nano /etc/ssh/sshd_config #Habilita o modo de edição no arquivo de configurações
            ```

            - **Ajuste as seguintes linhas**

                ```
                    PasswordAuthentication no        # Desabilita a opção de login por senha
                    PubkeyAuthentication yes         # Habilita a autenticação por chave SSH
                    PermitRootLogin no               # Usuário root não pode realizar o login remoto
                    ListenAddress 0.0.0.0            # Habilita o acesso de qualquer IP
                    ListenAddress :: 
                    ClientAliveInterval 60           # Tempo em segundos entre verificações de conexão
                    ClientAliveCountMax 3            # Número de verificações antes de encerrar a sesssão
                ```

        - **Reiniciar o serviço**

            Reinicie o serviço SSH e verifique se as configurações foram aplicadas

            ```
                sudo systemctl restart ssh

                # Confirmar que senha está bloqueada
                sudo sshd -T | grep passwordauthentication

                # Deve retornar: passwordauthentication no
            ```

- `Acesso remoto`

    Para permitir que o dispositivo embarcado possa ser acessado de qualquer ambiente, sem a necessidade do terminal e o embarcado estarem conectados a mesma rede, utilizamos o `Tailscale`. O Tailscale cria uma rede VPN entre todos os dispositivos da mesma conta, permitindo acesso remoto de qualquer lugar sem abrir portas no roteador.


    - **Instalação** 
        ```
            curl -fsSL https://tailscale.com/install.sh | sh && sudo tailscale up
        ```

        Após a execução desse comando, será retornado uma URL para autenticação do usuário dentro do Tailscale, cole-a no navegador do computador e realize a autenticação. Após finalizar, o dispositivo já estará configurado.

    - **Verificar dispositivos e IPs**

        ```
            # Listar dispositivos da rede Tailscale
            tailscale status

            #Ver o IP do dispositivo atual
            tailscale ip
        ```

    - **Conectar ao Pi remotamente**
        ```
            # Por IP Tailscale

            ssh vigia@100.X.X.X

            $ Por magicDNS (URL fixa para acesso)
            ssh vigia@<MAGIC_DNS>
        ```

    Com o Tailscale, os dispositivos (Board | Host) pode ser acessados remotamente de qualquer lugar, desde que estejam conectados a internet e vinculados a mesma conta do tailscale.

- `Gerenciamento de redes Wi-Fi`

    O NetworkManager gerencia as conexões de rede. Cada rede salva recebe uma prioridade - quanto maior o número, maior a preferência. O Pi conecta automaticamente à rede disponível de maior prioridade.

    - **Inteface terminal (nmtui)**

        Para adicionar ou gerenciar redes com uma interface no terminal
        ```
            sudo nmtui
        ```
            
        - Active a connection -> Selecionar rede -> digitar senha
        - Edit a connection -> Gerenciar redes salvar

    - **Comandos rápidos (CLI)**

        ````
            # Listar redes disponíveis

            nmcli device wifi list

            # Conectar a uma rede salva
            sudo nmcli device wifi connect "<NOME REDE>"

            # Conectar e salvar uma nova rede
            sudo nmcli device wifi connect "<NOME REDE>" password "<SENHA DA REDE>"

            # Definir prioridade da rede
            sudo nmcli connection modify "<NOME REDE>" connection.autoconnect-priority 10

            # Ver todas as redes salvas com prioridade
            nmcli -f NAME, TYPE, AUTOCONNECT, AUTOCONNECT-PRIORITY connection show

            # Remover uma rede salva
            sudo nmcli connection delete "<NOME REDE>"
        ```

- `Atualizar o serviço bootstrap na placa`

    O **vigia-bootstrap** é o control plane da placa (pareamento BLE, Wi‑Fi, LCD e GPIO). Corre como serviço systemd em `/opt/vigia/bootstrap/`.

    O pacote de deploy é o zip único da release GitHub **Vigia Bootstrap** (tag `bootstrap`): `vigia-bootstrap-deploy.zip`.

    1. **Remover um serviço existente**

        Na placa (SSH):

        ```bash
        # Remove serviço, binário e scripts (mantém identity/network)
        sudo vigia-bootstrap-uninstall
        ```

        Se também quiser apagar identidade, rede e `.env` (será preciso parear de novo):

        ```bash
        sudo vigia-bootstrap-uninstall --purge-data
        ```

        Se o comando `vigia-bootstrap-uninstall` não existir (instalação antiga/manual):

        ```bash
        sudo systemctl stop vigia-bootstrap.service
        sudo systemctl disable vigia-bootstrap.service
        sudo rm -f /etc/systemd/system/vigia-bootstrap.service
        sudo systemctl daemon-reload
        sudo rm -rf /opt/vigia/bootstrap
        ```

    2. **Enviar o pacote do computador para a placa**

        No PC:

        1. Abra a release **Vigia Bootstrap** (tag `bootstrap`) no repositório
        2. Baixe **apenas** `vigia-bootstrap-deploy.zip`
        3. Envie para a placa:

        ```bash
        scp vigia-bootstrap-deploy.zip vigia@vigia.local:/tmp/
        ```

        Substitua o destino (`vigia@vigia.local` ou IP Tailscale) conforme o acesso disponível.

    3. **Instalar o serviço na placa**

        Na placa (SSH):

        ```bash
        cd /tmp
        unzip -o vigia-bootstrap-deploy.zip -d vigia-bootstrap-deploy
        sudo ./vigia-bootstrap-deploy/install-on-board.sh
        ```

        O script instala o bootstrap, ativa `vigia-bootstrap.service` e apaga o zip e a pasta temporária.

        Conferir:

        ```bash
        sudo systemctl status vigia-bootstrap.service
        journalctl -u vigia-bootstrap.service -n 80 --no-pager
        ```

        **Notas**

        - Sem `--purge-data` na desinstalação, identidade e Wi‑Fi já gravados são reutilizados
        - Se o I2C acabou de ser ativado pela primeira vez, pode ser necessário um reboot para o LCD (`/dev/i2c-1`)
        - Detalhes de hardware, build local e variáveis de ambiente: `vigia-bootstrap/docs/DEPLOY.md`

- `Atualizar o serviço fall-detection na placa`

    O **vigia-fall-detection** é o serviço de detecção de quedas (câmara + modelo). Corre como serviço systemd em `/opt/vigia/fall-detection/`. Depende do bootstrap já ter gravado `identity.json` e `network.json`.

    O pacote de deploy é o zip único da release GitHub **Vigia Onboard** (tag `onboard`): `vigia-fall-detection-deploy.zip`.

    1. **Remover um serviço existente**

        Na placa (SSH):

        ```bash
        # Remove serviço e binário (mantém identity/network do bootstrap)
        sudo vigia-fall-detection-uninstall
        ```

        Se também quiser apagar a base SQLite local do fall (`/opt/vigia/DB`):

        ```bash
        sudo vigia-fall-detection-uninstall --purge-data
        ```

        Se o comando `vigia-fall-detection-uninstall` não existir (instalação antiga/manual):

        ```bash
        sudo systemctl stop fall-detection.service
        sudo systemctl disable fall-detection.service
        sudo rm -f /etc/systemd/system/fall-detection.service
        sudo systemctl daemon-reload
        sudo rm -rf /opt/vigia/fall-detection
        ```

    2. **Enviar o pacote do computador para a placa**

        No PC:

        1. Abra a release **Vigia Onboard** (tag `onboard`) no repositório
        2. Baixe **`vigia-fall-detection-deploy.zip`**
        3. Envie para a placa:

        ```bash
        scp vigia-fall-detection-deploy.zip vigia@vigia.local:/tmp/
        ```

        Substitua o destino (`vigia@vigia.local` ou IP Tailscale) conforme o acesso disponível.

    3. **Instalar o serviço na placa**

        Na placa (SSH):

        ```bash
        cd /tmp
        unzip -o vigia-fall-detection-deploy.zip -d vigia-fall-detection-deploy
        sudo ./vigia-fall-detection-deploy/install-on-board.sh
        ```

        O script instala o fall-detection, ativa `fall-detection.service` e apaga o zip e a pasta temporária.

        Conferir:

        ```bash
        sudo systemctl status fall-detection.service
        journalctl -u fall-detection.service -n 80 --no-pager
        ```

        **Notas**

        - Instale **primeiro** o bootstrap; o fall só arranca com `identity.json` e `network.json` presentes
        - Sem `--purge-data` na desinstalação, a identidade/rede do bootstrap e o `.env` em `/opt/vigia/` são mantidos
        - A pipeline Onboard também gera um pacote OTA (`vigia-fall-ota-onboard.tar.gz`); o envio automático para a API é opcional (`upload_to_api`)
        - Detalhes de build local e variáveis de ambiente: `vigia-fall/docs/DEPLOY.md`


## FIWARE

### Visão geral

O schema de **atributos** e **comandos** dos dispositivos é definido em configuração (`appsettings`) e funciona como fonte da verdade da integração FIWARE. Esse schema é aplicado automaticamente:

- no **cadastro** de um novo dispositivo
- na **atualização** dos dispositivos já provisionados, ao reiniciar a `Vigia.API`

Protocolo e transporte padrão: **Ultralight** + **MQTT** (também configuráveis).

A configuração fica na seção `Fiware:Devices` de:

- `vigia-api/Vigia.API/appsettings.json`
- `vigia-api/Vigia.API/appsettings.Development.json`

Também pode ser sobrescrita por variáveis de ambiente (ex.: em Docker/K8s), no padrão do ASP.NET Core.

### Cadastro de um dispositivo

Ao cadastrar um dispositivo pela API:

1. O nome deve seguir o padrão `Vigia-{8 caracteres hexadecimais}` (ex.: `Vigia-a1b2c3d4`)
2. O dispositivo é provisionado no FIWARE já com os atributos e comandos de `Fiware:Devices`
3. Em seguida, o registro é persistido no banco da aplicação
4. Se a persistência falhar, o provisionamento no FIWARE é revertido

Devices já existentes no banco não são cadastrados novamente.

### Atualizar comandos e atributos

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

#### Adicionar um comando

Inclua um item em `Fiware:Devices:Commands`:

```json
{ "Name": "reboot", "Type": "command" }
```

Reinicie a `Vigia.API`.

> O `Type` do comando deve ser sempre `"command"`.

#### Adicionar um atributo

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

#### Variáveis de ambiente

No ASP.NET Core, arrays do appsettings podem ser sobrescritos por env vars indexadas, por exemplo:

```bash
Fiware__Devices__Commands__0__Name=stream_on
Fiware__Devices__Commands__0__Type=command
Fiware__Devices__Attributes__0__ObjectId=s
Fiware__Devices__Attributes__0__Name=status
Fiware__Devices__Attributes__0__Type=Text
```

### Verificação no MongoDB do IoT Agent

| Collection / campo | Conteúdo |
|--------------------|----------|
| `devices.active` | Atributos provisionados |
| `devices.commands` | Comandos provisionados |
| `commands` | Fila de comandos pendentes no modo *poll* |

Com transporte MQTT, a collection `commands` permanece vazia mesmo após o envio de um comando: o IoT Agent publica no MQTT e não enfileira no MongoDB. Esse é o comportamento esperado.
